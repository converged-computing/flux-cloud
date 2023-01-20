# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.decorator import save_meta, timed

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
        """
        Run a timed command, and handle nonzero exit codes.
        """
        logger.debug("\n> Running Timed Command: " + " ".join(cmd))
        res = utils.run_command(cmd)
        if res.returncode != 0:
            raise ValueError("nonzero exit code, exiting.")

    def run_command(self, cmd, cleanup_func=None):
        """
        Run a timed command, and handle nonzero exit codes.
        """
        logger.debug("\n> Running Command: " + " ".join(cmd))
        res = utils.run_command(cmd)

        # An optional cleanup function (also can run if not successful)
        if cleanup_func is not None:
            cleanup_func()

        if res.returncode != 0:
            raise ValueError("nonzero exit code, exiting.")

    def __str__(self):
        return "[flux-cloud-client]"

    @save_meta
    def run(self, setup):
        """
        Run Flux Operator experiments in GKE

        1. create the cluster
        2. run each command and save output
        3. bring down the cluster
        """
        # Each experiment has its own cluster size and machine type
        for experiment in setup.matrices:

            # Don't bring up a cluster if experiments already run!
            if not setup.force and experiment.is_run():
                logger.info(
                    f"Experiment on machine {experiment['id']} was already run and force is False, skipping."
                )
                continue

            self.up(setup, experiment=experiment)
            self.apply(setup, experiment=experiment)
            self.down(setup, experiment=experiment)

    @save_meta
    def down(self, *args, **kwargs):
        """
        Destroy a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    @save_meta
    def apply(self, setup, experiment):
        """
        Apply a CRD to run the experiment and wait for output.

        This is really just running the setup!
        """
        # The MiniCluster can vary on size
        minicluster = experiment.minicluster
        if not experiment.jobs:
            logger.warning(f"Experiment {experiment} has no jobs, nothing to run.")
            return

        # The experiment is defined by the machine type and size
        experiment_dir = experiment.root_dir

        # Iterate through all the cluster sizes
        for size in minicluster["size"]:

            # We can't run if the minicluster > the experiment size
            if size > experiment.size:
                logger.warning(
                    f"Cluster of size {experiment.size} cannot handle a MiniCluster of size {size}, skipping."
                )
                continue

            # Jobname is used for output
            for jobname, job in experiment.jobs.items():

                # Do we want to run this job for this size and machine?
                if not experiment.check_job_run(job, size):
                    logger.debug(
                        f"Skipping job {jobname} as does not match inclusion criteria."
                    )
                    continue

                # Add the size
                jobname = f"{jobname}-minicluster-size-{size}"
                job_output = os.path.join(experiment_dir, jobname)
                logfile = os.path.join(job_output, "log.out")

                # Any custom commands to run first?
                if hasattr(self, "pre_apply"):
                    self.pre_apply(experiment, jobname, job)

                # Do we have output?
                if os.path.exists(logfile) and not setup.force:
                    logger.warning(
                        f"{logfile} already exists and force is False, skipping."
                    )
                    continue

                elif os.path.exists(logfile) and setup.force:
                    logger.warning(f"Cleaning up previous run in {job_output}.")
                    shutil.rmtree(job_output)

                # Create job directory anew
                utils.mkdir_p(job_output)

                # Generate the populated crd from the template
                crd = experiment.generate_crd(job, size)

                # Prepare specific .crd for template
                # Note the output directory is already specific to the job index
                kwargs = {"minicluster": minicluster, "logfile": logfile, "crd": crd}
                apply_script = experiment.get_shared_script(
                    "minicluster-run", kwargs, suffix=f"-{jobname}"
                )

                # Apply the job, and save to output directory
                self.run_timed(
                    f"{self.job_prefix}-{jobname}", ["/bin/bash", apply_script]
                )

    def clear_minicluster_times(self):
        """
        Update times to not include jobs
        """
        times = {}
        for key, value in self.times.items():

            # Don't add back a job that was already saved
            if key.startswith(self.job_prefix):
                continue
            times[key] = value
        self.times = times

    @save_meta
    def up(self, *args, **kwargs):
        """
        Bring up a cluster implemented by underlying cloud.
        """
        raise NotImplementedError
