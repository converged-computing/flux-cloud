# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.main.experiment as experiments
import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.decorator import timed

here = os.path.dirname(os.path.abspath(__file__))


class ExperimentClient:
    """
    A base experiment client
    """

    def __init__(self, *args, **kwargs):
        import fluxcloud.main.settings as settings

        self.quiet = kwargs.get("quiet", False)
        validate = kwargs.get("validate", True) or True
        self.settings = settings.Settings(kwargs.get("settings_file"), validate)
        self.times = {}

    def __repr__(self):
        return str(self)

    @timed
    def run_timed(self, name, cmd):
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

    def destroy(self, *args, **kwargs):
        """
        Destroy a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    def up(self, *args, **kwargs):
        """
        Bring up a cluster implemented by underlying cloud.
        """
        raise NotImplementedError

    def run(self, *args, **kwargs):
        """
        Run an experiment! Must be implemented by underlying cloud.
        """
        raise NotImplementedError

    def prepare_matrices(self, specfile, test=False):
        """
        Given an experiments.yaml, prepare matrices to run.
        """
        spec = utils.read_yaml(specfile)
        experiments.validate_experiments(spec)

        # Sploot out into matrices
        matrices = experiments.expand_experiments(spec)
        if not matrices:
            raise ValueError(
                "No matrices generated. Did you include any empty variables in your matrix?"
            )

        # Test mode means just one run
        if test:
            matrices = [matrices[0]]
        logger.info(f"🧪 Prepared {len(matrices)} experiment matrices")
        return matrices
