# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess

from fluxcloud.logger import logger


def ensure_no_extra(extra):
    """
    Ensure no extra arguments (in case typos)
    """
    if extra:
        logger.exit(
            "Extra arguments provided that are not known to this command: %s"
            % " ".join(extra)
        )


def check_install(software, quiet=True, command="--version"):
    """
    check_install will attempt to run the singularity command, and
    return True if installed. The command line utils will not run
    without this check.

    Parameters
    ==========
    software: the software to check if installed
    quiet: should we be quiet? (default True)
    command: the command to use to check (defaults to --version)
    """
    cmd = [software, command]
    try:
        version = run_command(cmd, software)
    except Exception:
        return False
    if version:
        if not quiet and version["return_code"] == 0:
            version = version["message"]
            logger.info("Found %s version %s" % (software.upper(), version))
        return True
    return False


def get_installdir():
    """
    get_installdir returns the installation directory of the application
    """
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def run_command(cmd):
    """
    run_command uses subprocess to send a command to the terminal.
    """
    return subprocess.run(cmd)


def run_capture(cmd, stream=False):
    """
    run_capture uses subprocess to send a command to the terminal.

    Parameters
    ==========
    cmd: the command to send, should be a list for subprocess
    error_message: the error message to give to user if fails,
    if none specified, will alert that command failed.

    """
    stdout = subprocess.PIPE if stream else None
    output = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=stdout)

    t = output.communicate()[0], output.returncode
    output = {"message": t[0], "return_code": t[1]}

    if isinstance(output["message"], bytes):
        output["message"] = output["message"].decode("utf-8")

    return output


def confirm_action(question, force=False):
    """confirm if the user wants to perform a certain action

    Parameters
    ==========
    question: the question that will be asked
    force: if the user wants to skip the prompt
    """
    if force is True:
        return True

    response = input(question + " (yes/no)? ")
    while len(response) < 1 or response[0].lower().strip() not in "ynyesno":
        response = input("Please answer yes or no: ")

    if response[0].lower().strip() in "no":
        return False

    return True


def confirm_uninstall(filename, force=False):
    """confirm if the user wants to uninstall a module

    Parameters
    ==========
    filename: the file that will be removed
    force: if the user wants to skip the prompt
    """
    return confirm_action(
        "Are you sure you want to uninstall {}".format(filename), force
    )
