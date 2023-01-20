# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from fluxcloud.main.client import ExperimentClient
from fluxcloud.main.decorator import save_meta


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

    @save_meta
    def up(self, setup, experiment=None):
        """
        Bring up a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        kwargs = {
            "experiment": experiment,
            "setup": setup,
            "project": self.project,
            "zone": self.get_zone(experiment),
        }
        create_script = experiment.get_script("cluster-create", self.name, kwargs)
        return self.run_timed("create-cluster", ["/bin/bash", create_script])

    def get_zone(self, experiment):
        """
        Get the region - using the experiment first and defaulting to settings
        """
        return experiment.variables.get("zone") or self.zone

    @save_meta
    def down(self, setup, experiment=None):
        """
        Destroy a cluster
        """
        experiment = experiment or setup.get_single_experiment()
        kwargs = {
            "experiment": experiment,
            "setup": setup,
            "zone": self.get_zone(experiment),
        }
        destroy_script = experiment.get_script("cluster-destroy", self.name, kwargs)
        return self.run_timed("destroy-cluster", ["/bin/bash", destroy_script])
