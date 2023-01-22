# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils

from .helpers import prepare_client, select_experiment


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)
    cli, setup, experiment = prepare_client(args, extra)

    if args.down_all:
        experiments = setup.matrices
    else:
        experiments = [select_experiment(setup, args.experiment_id)]

    # Bring down all experiments (minicluster size doesn't matter, it's one cluster)
    for experiment in experiments:
        cli.down(setup, experiment=experiment)
    setup.cleanup(setup.matrices)
