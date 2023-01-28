# Copyright 2022-2023 Lawrence Livermore National Security, LLC
# SPDX-License-Identifier: Apache-2.0

__version__ = "0.1.17"
AUTHOR = "Vanessa Sochat"
EMAIL = "vsoch@users.noreply.github.com"
NAME = "flux-cloud"
PACKAGE_URL = "https://github.com/converged-computing/flux-cloud"
KEYWORDS = "cloud, flux, deployment"
DESCRIPTION = "deploy workflows to the flux operator in the cloud! 📦️"
LICENSE = "LICENSE"

################################################################################
# Global requirements

INSTALL_REQUIRES = (
    ("ruamel.yaml", {"min_version": None}),
    ("jsonschema", {"min_version": None}),
    ("requests", {"min_version": None}),
    ("jinja2", {"min_version": None}),
    ("flux-restful-client", {"min_version": None}),
)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

################################################################################
# Submodule Requirements (versions that include database)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES + TESTS_REQUIRES
