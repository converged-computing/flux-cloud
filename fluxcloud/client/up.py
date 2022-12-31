# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main import get_experiment_client
from fluxcloud.main.experiment import ExperimentSetup

from .helpers import select_experiment


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)

    cli = get_experiment_client(args.cloud)
    setup = ExperimentSetup(
        args.experiments, quiet=True, force_cluster=args.force_cluster
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)
    setup.settings.update_params(args.config_params)
    experiment = select_experiment(setup, args.experiment_id)

    try:
        cli.up(setup, experiment=experiment)
    except Exception as e:
        logger.exit(f"Issue with up: {e}")
