# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import time

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.api import APIClient
from fluxcloud.main.decorator import save_meta, timed

here = os.path.dirname(os.path.abspath(__file__))


class ExperimentClient:
    """
    A base experiment client
    """

    def __init__(self, *args, **kwargs):
        import fluxcloud.main.settings as settings

        self.settings = settings.Settings
        self.info = {}
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

    def run_command(self, cmd):
        """
        Run a timed command, and handle nonzero exit codes.
        """
        logger.debug("\n> Running Command: " + " ".join(cmd))
        res = utils.run_command(cmd)
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
        for experiment in setup.iter_experiments():
            self.up(setup, experiment=experiment)
            self.apply(setup, experiment=experiment)
            self.down(setup, experiment=experiment)

    @save_meta
    def batch(self, setup):
        """
        Run Flux Operator experiments via batch submit

        1. create the cluster
        2. run each command via submit to same MiniCluster
        3. bring down the cluster
        """
        # Each experiment has its own cluster size and machine type
        for experiment in setup.iter_experiments():
            self.up(setup, experiment=experiment)
            self.submit(setup, experiment=experiment)
            self.down(setup, experiment=experiment)

    @save_meta
    def down(self, *args, **kwargs):
        """
        Destroy a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    @save_meta
    def open_ui(self, setup, experiment, size, api=None, persistent=False):
        """
        Launch a CRD that opens the UI only.
        """
        # The MiniCluster can vary on size
        minicluster = experiment.minicluster

        # Create a FluxRestful API to submit to
        created = False
        if api is None:
            api = APIClient()
            created = True

        logger.info(f"\n🌀 Bringing up MiniCluster of size {size}")

        # Get persistent variables for this job size, image is required
        job = experiment.get_persistent_variables(size, required=["image"])
        job.update({"token": api.token, "user": api.user})

        # We can't have a command
        if "command" in job:
            del job["command"]

        # Pre-pull containers, etc.
        if hasattr(self, "pre_apply"):
            self.pre_apply(experiment, "global-job", job=job)

        # Create the minicluster via a CRD without a command
        crd = experiment.generate_crd(job, size)

        # Create one MiniCluster CRD (without a command) to run the Flux Restful API
        kwargs = {
            "minicluster": minicluster,
            "crd": crd,
            "token": api.token,
            "user": api.user,
            "size": size,
        }
        submit_script = experiment.get_shared_script(
            "minicluster-create-persistent", kwargs, suffix=f"-size-{size}"
        )
        # Start the MiniCluster! This should probably be done better...
        self.run_timed(
            f"minicluster-create-persistent-size-{size}", ["/bin/bash", submit_script]
        )

        # Ensure our credentials still work, and open port forward
        api.check(experiment)
        logger.info(f"\n🌀 MiniCluster of size {size} is up.\n")

        # If created for the first time, show credentials
        if created:
            logger.info(
                "Save these if you want to log into the Flux RESTFul interface, there are specific to the MiniCluster"
            )
            logger.info(f"export FLUX_USER={api.user}")
            logger.info(f"export FLUX_TOKEN={api.token}")

        # If we exit, the port forward will close.
        if persistent:
            try:
                logger.info("Press Control+c to Disconnect.")
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                logger.info("🧽️ Cleaning up!")
                self.run_timed(
                    f"minicluster-persistent-destroy-size-{size}",
                    ["kubectl", "delete", "-f", crd],
                )

        return api, kwargs

    @save_meta
    def submit(self, setup, experiment):
        """
        Submit a Job via the Restful API
        """
        if not experiment.jobs:
            logger.warning(
                f"Experiment {experiment.expid} has no jobs, nothing to run."
            )
            return

        api = None

        # Iterate through all the cluster sizes
        for size in experiment.minicluster["size"]:

            # We can't run if the minicluster > the experiment size
            if size > experiment.size:
                logger.warning(
                    f"Cluster of size {experiment.size} cannot handle a MiniCluster of size {size}, skipping."
                )
                continue

            # Open the api for the size
            api, uiattrs = self.open_ui(setup, experiment, size, api)
            logger.info(f"\n🌀 Bringing up MiniCluster of size {size}")

            # Save times (and logs in submit) as we go
            for jobid, info in api.submit(setup, experiment, size):
                logger.info(f"{jobid} took {info['runtime']} seconds.")
                self.times[jobid] = info["runtime"]
                self.info[jobid] = info

            logger.info(f"\n🌀 MiniCluster of size {size} is finished")
            self.run_timed(
                f"minicluster-persistent-destroy-size-{size}",
                ["kubectl", "delete", "-f", uiattrs["crd"]],
            )

    @save_meta
    def apply(self, setup, experiment):
        """
        Apply a CRD to run the experiment and wait for output.

        This is really just running the setup!
        """
        # The MiniCluster can vary on size
        if not experiment.jobs:
            logger.warning(
                f"Experiment {experiment.expid} has no jobs, nothing to run."
            )
            return

        # Save output here
        experiment_dir = experiment.root_dir

        for size, jobname, job in experiment.iter_jobs():

            # Add the size
            jobname = f"{jobname}-minicluster-size-{size}"
            job_output = os.path.join(experiment_dir, jobname)
            logfile = os.path.join(job_output, "log.out")

            # Any custom commands to run first?
            if hasattr(self, "pre_apply"):
                self.pre_apply(experiment, jobname, job)

            # Do we have output?
            if os.path.exists(logfile) and not setup.force:
                relpath = os.path.relpath(logfile, experiment_dir)
                logger.warning(
                    f"{relpath} already exists and force is False, skipping."
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
            kwargs = {
                "minicluster": experiment.minicluster,
                "logfile": logfile,
                "crd": crd,
            }
            apply_script = experiment.get_shared_script(
                "minicluster-run", kwargs, suffix=f"-{jobname}"
            )

            # Apply the job, and save to output directory
            self.run_timed(f"{self.job_prefix}-{jobname}", ["/bin/bash", apply_script])

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
