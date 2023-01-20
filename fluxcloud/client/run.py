# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.utils as utils
from fluxcloud.main import get_experiment_client
from fluxcloud.main.experiment import ExperimentSetup


def main(args, parser, extra, subparser):
    utils.ensure_no_extra(extra)

    cli = get_experiment_client(args.cloud)
    setup = ExperimentSetup(
        args.experiments,
        template=args.template,
        outdir=args.output_dir,
        test=args.test,
        cleanup=args.cleanup,
        force_cluster=args.force_cluster,
        force=args.force,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)
    setup.settings.update_params(args.config_params)

    # Set the Minicluster size across experiments
    if args.size:
        setup.set_minicluster_size(args.size)

    cli.run(setup)
    setup.cleanup(setup.matrices)
