# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from fluxcloud.main.client import ExperimentClient


class AmazonCloud(ExperimentClient):
    """
    An Amazon EKS (Elastic Kubernetes Service) experiment runner.
    """

    name = "aws"

    def __init__(self, **kwargs):
        super(AmazonCloud, self).__init__(**kwargs)
        self.region = kwargs.get("region") or "us-east-1"

    def up(self, setup, experiment=None):
        """
        Bring up a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        create_script = self.get_script("cluster-create")
        tags = setup.get_tags(experiment)

        # AWS tags are key value pairs k=v
        self.check_tags(tags)

        # Create the cluster with creation script
        cmd = [
            create_script,
            "--region",
            self.region,
            "--machine",
            setup.get_machine(experiment),
            "--cluster",
            setup.get_cluster_name(experiment),
            "--cluster-version",
            setup.settings.kubernetes["version"],
            "--size",
            setup.get_size(experiment),
        ]
        if setup.force_cluster:
            cmd.append("--force-cluster")
        if tags:
            cmd += ["--tags", ",".join(tags)]

        # ssh key if provided must exist
        ssh_key = self.settings.aws.get("ssh_key")
        if ssh_key:
            if not os.path.exists(ssh_key):
                raise ValueError("ssh_key defined and does not exist: {ssh_key}")
            cmd += ["--ssh-key", ssh_key]

        return self.run_timed("create-cluster", cmd)

    def check_tags(self, tags):
        """
        Ensure tags are in format key=value
        """
        for tag in tags or []:
            if "=" not in tag:
                raise ValueError(
                    f"Cluster tags must be provided in format key=value, found {tag}"
                )

    def down(self, setup, experiment=None):
        """
        Destroy a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        destroy_script = self.get_script("cluster-destroy")

        # Create the cluster with creation script
        cmd = [
            destroy_script,
            "--region",
            self.region,
            "--cluster",
            setup.get_cluster_name(experiment),
        ]
        if setup.force_cluster:
            cmd.append("--force-cluster")
        return self.run_timed("destroy-cluster", cmd)
