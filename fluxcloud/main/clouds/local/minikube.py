# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.client import ExperimentClient
from fluxcloud.main.decorator import save_meta


class MiniKube(ExperimentClient):
    """
    A Local MiniKube cluster.
    """

    name = "minikube"

    @save_meta
    def up(self, setup, experiment=None):
        """
        Bring up a MiniKube cluster
        """
        experiment = experiment or setup.get_single_experiment()

        # Variables to populate template
        kwargs = {"experiment": experiment, "setup": setup}
        create_script = experiment.get_script(
            "cluster-create-minikube", "local", kwargs
        )

        # Create the cluster with creation script
        return self.run_timed("create-cluster", ["/bin/bash", create_script])

    def pre_apply(self, experiment, jobname, job):
        """
        If we have the container image for a job, ensure to pull it first.
        """
        if "image" not in job:
            logger.warning('"image" not found in job, cannot pre-pull for MiniKube')
            return

        # Does minikube already have the image pulled?
        existing = utils.run_capture(["minikube", "image", "ls"], True)
        if job["image"] in existing["message"]:
            return

        # cmd = ["minikube", "ssh", "docker", "pull", job["image"]]
        logger.info(f"{job['image']} is being pre-pulled, please wait...")
        cmd = ["minikube", "image", "load", job["image"]]

        # Don't pull again if we've done it once
        return self.run_command(cmd)

    @save_meta
    def down(self, setup, experiment=None):
        """
        Destroy a cluster
        """
        experiment = experiment or setup.get_single_experiment()

        kwargs = {"experiment": experiment, "setup": setup}
        destroy_script = experiment.get_script(
            "cluster-destroy-minikube", "local", kwargs
        )

        # If we aren't cleaning up, show path to destroy script in debug
        return self.run_timed("destroy-cluster", ["/bin/bash", destroy_script])
