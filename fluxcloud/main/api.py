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
from fluxoperator.client import FluxOperator

from fluxcloud.logger import logger

here = os.path.dirname(os.path.abspath(__file__))


class APIClient:
    def __init__(self, token=None, user=None):
        """
        API client wrapper.
        """
        self.user = token or os.environ.get("FLUX_USER") or user or "fluxuser"
        self.token = token or os.environ.get("FLUX_TOKEN") or str(uuid.uuid4())
        self.proc = None
        self.broker_pod = None

    def show_credentials(self):
        """
        Show the token and user, if requested.
        """
        logger.info("MiniCluster created with credentials:")
        logger.info(f"  FLUX_USER={self.user}")
        logger.info(f"  FLUX_TOKEN={self.token}")

    def _create_minicluster(self, operator, minicluster, experiment, job):
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

        # Add Flux Restful user and token
        minicluster["flux_restful"] = {"username": self.user, "token": self.token}

        # The operator will time creation through pods being ready
        try:
            result = operator.create_minicluster(**minicluster, container=job)
        except Exception as e:
            msg = f"Try: 'kubectl delete -n {namespace} minicluster {name}'"
            logger.exit(f"There was an issue creating the MiniCluster: {e}\n{msg}")

        # Wait for pods to be ready to include in minicluster up time
        self.show_credentials()

        # Save MiniCluster metadata
        image_slug = re.sub("(:|/)", "-", image)
        uid = f"{size}-{name}-{image_slug}"
        experiment.save_json(result, f"minicluster-size-{uid}.json")

        # This is a good point to also save nodes metadata
        nodes = operator.get_nodes()
        operator.wait_pods(quiet=True)
        pods = operator.get_pods()

        experiment.save_file(nodes.to_str(), f"nodes-{uid}.json")
        experiment.save_file(pods.to_str(), f"pods-size-{uid}.json")
        return result

    def apply(self, experiment, minicluster, job=None, outfile=None, stdout=True):
        """
        Use the client to apply (1:1 job,minicluster) the jobs programatically.
        """
        namespace = minicluster["namespace"]
        name = minicluster["name"]

        # Interact with the Flux Operator Python SDK
        operator = FluxOperator(namespace)
        self._create_minicluster(operator, minicluster, experiment, job)

        # Get the broker pod (this would also wait for all pods to be ready)
        broker = operator.get_broker_pod()

        # Time from when broker pod (and all pods are ready)
        start = time.time()

        # Get the pod to stream output from directly
        if outfile is not None:
            operator.stream_output(outfile, pod=broker, stdout=stdout)

        # When output done streaming, job is done
        end = time.time()
        logger.info(f"Job {name} is complete! Cleaning up MiniCluster...")

        # This also waits for termination (and pods to be gone) and times it
        operator.delete_minicluster(name=name, namespace=namespace)

        # TODO likely need to separate minicluster up/down times.
        results = {"times": operator.times}
        results["times"][name] = end - start
        return results

    def submit(self, setup, experiment, minicluster, job, poll_seconds=20):
        """
        Use the client to submit the jobs programatically.
        """
        namespace = minicluster["namespace"]
        image = job["image"]
        name = minicluster["name"]
        size = minicluster["size"]

        # Interact with the Flux Operator Python SDK
        operator = FluxOperator(namespace)
        self._create_minicluster(operator, minicluster, experiment, job)

        # Get the broker pod (this would also wait for all pods to be ready)
        broker = operator.get_broker_pod()

        # Return results (and times) to calling client
        results = {}

        # Submit jobs via port forward - this waits until the server is ready
        with operator.port_forward(broker) as forward_url:
            print(f"Port forward opened to {forward_url}")

            # See https://flux-framework.org/flux-restful-api/getting_started/api.html
            cli = get_client(host=forward_url, user=self.user, token=self.token)
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
                    info = cli.jobs(job["id"])
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

        logger.info("All jobs are complete! Cleaning up MiniCluster...")

        # This also waits for termination (and pods to be gone) and times it
        operator.delete_minicluster(name=name, namespace=namespace)

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

        # Assume the task gets all nodes, unless specified in job
        # Also assume the flux restful server is using one node
        if "nodes" not in kwargs:
            kwargs["nodes"] = minicluster["size"] - 1
        if "tasks" not in kwargs:
            kwargs["tasks"] = minicluster["size"] - 1

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

        # Submit the job, add the expected output file, and return
        logger.info(f"Submitting {jobname}: {job['command']}")
        res = cli.submit(command=job["command"], **kwargs)
        res["job_output"] = logfile
        return res
