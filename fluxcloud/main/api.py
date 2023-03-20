# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
import shutil
import time
import uuid

from flux_restful_client.main import get_client
from fluxoperator.client import FluxMiniCluster

import fluxcloud.utils as utils
from fluxcloud.logger import logger

here = os.path.dirname(os.path.abspath(__file__))


class APIClient:
    def __init__(self, token=None, user=None, secret_key=None):
        """
        API client wrapper.
        """
        self.user = token or os.environ.get("FLUX_USER") or user or "fluxuser"
        self.token = token or os.environ.get("FLUX_TOKEN") or str(uuid.uuid4())
        self.secret_key = (
            secret_key or os.environ.get("FLUX_SECRET_KEY") or str(uuid.uuid4())
        )
        self.proc = None
        self.broker_pod = None

    def show_credentials(self):
        """
        Show the token and user, if requested.
        """
        logger.info("MiniCluster created with credentials:")
        logger.info(f"  FLUX_USER={self.user}")
        logger.info(f"  FLUX_TOKEN={self.token}")

    def _set_minicluster_credentials(self, minicluster):
        """
        If the user provided credentials, use
        """
        if "flux_restful" not in minicluster:
            minicluster["flux_restful"] = {}

        if "username" not in minicluster["flux_restful"]:
            minicluster["flux_restful"]["username"] = self.user

        if "token" not in minicluster["flux_restful"]:
            minicluster["flux_restful"]["token"] = self.token

        if "secret_key" not in minicluster["flux_restful"]:
            minicluster["flux_restful"]["secret_key"] = self.secret_key

        # Update credentials
        self.user = minicluster["flux_restful"]["username"]
        self.token = minicluster["flux_restful"]["token"]
        self.secret_key = minicluster["flux_restful"]["secret_key"]
        return minicluster

    def _create_minicluster(
        self, operator, minicluster, experiment, job, interactive=True
    ):
        """
        Shared function to take an operator handle and create the minicluster.

        This can be used for apply or submit! We separate minicluster (gets
        piped into the MiniClusterSpec) from job (gets piped into a
        MiniClusterContainer spec).
        """
        namespace = minicluster["namespace"]
        image = job["image"]
        name = minicluster["name"]
        size = minicluster["size"]

        self._set_minicluster_credentials(minicluster)

        try:
            # The operator will time creation through pods being ready
            operator.create(**minicluster, container=job)
        except Exception as e:
            # Give the user the option to delete and recreate or just exit
            logger.error(f"There was an issue creating the MiniCluster: {e}")
            if interactive and not utils.confirm_action(
                "Would you like to submit jobs to the current cluster? You will need to have provided the same username as password."
            ):
                if utils.confirm_action(
                    "Would you like to delete this mini cluster and re-create?"
                ):
                    logger.info("Cleaning up MiniCluster...")
                    operator.delete()
                    return self._create_minicluster(
                        operator, minicluster, experiment, job, interactive=interactive
                    )
                else:
                    logger.exit(
                        f"Try: 'kubectl delete -n {namespace} minicluster {name}'"
                    )
            elif not interactive:
                logger.exit(f"Try: 'kubectl delete -n {namespace} minicluster {name}'")
            return

        # Wait for pods to be ready to include in minicluster up time
        self.show_credentials()

        # Save MiniCluster metadata
        image_slug = re.sub("(:|/)", "-", image)
        uid = f"{size}-{name}-{image_slug}"
        experiment.save_json(operator.metadata, f"minicluster-size-{uid}.json")

        # This is a good point to also save nodes metadata
        nodes = operator.get_nodes()
        pods = operator.get_pods()
        experiment.save_file(nodes.to_str(), f"nodes-{uid}.json")
        experiment.save_file(pods.to_str(), f"pods-size-{uid}.json")
        return operator.metadata

    def apply(
        self,
        experiment,
        minicluster,
        job=None,
        outfile=None,
        stdout=True,
        interactive=True,
    ):
        """
        Use the client to apply (1:1 job,minicluster) the jobs programatically.
        """
        name = minicluster["name"]

        # Interact with the Flux Operator Python SDK
        operator = FluxMiniCluster()

        self._create_minicluster(
            operator, minicluster, experiment, job, interactive=interactive
        )

        # Time from when broker pod (and all pods are ready)
        start = time.time()

        # Get the pod to stream output from directly
        if outfile is not None:
            operator.stream_output(outfile, stdout=stdout)

        # When output done streaming, job is done
        end = time.time()
        logger.info(f"Job {name} is complete! Cleaning up MiniCluster...")

        # This also waits for termination (and pods to be gone) and times it
        operator.delete()

        # TODO likely need to separate minicluster up/down times.
        results = {"times": operator.times}
        results["times"][name] = end - start
        return results

    def submit(
        self, setup, experiment, minicluster, job, poll_seconds=20, interactive=True
    ):
        """
        Use the client to submit the jobs programatically.
        """
        image = job["image"]
        size = minicluster["size"]

        # Interact with the Flux Operator Python SDK
        operator = FluxMiniCluster()

        self._create_minicluster(
            operator, minicluster, experiment, job, interactive=interactive
        )

        # Return results (and times) to calling client
        results = {}

        # Submit jobs via port forward - this waits until the server is ready
        with operator.port_forward() as forward_url:
            print(f"Port forward opened to {forward_url}")

            # See https://flux-framework.org/flux-restful-api/getting_started/api.html
            cli = get_client(
                host=forward_url,
                user=self.user,
                token=self.token,
                secret_key=self.secret_key,
            )
            cli.set_basic_auth(self.user, self.token)

            # Keep a lookup of jobid and output files.
            # We will try waiting for all jobs to finish and then save output
            jobs = []
            for jobname, job in experiment.jobs.items():
                # Do we want to run this job for this size, image?
                if not experiment.check_job_run(job, size=size, image=image):
                    logger.debug(
                        f"Skipping job {jobname} as does not match inclusion criteria."
                    )
                    continue

                if "command" not in job:
                    logger.debug(f"Skipping job {jobname} as does not have a command.")
                    continue

                # Here we submit all jobs to the scheduler. Let the scheduler handle it!
                submit_job = self.submit_job(
                    cli, experiment, setup, minicluster, job, jobname
                )
                if not submit_job:
                    continue
                jobs.append(submit_job)

            logger.info(f"Submit {len(jobs)} jobs! Waiting for completion...")

            # Poll once every 30 seconds
            # This could be improved with some kind of notification / pubsub thing
            completed = []
            while jobs:
                logger.info(f"{len(jobs)} are active.")
                time.sleep(poll_seconds)
                unfinished = []
                for job in jobs:
                    if "id" not in job:
                        logger.warning(
                            f"Job {job} is missing an id or name, likely an issue or not ready, skipping."
                        )
                        continue

                    info = cli.jobs(job["id"])

                    # If we don't have a name yet, it's still pending
                    if "name" not in info:
                        unfinished.append(job)
                        continue

                    jobname = info["name"].rjust(15)
                    if info["state"] == "INACTIVE":
                        finish_time = round(info["runtime"], 2)
                        logger.debug(
                            f"{jobname} is finished {info['result']} in {finish_time} seconds."
                        )
                        job["info"] = info
                        job["output"] = cli.output(job["id"]).get("Output")
                        completed.append(job)
                    else:
                        logger.debug(f"{jobname} is in state {info['state']}")
                        unfinished.append(job)
                jobs = unfinished

        logger.info("All jobs are complete!")

        # This also waits for termination (and pods to be gone) and times it
        if not interactive or utils.confirm_action(
            "Would you like to delete this mini cluster?"
        ):
            logger.info("Cleaning up MiniCluster...")
            operator.delete()

        # Get times recorded by FluxOperator Python SDK
        results["jobs"] = completed
        results["times"] = operator.times
        return results

    def submit_job(self, cli, experiment, setup, minicluster, job, jobname):
        """
        Submit the job (if appropriate for the minicluster)

        Return an appended Flux Restful API job result with the expected
        output file.
        """
        # The experiment is defined by the machine type and size
        experiment_dir = experiment.root_dir

        jobname = f"{jobname}-minicluster-size-{minicluster['size']}"
        job_output = os.path.join(experiment_dir, jobname)
        logfile = os.path.join(job_output, "log.out")

        # Do we have output?
        if os.path.exists(logfile) and not setup.force:
            relpath = os.path.relpath(logfile, experiment_dir)
            logger.warning(f"{relpath} already exists and force is False, skipping.")
            return

        if os.path.exists(logfile) and setup.force:
            logger.warning(f"Cleaning up previous run in {job_output}.")
            shutil.rmtree(job_output)

        kwargs = dict(job)
        del kwargs["command"]

        # Ensure we convert - map between job params and the flux restful api
        for convert in (
            ["num_tasks", "tasks"],
            ["cores_per_task", "cores"],
            ["gpus_per_task", "gpus"],
            ["num_nodes", "nodes"],
            ["workdir", "working_dir"],
        ):
            if convert[1] in kwargs:
                kwargs[convert[0]] = kwargs[convert[1]]
                del kwargs[convert[1]]

        # Submit the job, add the expected output file, and return
        logger.info(f"Submitting {jobname}: {job['command']}")
        res = cli.submit(command=job["command"], **kwargs)
        res["job_output"] = logfile
        return res
