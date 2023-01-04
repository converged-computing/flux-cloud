# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import jinja2

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.client import ExperimentClient

here = os.path.dirname(os.path.abspath(__file__))


class AmazonCloud(ExperimentClient):
    """
    An Amazon EKS (Elastic Kubernetes Service) experiment runner.
    """

    name = "aws"

    def __init__(self, **kwargs):
        super(AmazonCloud, self).__init__(**kwargs)
        self.region = kwargs.get("region") or "us-east-1"

        # This could eventually just be provided
        self.config_template = os.path.join(here, "templates", "cluster-config.yaml")

    def up(self, setup, experiment=None):
        """
        Bring up a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        create_script = self.get_script("cluster-create")

        # ssh key if provided must exist
        ssh_key = self.settings.aws.get("ssh_key")
        if ssh_key and not os.path.exists(ssh_key):
            raise ValueError("ssh_key defined and does not exist: {ssh_key}")

        tags = self.get_tags(experiment)

        # Create the cluster with creation script, write to temporary file
        template = self.generate_config(setup, experiment)
        config_file = utils.get_tmpfile(prefix="eksctl-config", suffix=".yaml")
        utils.write_file(template, config_file)

        # Most of these are not needed, but provided for terminal printing
        # and consistent output with Google GKE runner
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
            "--config",
            config_file,
            "--size",
            setup.get_size(experiment),
        ]
        if setup.force_cluster:
            cmd.append("--force-cluster")
        if tags:
            cmd += ["--tags", ",".join(tags)]

        # Cleanup function to remove temporary file
        def cleanup():
            if os.path.exists(config_file):
                os.remove(config_file)

        return self.run_timed("create-cluster", cmd, cleanup)

    def get_tags(self, experiment):
        """
        Convert cluster tags into list of key value pairs
        """
        tags = {}
        for tag in experiment.get("cluster", {}).get("tags") or []:
            if "=" not in tag:
                raise ValueError(
                    f"Cluster tags must be provided in format key=value, found {tag}"
                )
            key, value = tag.split("=", 1)
            tags[key] = value
        return tags

    def generate_config(self, setup, experiment):
        """
        Generate the config to create the cluster.

        Note that we could use the command line client alone but it doesn't
        support all options. Badoom fzzzz.
        """
        template = jinja2.Template(utils.read_file(self.config_template))
        values = {}

        # Cluster name, kubernetes version, and region
        values["cluster_name"] = setup.get_cluster_name(experiment)
        values["region"] = self.region
        values["machine"] = setup.get_machine(experiment)
        values["kubernetes_version"] = setup.settings.kubernetes["version"]
        values["size"] = setup.get_size(experiment)
        values["ssh_key"] = self.settings.aws.get("ssh_key")

        # Optional booleans
        for key in ["private_networking", "efa_enabled"]:
            value = self.settings.aws.get("private_networking")
            if value is True:
                values[key] = value

        result = template.render(**values)
        logger.debug(result)
        return result

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
