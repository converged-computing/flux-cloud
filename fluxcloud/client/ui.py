# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from fluxcloud.logger import logger

from .helpers import prepare_client


def main(args, parser, extra, subparser):
    """
    open the ui by starting flux
    """
    cli, setup, experiment = prepare_client(args, extra)
    size = args.size
    if not size and len(experiment.minicluster.get("size")) != 1:
        logger.exit(
            "Your MiniCluster has more than one size - please define the targer size with --size."
        )
    elif not size:
        size = experiment.minicluster["size"][0]
    logger.info(f"Selected size {size} MiniCluster to open user interface.")
    cli.open_ui(setup, experiment=experiment, size=size, persistent=True)
