# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from .helpers import prepare_client


def main(args, parser, extra, subparser):
    """
    apply parser submits via separate CRDs.
    """
    cli, setup, experiment = prepare_client(args, extra)
    cli.apply(setup, experiment=experiment)
    setup.cleanup(setup.matrices)


def submit(args, parser, extra, subparser):
    """
    submit parser submits via the Flux Restful API to one cluster
    """
    cli, setup, experiment = prepare_client(args, extra)
    cli.submit(setup, experiment=experiment)
    setup.cleanup(setup.matrices)
