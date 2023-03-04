# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import os
import shutil

import fluxcloud.main.api as api
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
        self.info = {}
        self.times = {}
        self.debug = kwargs.get("debug", False)

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
    def submit(self, setup, experiment):
        """
        Submit a Job via the Restful API
        """
        if not experiment.jobs:
            logger.warning(
                f"Experiment {experiment.expid} has no jobs, nothing to run."
            )
            return

        # Iterate through all the cluster sizes
        for size in experiment.minicluster["size"]:
            # We can't run if the minicluster > the experiment size
            if size > experiment.size:
                logger.warning(
                    f"Cluster of size {experiment.size} cannot handle a MiniCluster of size {size}, skipping."
                )
                continue

            # Launch a unique Minicluster per container image. E.g.,
            # if the user provides 2 images for size 4, we create two MiniClusters
            # This will provide all shared volumes across the jobs
            for minicluster, job in experiment.get_submit_miniclusters(size):
                logger.info(
                    f"\n🌀 Bringing up MiniCluster of size {size} with image {job['image']}"
                )

                # Create the API client (creates the user and token for the cluster)
                cli = api.APIClient()

                # Pre-pull containers, etc.
                if hasattr(self, "pre_apply"):
                    self.pre_apply(experiment, minicluster["name"], job=job)

                # Get back results with times (for minicluster assets) and jobs
                results = cli.submit(setup, experiment, minicluster, job=job)

                # Save times and output files for jobs
                for job in results.get("jobs", []):
                    self.save_job(job)

    def save_job(self, job):
        """
        Save the job and add times to our times listing.
        """
        jobid = f"job_{job['id']}"
        self.times[jobid] = job["info"]["runtime"]

        # Do we have an output file and output?
        if job["output"]:
            # Save to our output directory!
            logfile = job["job_output"]
            utils.mkdir_p(os.path.dirname(logfile))
            utils.write_file(job["output"], logfile)

        del job["output"]
        self.info[jobid] = job

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

            # Prepare the client for one minicluster
            cli = api.APIClient()

            # Prepare a specific MiniCluster for this size
            minicluster = copy.deepcopy(experiment.minicluster)
            minicluster["size"] = size

            # Get back results with times (for minicluster assets) and jobs
            # If debug level, print job output to terminal too :)
            results = cli.apply(
                experiment=experiment,
                minicluster=minicluster,
                outfile=logfile,
                stdout=self.debug,
                job=job,
            )
            self.times[jobname] = results["times"]

            # Save times between experiment runs
            experiment.save_metadata(self.times, self.info)

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
