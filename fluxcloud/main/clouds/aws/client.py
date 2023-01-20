# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import jinja2

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.client import ExperimentClient
from fluxcloud.main.decorator import save_meta

here = os.path.dirname(os.path.abspath(__file__))


class AmazonCloud(ExperimentClient):
    """
    An Amazon EKS (Elastic Kubernetes Service) experiment runner.
    """

    name = "aws"

    def __init__(self, **kwargs):
        super(AmazonCloud, self).__init__(**kwargs)
        self.region = (
            kwargs.get("region") or self.settings.aws.get("region") or "us-east-1"
        )

        # This could eventually just be provided
        self.config_template = os.path.join(here, "templates", "cluster-config.yaml")

    @save_meta
    def up(self, setup, experiment=None):
        """
        Bring up a cluster
        """
        experiment = experiment or setup.get_single_experiment()

        # ssh key if provided must exist
        ssh_key = self.settings.aws.get("ssh_key")
        if ssh_key and not os.path.exists(ssh_key):
            raise ValueError("ssh_key defined and does not exist: {ssh_key}")

        # Create the cluster with creation script, write to temporary file
        config_file = self.generate_config(setup, experiment)
        tags = ",".join(self.get_tags(experiment))
        kwargs = {
            "experiment": experiment,
            "setup": setup,
            "region": self.get_region(experiment),
            "config_file": config_file,
            "tags": tags,
        }
        create_script = experiment.get_script("cluster-create", self.name, kwargs)
        return self.run_timed("create-cluster", ["/bin/bash", create_script])

    def get_region(self, experiment):
        """
        Get the region - using the experiment first and defaulting to settings
        """
        return experiment.variables.get("region") or self.region

    def get_tags(self, experiment):
        """
        Convert cluster tags into list of key value pairs
        """
        tags = {}
        for tag in experiment.tags or []:
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

        # Write to experiment scripts directory
        config_file = os.path.join(experiment.script_dir, "eksctl-config.yaml")
        if not os.path.exists(experiment.script_dir):
            utils.mkdir_p(experiment.script_dir)

        # Experiment variables and custom variables
        values = {
            "experiment": experiment,
            "setup": setup,
            "region": self.get_region(experiment),
            "variables": experiment.variables,
            "tags": self.get_tags(experiment),
        }

        # Optional booleans for settings, don't take preference over experiment
        for key, value in self.settings.aws.get("variables", {}).items():
            if value and key not in values["variables"]:
                values["variables"][key] = value

        # Add zones if not present!
        region = self.get_region(experiment)
        if "availability_zones" not in values["variables"]:
            values["variables"]["availability_zones"] = [
                "%sa" % region,
                "%sb" % region,
            ]

        # Show the user custom variables
        for key, value in values["variables"].items():
            logger.info(f"> Custom variable: {key}={value}")

        result = template.render(**values)
        logger.debug(result)
        utils.write_file(result, config_file)
        return config_file

    @save_meta
    def down(self, setup, experiment=None):
        """
        Destroy a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        kwargs = {
            "setup": setup,
            "experiment": experiment,
            "region": self.get_region(experiment),
        }
        destroy_script = experiment.get_script("cluster-destroy", self.name, kwargs)
        return self.run_timed("destroy-cluster", ["/bin/bash", destroy_script])
