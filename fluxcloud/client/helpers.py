# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

from fluxcloud.logger import logger


def select_experiment(setup, experiment_id):
    """
    Select a named experiment based on id, or choose the first.
    """
    experiment = None
    choices = " ".join([x["id"] for x in setup.matrices])
    if not experiment_id:
        experiment = setup.matrices[0]
        logger.warning(
            f"No experiment ID provided, assuming first experiment {experiment['id']}."
        )
    else:
        for entry in setup.matrices:
            if entry["id"] == experiment_id:
                experiment = entry
                logger.info(f"Selected experiment {experiment['id']}.")
                break

    if not experiment:
        logger.exit(
            f"Cannot find experiment with matching id {experiment_id}, choices are {choices}"
        )
    return experiment
