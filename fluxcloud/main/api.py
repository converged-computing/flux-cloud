# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import uuid
import time

from flux_restful_client.main import get_client
import fluxcloud.utils as utils
from fluxcloud.logger import logger
import threading

here = os.path.dirname(os.path.abspath(__file__))

exit_event = threading.Event()

class APIClient:

    def __init__(self, token=None, user=None):
        """
        API client wrapper.
        """
        self.user = token or os.environ.get('FLUX_USER') or "fluxuser"
        self.token = token or os.environ.get('FLUX_TOKEN') or str(uuid.uuid4())
        self.cli = get_client(user=self.user, token=self.token)
        self.pid = None
        self.broker_pod = None

    def check(self, experiment):
        """
        Set the basic auth for username and password and check it works
        """
        minicluster = experiment.minicluster
        get_broker_pod = experiment.get_shared_script("broker-id", {"minicluster": minicluster})

        logger.info('Waiting for id of running broker pod...')
 
        # We've already waited for them to be running
        broker_pod = None
        while not broker_pod:
            result = utils.run_capture(["/bin/bash", get_broker_pod], stream=True)

            # Save the broker pod, or exit on failure.
            if result['message']:
                broker_pod = result['message'].strip()        

        self.broker_pod = broker_pod
        self.port_forward(minicluster['namespace'], self.broker_pod)

    # Create a port forward via threading
    def port_forward(self, namespace, broker_pod):
        """
        Ask user to open port to forward
        """
        command = f"kubectl port-forward -n {namespace} {broker_pod} 5000:5000"

        # Try to list nodes
        retry = 0
        while True and retry < 3:
            if not utils.confirm_action(f"Please run the following command in another terminal to connect to your cluster:\n{command}\nAre you done?"):
                logger.exit('We cannot port forward without connecting to the RESTFul API.')
            try:
                self.cli.list_nodes()
                return
            except Exception as e:
                time.sleep(5)
                retry += 1

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
                logger.debug(
                    f"Skipping job {jobname} as does not have a command."
                )
                continue
       
            # The experiment is defined by the machine type and size
            experiment_dir = experiment.root_dir

            # Add the size
            jobname = f"{jobname}-minicluster-size-{size}"
            job_output = os.path.join(experiment_dir, jobname)
            logfile = os.path.join(job_output, "log.out")

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

            kwargs = dict(job)
            del kwargs['command']
 
            # Assume the task gets all nodes, unless specified in job
            # Also assume the flux restful server is using one node
            if "nodes" not in kwargs:
                kwargs['nodes'] = size-1 
            if "tasks" not in kwargs:
                kwargs['tasks'] = size-1

            # Ensure we convert - map between job params and the flux restful api
            for convert in ['num_tasks', 'tasks'], ['cores_per_task', 'cores'], ['gpus_per_task', 'gpus'], ['num_nodes', 'nodes']:
                if convert[1] in kwargs:
                    kwargs[convert[0]] = kwargs[convert[1]]
            
            # Run and block output until job is done
            res = self.cli.submit(command=job['command'], **kwargs)
            
            logger.info(f"Submitting {jobname}: {job['command']}")
            if job.get('has_output', True) != False:
                output = None
                while not output or "output does not exist yet" in output:
                    output = self.cli.output(res['id']).get('Output')
                    print('.', end='')
                    time.sleep(sleep_time) 
            else:
                logger.info('Job is not expected to have output.')
                time.sleep(sleep_time) 

            utils.write_file(''.join(output), logfile)

            # Get the full job info
            info = self.cli.jobs(res['id'])
            yield jobname, info
            sleep_time = info['runtime']

        #self.thread.raise_exception()