# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os

import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main import get_experiment_client
from fluxcloud.main.experiment import ExperimentSetup


def prepare_client(args, extra):
    """
    apply parser submits via separate CRDs.
    """
    utils.ensure_no_extra(extra)

    cli = get_experiment_client(args.cloud)
    setup = ExperimentSetup(
        args.experiments,
        force_cluster=args.force_cluster,
        template=args.template,
        cleanup=args.cleanup,
        # Ensure the output directory is namespaced by the cloud name
        outdir=os.path.join(args.output_dir, cli.name),
        test=args.test,
        quiet=True,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)
    setup.settings.update_params(args.config_params)
    experiment = select_experiment(setup, args.experiment_id, args.size)
    return cli, setup, experiment


def select_experiment(setup, experiment_id, size=None):
    """
    Select a named experiment based on id, or choose the first.
    """
    experiment = None
    choices = " ".join([x.expid for x in setup.matrices])
    if not experiment_id:
        experiment = setup.matrices[0]
        logger.warning(
            f"No experiment ID provided, assuming first experiment {experiment.expid}."
        )
    else:
        for entry in setup.matrices:
            if entry.expid == experiment_id:
                experiment = entry
                logger.info(f"Selected experiment {experiment.expid}.")
                break

    if not experiment:
        logger.exit(
            f"Cannot find experiment with matching id {experiment_id}, choices are {choices}"
        )

    # Once we are down here, if a size is selected, update
    if size:
        experiment.set_minicluster_size(size)
    return experiment
