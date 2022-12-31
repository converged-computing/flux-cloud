# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.decorator import timed

here = os.path.dirname(os.path.abspath(__file__))


class ExperimentClient:
    """
    A base experiment client
    """

    def __init__(self, *args, **kwargs):
        import fluxcloud.main.settings as settings

        self.settings = settings.Settings
        self.times = {}

        # Job prefix is used for organizing time entries
        self.job_prefix = "minicluster-run"

    def __repr__(self):
        return str(self)

    @timed
    def run_timed(self, name, cmd):
        return utils.run_command(cmd)

    def __str__(self):
        return "[flux-cloud-client]"

    def get_script(self, name):
        """
        Get a named script from the cloud's script folder
        """
        script = os.path.join(here, "clouds", self.name, "scripts", name)
        if os.path.exists(script):
            return script

    def experiment_is_run(self, setup, experiment):
        """
        Determine if all jobs are already run in an experiment
        """
        # The experiment is defined by the machine type and size
        experiment_dir = os.path.join(setup.outdir, experiment["id"])

        # One run per job (command)
        jobs = experiment.get("jobs", [])
        if not jobs:
            logger.warning(
                f"Experiment {experiment['id']} has no jobs, nothing to run."
            )
            return True

        # If all job output files exist, experiment is considered run
        for jobname, _ in jobs.items():
            job_output = os.path.join(experiment_dir, jobname)
            logfile = os.path.join(job_output, "log.out")

            # Do we have output?
            if not os.path.exists(logfile):
                return False
        return True

    def run(self, setup, force=False):
        """
        Run Flux Operator experiments in GKE

        1. create the cluster
        2. run each command and save output
        3. bring down the cluster
        """
        # Each experiment has its own cluster size and machine type
        for experiment in setup.matrices:

            # Don't bring up a cluster if experiments already run!
            if not force and self.experiment_is_run(setup, experiment):
                logger.info(
                    f"Experiment {experiment['id']} was already run and force is False, skipping."
                )
                continue

            self.up(setup, experiment=experiment)
            self.apply(setup, force=force, experiment=experiment)
            self.down(setup, experiment=experiment)

    def down(self, *args, **kwargs):
        """
        Destroy a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    def apply(self, *args, **kwargs):
        """
        Apply (run) one or more experiments.
        """
        raise NotImplementedError

    def up(self, *args, **kwargs):
        """
        Bring up a cluster implemented by underlying cloud.
        """
        raise NotImplementedError
