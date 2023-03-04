#!/usr/bin/python

# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.utils as utils
from fluxcloud.main.experiment import ExperimentSetup

from kubernetes import client, config

from .helpers import here, init_client

here = os.path.abspath(os.path.dirname(__file__))
root = os.path.dirname(os.path.dirname(here))

try:
    config.load_kube_config()
except:
    config.load_incluster_config()

def _test_example(dirname, tmp_path, check):
    """
    Shared function to test an example in a dirname, with a check function
    """
    client = init_client(str(tmp_path), cloud="minikube")
    experiment_file = os.path.join(root, "examples", "minikube", dirname, "experiments.yaml")

    # Create a new experiment directory to work from
    experiment_dir = os.path.join(tmp_path, "experiment")
    outdir = os.path.join(experiment_dir, 'data')
    utils.mkdir_p(experiment_dir)
    setup = ExperimentSetup(experiment_file, outdir=outdir)

    # Select the first (only) experiment!
    experiment = setup.matrices[0]
    client.up(setup, experiment=experiment)

    # Expected output directory
    expected_outdir = os.path.join(outdir, f'k8s-size-{experiment.size}-local')
    expected_scripts = os.path.join(expected_outdir, '.scripts')
    minicluster_file = os.path.join(expected_scripts, 'minicluster-size-2-lammps-job-ghcr.io-rse-ops-lammps-flux-sched-focal-v0.24.0.json')

    def shared_checks(info=True):
        assert os.path.exists(expected_outdir)
        assert 'meta.json' in os.listdir(expected_outdir)
        meta = utils.read_json(os.path.join(expected_outdir, 'meta.json'))
        assert meta['times']
        assert meta['minicluster']
        assert meta['jobs']

        # All examples use lammps
        for out in utils.recursive_find(expected_outdir, 'log.out'):
            content = utils.read_file(out)
            assert "Total wall time" in content
            assert "LAMMPS" in content

        # Info is only present for submit
        if info:
            assert meta['info']

    # Run the experiment in the working directory
    with utils.working_dir(experiment_dir):
        # This won't work in the CI it seems
        client.submit(setup, experiment)
        shared_checks()
        check(minicluster_file, experiment)
        
        # Now do the same for apply
        # shutil.rmtree(expected_outdir)
        client.apply(setup, experiment)
        shared_checks(info=False)
        check(minicluster_file, experiment)

    client.down(setup, experiment=experiment)


def test_minicluster_logging(tmp_path):
    """
    Ensure that the logging example returns expected logging params set
    in the minicluster output.
    """
    def check(minicluster_file, experiment):
        assert os.path.exists(minicluster_file)

        # Assert that the logging spec matches
        minicluster = utils.read_json(minicluster_file)
        for level, value in experiment.minicluster['logging'].items():
            assert level in minicluster['spec']['logging']
            assert minicluster['spec']['logging'][level] == value    

    # Run the example for submit and apply, with check
    _test_example("logging", tmp_path, check)


def test_minicluster_volumes(tmp_path):
    """
    Ensure that the volumes example produces the expected Minicluster spec
    """
    def check(minicluster_file, experiment):
        assert os.path.exists(minicluster_file)

        # Assert that the logging spec matches
        minicluster = utils.read_json(minicluster_file)
        assert "volumes" in minicluster['spec']

        # And container level volumes
        assert "volumes" in minicluster['spec']['containers'][0]
        container_volumes = minicluster['spec']['containers'][0]['volumes']

        # This checks the cluster level volumes
        for name, volume in experiment.minicluster['volumes'].items():
            assert name in minicluster['spec']['volumes']
            generated_volume = minicluster['spec']['volumes'][name]

            for attr, value in volume.items():
                if attr in generated_volume:
                    assert value == generated_volume[attr]

            assert name in container_volumes

            for vname, containervol in experiment.jobs['reaxc-hns-1']['volumes'].items():            
                assert vname in container_volumes
                for attr, val in containervol.items():
                    assert attr in container_volumes[vname]
                    assert container_volumes[vname][attr] == val


    # Run the example for submit and apply, with check
    _test_example("volumes", tmp_path, check)

def test_minicluster_resources(tmp_path):
    """
    Ensure that the resources example works as expected.
    """
    def check(minicluster_file, experiment):
        assert os.path.exists(minicluster_file)

        # Assert that the logging spec matches
        minicluster = utils.read_json(minicluster_file)

        assert "resources" in minicluster['spec']['containers'][0]
        resources = minicluster['spec']['containers'][0]['resources']

        for rtype, rvalue in experiment.jobs['reaxc-hns-1']['resources'].items():            
            assert rtype in resources
            assert resources[rtype] == rvalue

    # Run the example for submit and apply, with check
    _test_example("resources", tmp_path, check)
