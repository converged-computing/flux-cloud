# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.defaults as defaults
from fluxcloud.logger import logger
from fluxcloud.main.client import ExperimentClient


class GoogleCloud(ExperimentClient):
    """
    A Google Cloud GKE experiment runner.
    """

    name = "google"

    def __init__(self, **kwargs):
        super(GoogleCloud, self).__init__(settings_file=kwargs.get("settings_file"))
        self.zone = kwargs.get("zone") or "us-central1-a"
        self.project = kwargs.get("project") or self.settings.google["project"]

    def run(self, experiments, template, outdir, test=False):
        """
        Run Flux Operator experiments in GKE
        """
        matrices = self.prepare_matrices(experiments, test=test)
        for experiment in matrices:
            self.run_experiment(experiment, template, outdir)

    def up(self, experiments):
        """
        Bring up a cluster
        """
        if "matrix" in experiments:
            logger.warning("Matrix found - will bring up cluster for first entry.")
        experiment = self.prepare_matrices(experiments, test=True)[0]

        # TODO if these are to be shared, make more easily accessible
        size = experiment.get("size") or self.settings.google["size"]
        machine = experiment.get("machine") or self.settings.google["machine"]
        tags = experiment.get("cluster", {}).get("tags")

        cluster_name = (
            experiment.get("cluster", {}).get("name") or defaults.default_cluster_name
        )
        create_script = self.get_script("cluster-create")

        # Create the cluster with creation script
        cmd = [
            create_script,
            "--project",
            self.project,
            "--zone",
            self.zone,
            "--machine",
            machine,
            "--cluster",
            cluster_name,
            "--cluster-version",
            self.settings.kubernetes["version"],
            "--size",
            str(size),
        ]
        if tags:
            cmd += ["--tags", ",".join(tags)]
        return self.run_timed("create-cluster", cmd)

    def down(self, experiments):
        """
        Destroy a cluster
        """
        if "matrix" in experiments:
            logger.warning("Matrix found - will bring up cluster for first entry.")
        experiment = self.prepare_matrices(experiments, test=True)[0]

        cluster_name = (
            experiment.get("cluster", {}).get("name") or defaults.default_cluster_name
        )
        destroy_script = self.get_script("cluster-destroy")

        # Create the cluster with creation script
        return self.run_timed(
            "destroy-cluster",
            [destroy_script, "--zone", self.zone, "--cluster", cluster_name],
        )

    def apply(self, experiment):
        """
        Apply a CRD to run the experiment and wait for output.
        """
        namespace = (
            experiment.get("", {}).get("namespace") or defaults.default_namespace
        )
        assert namespace
        print("TODO need to apply yaml to run experiment, collect output.")
        import IPython

        IPython.embed()

    def run_experiment(self, experiment, template, outdir):
        """
        Run a single experiment

        1. create the cluster
        2. run each command and save output
        3. bring down the cluster
        """
        self.up(experiment)

        # For each command:
        # generate the crd from template
        # create named output dir
        # write to temporary file
        # apply script
        # wait for log output (with workdir)
        #

        if not self.project:
            raise ValueError(
                "Please provide your Google Cloud project in your settings.yml or flux-cloud set google:project <project>"
            )
