# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils
from fluxcloud.main import get_experiment_client
from fluxcloud.main.experiment import ExperimentSetup

from .helpers import select_experiment


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)

    cli = get_experiment_client(args.cloud)
    setup = ExperimentSetup(
        args.experiments,
        quiet=True,
        cleanup=args.cleanup,
        force_cluster=args.force_cluster,
        outdir=args.output_dir,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)
    setup.settings.update_params(args.config_params)

    if args.down_all:
        experiments = setup.matrices
    else:
        experiments = [select_experiment(setup, args.experiment_id)]

    # Bring down all experiments (minicluster size doesn't matter, it's one cluster)
    for experiment in experiments:
        cli.down(setup, experiment=experiment)
    setup.cleanup(setup.matrices)
