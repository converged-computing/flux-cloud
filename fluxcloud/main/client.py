# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.utils as utils
from fluxcloud.main.decorator import job_timed, timed

here = os.path.dirname(os.path.abspath(__file__))


class ExperimentClient:
    """
    A base experiment client
    """

    def __init__(self, *args, **kwargs):
        import fluxcloud.main.settings as settings

        self.settings = settings.Settings
        self.times = {}

    def __repr__(self):
        return str(self)

    @timed
    def run_timed(self, name, cmd):
        return utils.run_command(cmd)

    @job_timed
    def run_timed_append(self, name, cmd, times):
        return utils.run_command(cmd)

    def __str__(self):
        return "[flux-cloud-client]"

    def get_script(self, name):
        """
        Get a named script from the cloud's script folder
        """
        script = os.path.join(here, "clouds", self.name, "scripts", name)
        if os.path.exists(script):
            return script

    def run(self, setup, force=False):
        """
        Run Flux Operator experiments in GKE

        1. create the cluster
        2. run each command and save output
        3. bring down the cluster
        """
        self.up(setup)
        self.apply(setup, force=force)
        self.down(setup)

    def down(self, *args, **kwargs):
        """
        Destroy a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    def apply(self, *args, **kwargs):
        """
        Apply (run) one or more experiments.
        """
        raise NotImplementedError

    def up(self, *args, **kwargs):
        """
        Bring up a cluster implemented by underlying cloud.
        """
        raise NotImplementedError
