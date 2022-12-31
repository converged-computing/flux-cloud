#!/usr/bin/env python

# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import sys

import fluxcloud
import fluxcloud.main.clouds as clouds
from fluxcloud.logger import setup_logger
from fluxcloud.main.settings import setup_settings


def get_parser():
    parser = argparse.ArgumentParser(
        description="Flux Kubernetes Experiment Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global Variables
    parser.add_argument(
        "--debug",
        dest="debug",
        help="use verbose logging to debug.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        help="print additional solver output (atoms).",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--settings-file",
        dest="settings_file",
        help="custom path to settings file.",
    )

    # On the fly updates to config params
    parser.add_argument(
        "-c",
        dest="config_params",
        help=""""customize a config value on the fly to ADD/SET/REMOVE for a command
fluxcloud -c set:key:value <command> <args>
fluxcloud -c add:registry:/tmp/registry <command> <args>
fluxcloud -c rm:registry:/tmp/registry""",
        action="append",
    )
    parser.add_argument(
        "--version",
        dest="version",
        help="show software version.",
        default=False,
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        help="fluxcloud actions",
        title="actions",
        description="actions",
        dest="command",
    )

    # print version and exit
    subparsers.add_parser("version", description="show software version")

    # Local shell with client loaded
    shell = subparsers.add_parser(
        "shell",
        description="shell into a Python session with a client.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    shell.add_argument(
        "--interpreter",
        "-i",
        dest="interpreter",
        help="python interpreter",
        choices=["ipython", "python", "bpython"],
        default="ipython",
    )

    config = subparsers.add_parser(
        "config",
        description="update configuration settings. Use set or get to see or set information.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    config.add_argument(
        "--central",
        dest="central",
        help="make edits to the central config file.",
        default=False,
        action="store_true",
    )

    config.add_argument(
        "params",
        nargs="*",
        help="""Set or get a config value, edit the config, add or remove a list variable, or create a user-specific config.
flux-cloud config set key value
flux-cloud config set key:subkey value
flux-cloud config get key
flux-cloud edit
flux-cloud config inituser
flux-cloud config remove cloud aws
flux-cloud config add cloud aws""",
        type=str,
    )

    # Experiment runner is "run"
    run = subparsers.add_parser(
        "run",
        description="Main run command to run experiments",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    apply = subparsers.add_parser(
        "apply",
        description="Apply experiments (CRDs) to the cluster.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    up = subparsers.add_parser(
        "up",
        description="Bring up a cluster and install the operator",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    down = subparsers.add_parser(
        "down",
        description="Bring down or destroy a cluster",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    down.add_argument(
        "--all",
        default=False,
        action="store_true",
        help="Bring down all experiment clusters",
        dest="down_all",
    )

    listing = subparsers.add_parser(
        "list",
        description="List experiment ids available.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    for command in run, up, down, apply, listing:
        command.add_argument(
            "experiments",
            default="experiments.yaml",
            help="Yaml file with experiments (first positional argument)",
            nargs="?",
        )
        command.add_argument("--cluster-version", help="GKE version", type=float)
        command.add_argument(
            "-c",
            "--cloud",
            help="cloud to use",
            choices=clouds.cloud_names,
        )

    for command in apply, up, down:
        command.add_argument(
            "--id",
            "-e",
            dest="experiment_id",
            help="experiment ID to apply to (<machine>-<size>)",
        )

    for command in run, apply:
        command.add_argument(
            "-o",
            "--output-dir",
            help="directory to write output to",
            default=os.path.join(os.getcwd(), "data"),
        )
        command.add_argument(
            "--test",
            help="Only run first experiment in matrix (test mode)",
            default=False,
            action="store_true",
        )
        command.add_argument(
            "--template",
            help="minicluster yaml template to populate for experiments (defaults to minicluster-template.yaml",
            default="minicluster-template.yaml",
        )
        command.add_argument(
            "--force",
            help="force re-run if experiment already exists.",
            default=False,
            action="store_true",
        )

    return parser


def run():
    parser = get_parser()

    def help(return_code=0):
        version = fluxcloud.__version__

        print("\nflux-cloud Kubernetes Experiment Client v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    if args.debug is True:
        os.environ["MESSAGELEVEL"] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version:
        print(fluxcloud.__version__)
        sys.exit(0)

    setup_logger(quiet=args.quiet, debug=args.debug)
    setup_settings(args.settings_file)

    # retrieve subparser (with help) from parser
    helper = None
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == args.command:
                helper = subparser
                break

    # Does the user want a shell?
    if args.command == "apply":
        from .apply import main
    elif args.command == "list":
        from .listing import main
    elif args.command == "run":
        from .run import main
    elif args.command == "config":
        from .config import main
    elif args.command == "up":
        from .up import main
    elif args.command == "down":
        from .down import main

    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args, parser=parser, extra=extra, subparser=helper)
        sys.exit(return_code)
    except UnboundLocalError:
        return_code = 1

    help(return_code)


if __name__ == "__main__":
    run()
