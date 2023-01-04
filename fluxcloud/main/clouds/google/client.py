# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from fluxcloud.main.client import ExperimentClient


class GoogleCloud(ExperimentClient):
    """
    A Google Cloud GKE experiment runner.
    """

    name = "google"

    def __init__(self, **kwargs):
        super(GoogleCloud, self).__init__(**kwargs)
        self.zone = kwargs.get("zone") or "us-central1-a"
        self.project = kwargs.get("project") or self.settings.google["project"]

        # No project, no go
        if not self.project:
            raise ValueError(
                "Please provide your Google Cloud project in your settings.yml or flux-cloud set google:project <project>"
            )

    def up(self, setup, experiment=None):
        """
        Bring up a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        create_script = self.get_script("cluster-create")
        tags = setup.get_tags(experiment)

        # Create the cluster with creation script
        cmd = [
            create_script,
            "--project",
            self.project,
            "--zone",
            self.zone,
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
        return self.run_timed("create-cluster", cmd)

    def down(self, setup, experiment=None):
        """
        Destroy a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        destroy_script = self.get_script("cluster-destroy")

        # Create the cluster with creation script
        cmd = [
            destroy_script,
            "--zone",
            self.zone,
            "--cluster",
            setup.get_cluster_name(experiment),
        ]
        if setup.force_cluster:
            cmd.append("--force-cluster")
        return self.run_timed("destroy-cluster", cmd)
