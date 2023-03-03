# Copyright 2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import fluxcloud.main.template as templates
from fluxcloud.main import get_experiment_client
from fluxcloud.logger import logger

def main(args, parser, extra, subparser):
    """
    apply parser submits via separate CRDs.
    """
    cli = get_experiment_client(args.cloud)
    if args.experiment_command == "init":
        if cli.name == "aws":
            print(templates.aws_experiment_template)
        elif cli.name in ['google', 'gcp']:
            print(templates.google_experiment_template)
        elif cli.name == "minikube":
            print(templates.minikube_experiment_template)
        else:
            logger.error(f'Client {cli.name} is not a recognized cloud')

    else:
        logger.exit(f'{args.experiment_command} is not recognized. Try "init"')


