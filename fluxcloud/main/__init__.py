# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


def get_experiment_client(cloud=None, force_cluster=False):
    """
    Create the cloud experiment client.
    """
    import fluxcloud.main.client as clients
    import fluxcloud.main.clouds as clouds
    import fluxcloud.main.settings as settings

    cloud = cloud or settings.Settings.default_cloud

    # Create the cloud client
    if cloud:
        cloud = clouds.get_cloud(cloud)
    else:
        cloud = clients.ExperimentClient
    return cloud(force_cluster=force_cluster)
