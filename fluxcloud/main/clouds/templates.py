# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

from jinja2 import Environment, FileSystemLoader

import fluxcloud.utils as utils
from fluxcloud.logger import logger

here = os.path.dirname(os.path.abspath(__file__))


class Script:
    """
    A script template.
    """

    def __init__(self, cloud, script):
        self.cloud = cloud
        self.script = script

    @property
    def script_path(self):
        return os.path.join(self.script_root, self.script)

    @property
    def script_root(self):
        return os.path.join(here, self.cloud, "scripts")

    @property
    def shared_root(self):
        return os.path.join(here, "shared", "scripts")

    def render(self, outfile=None, **kwargs):
        """
        Load the wrapper script.
        """
        # Ensure we add each only once
        include_paths = list(set([self.script_root, self.shared_root]))

        # This is a dict with either path (filesystem to load) or loaded (content)
        loader = FileSystemLoader(include_paths)
        env = Environment(loader=loader)

        # Do we have a filesystem path to load directly?
        # Note this path is relative to a template directory
        template = env.get_template(self.script)

        out = template.render(**kwargs)
        if outfile:
            logger.debug(f"Writing template script {self.script} to {outfile}")
            utils.write_file(out, outfile, exec=True)
            return outfile

        # Otherwise return output
        return out
