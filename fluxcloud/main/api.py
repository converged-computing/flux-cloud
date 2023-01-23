# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import atexit
import logging
import os
import shutil
import subprocess
import threading
import time
import uuid

from flux_restful_client.main import get_client

import fluxcloud.utils as utils
from fluxcloud.logger import logger

here = os.path.dirname(os.path.abspath(__file__))

exit_event = threading.Event()


class APIClient:
    def __init__(self, token=None, user=None):
        """
        API client wrapper.
        """
        self.user = token or os.environ.get("FLUX_USER") or "fluxuser"
        self.token = token or os.environ.get("FLUX_TOKEN") or str(uuid.uuid4())
        self.cli = get_client(user=self.user, token=self.token)
        self.proc = None
        self.broker_pod = None

    def check(self, experiment):
        """
        Set the basic auth for username and password and check it works
        """
        minicluster = experiment.minicluster
        get_broker_pod = experiment.get_shared_script(
            "broker-id", {"minicluster": minicluster}
        )

        logger.info("Waiting for id of running broker pod...")

        # We've already waited for them to be running
        broker_pod = None
        while not broker_pod:
            result = utils.run_capture(["/bin/bash", get_broker_pod], stream=True)

            # Save the broker pod, or exit on failure.
            if result["message"]:
                broker_pod = result["message"].strip()

        self.broker_pod = broker_pod
        self.port_forward(minicluster["namespace"], self.broker_pod)

    def port_forward(self, namespace, broker_pod):
        """
        Ask user to open port to forward
        """
        command = ["kubectl", "port-forward", "-n", namespace, broker_pod, "5000:5000"]

        # This is detached - we can kill but not interact
        logger.info(" ".join(command))
        self.proc = proc = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL if logger.level >= logging.DEBUG else None,
        )

        def cleanup():
            proc.kill()

        # Ensure we cleanup if anything goes wrong
        atexit.register(cleanup)

    def submit(self, setup, experiment, size):
        """
        Use the client to submit the jobs programatically.
        """
        # Submit jobs!

        # Sleep time will be time of last job, assuming they are similar
        sleep_time = 5
        for jobname, job in experiment.jobs.items():

            # Do we want to run this job for this size and machine?
            if not experiment.check_job_run(job, size):
                logger.debug(
                    f"Skipping job {jobname} as does not match inclusion criteria."
                )
                continue

            if "command" not in job:
                logger.debug(f"Skipping job {jobname} as does not have a command.")
                continue

            # The experiment is defined by the machine type and size
            experiment_dir = experiment.root_dir

            # Add the size
            jobname = f"{jobname}-minicluster-size-{size}"
            job_output = os.path.join(experiment_dir, jobname)
            logfile = os.path.join(job_output, "log.out")

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

            kwargs = dict(job)
            del kwargs["command"]

            # Assume the task gets all nodes, unless specified in job
            # Also assume the flux restful server is using one node
            if "nodes" not in kwargs:
                kwargs["nodes"] = size - 1
            if "tasks" not in kwargs:
                kwargs["tasks"] = size - 1

            # Ensure we convert - map between job params and the flux restful api
            for convert in (
                ["num_tasks", "tasks"],
                ["cores_per_task", "cores"],
                ["gpus_per_task", "gpus"],
                ["num_nodes", "nodes"],
            ):
                if convert[1] in kwargs:
                    kwargs[convert[0]] = kwargs[convert[1]]

            # Let's also keep track of actual time to get logs, info, etc.
            start = time.time()

            # Run and block output until job is done
            res = self.cli.submit(command=job["command"], **kwargs)

            logger.info(f"Submitting {jobname}: {job['command']}")
            info = self.cli.jobs(res["id"])

            while info["returncode"] == "":
                info = self.cli.jobs(res["id"])
                time.sleep(sleep_time)

            end1 = time.time()
            output = self.cli.output(res["id"]).get("Output")
            if output:
                utils.write_file("".join(output), logfile)
            end2 = time.time()

            # Get the full job info, and add some wrapper times
            info = self.cli.jobs(res["id"])
            info["start_to_info_seconds"] = end1 - start
            info["start_to_output_seconds"] = end2 - start

            yield jobname, info
            sleep_time = info["runtime"]

        # Kill the connection to the service
        self.proc.kill()
