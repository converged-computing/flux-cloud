# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.utils as utils

install_dir = utils.get_installdir()
reps = {"$install_dir": install_dir, "$root_dir": os.path.dirname(install_dir)}

# The default settings file in the install root
default_settings_file = os.path.join(reps["$install_dir"], "settings.yml")

# Default template if one is not provided
default_minicluster_template = os.path.join(install_dir, "minicluster-template.yaml")

# User home
userhome = os.path.expanduser("~/.fluxcloud")

# The user settings file can be created to over-ride default
user_settings_file = os.path.join(userhome, "settings.yml")

# variables in settings that allow environment variable expansion
allowed_envars = ["HOME"]

# default cluster name
default_cluster_name = "flux-cluster"
default_namespace = "flux-operator"

# The default GitHub repository
github_url = "https://github.com/converged-computing/flux-cloud"
