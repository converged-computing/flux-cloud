# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.experiment import ExperimentSetup


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)
    setup = ExperimentSetup(args.experiments, quiet=True)
    setup.settings.update_params(args.config_params)
    for experiment in setup.matrices:
        logger.info(experiment.expid)
        sizes = experiment.minicluster["size"]
        if sizes:
            logger.info("  sizes:")
            for size in sizes:
                logger.info(f"    {size}: {experiment.expid} {size}")
