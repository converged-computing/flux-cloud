# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from .helpers import prepare_client


def main(args, parser, extra, subparser):
    cli, setup, experiment = prepare_client(args, extra)
    cli.up(setup, experiment=experiment)
    setup.cleanup(setup.matrices)
