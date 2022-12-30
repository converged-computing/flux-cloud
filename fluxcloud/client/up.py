# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main import get_experiment_client


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)

    cli = get_experiment_client(
        quiet=args.quiet,
        settings_file=args.settings_file,
        cloud=args.cloud,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    try:
        cli.up(args.experiments)
    except Exception as e:
        logger.exit(f"Issue with up: {e}")
