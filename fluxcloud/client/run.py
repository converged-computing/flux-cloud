# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from .helpers import prepare_client


def main(args, parser, extra, subparser):
    cli, setup, _ = prepare_client(args, extra)

    # Set the Minicluster size across experiments
    if args.size:
        setup.set_minicluster_size(args.size)

    cli.run(setup)
    setup.cleanup(setup.matrices)


def batch(args, parser, extra, subparser):
    cli, setup, _ = prepare_client(args, extra)

    # Set the Minicluster size across experiments
    if args.size:
        setup.set_minicluster_size(args.size)

    cli.batch(setup)
    setup.cleanup(setup.matrices)
