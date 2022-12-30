# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0


def get_experiment_client(quiet=False, settings_file=None, cloud=None, **kwargs):
    """
    Create the cloud experiment client.
    """
    import fluxcloud.main.clouds as clouds
    import fluxcloud.main.settings as settings
    from fluxcloud.main.client import ExperimentClient

    validate = kwargs.get("validate", True) or True
    settings = settings.Settings(kwargs.get("settings_file"), validate)
    cloud = cloud or settings.default_cloud

    # Create the cloud client
    if cloud:
        cloud = clouds.get_cloud(cloud)
    else:
        cloud = ExperimentClient
    return cloud(quiet=quiet, settings_file=settings_file)
