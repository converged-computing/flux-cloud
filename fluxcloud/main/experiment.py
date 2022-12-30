# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import itertools

import jsonschema


def expand_experiments(experiments):
    """
    Given a valid experiments.yaml, expand out into experiments
    """
    if "matrix" in experiments and "experiment" in experiments:
        raise ValueError("You can either define a matrix OR experiment, but not both.")

    if "matrix" in experiments:
        matrix = expand_experiment_matrix(experiments)
    elif "experiment" in experiments:
        matrix = [experiments["experiment"]]
    else:
        raise ValueError('The key "experiment" or "matrix" is required.')
    return matrix


def expand_experiment_matrix(experiments):
    """
    Given a valid experiments.yaml, expand out into matrix
    """
    matrix = []
    keys, values = zip(*experiments["matrix"].items())
    for bundle in itertools.product(*values):
        experiment = dict(zip(keys, bundle))
        # Add variables, and others
        for key in experiments:
            if key == "matrix":
                continue
            # This is an ordered dict
            experiment[key] = experiments[key]
        matrix.append(experiment)
    return matrix


def validate_experiments(experiments):
    """
    Ensure jsonschema validates, and no overlapping keys.
    """
    import fluxcloud.main.schemas as schemas

    if jsonschema.validate(experiments, schema=schemas.experiment_schema) is not None:
        raise ValueError("Invalid experiments schema.")


def run_experiment(experiment, outdir, args):
    """
    Given one or more experiments, run them.
    """
    print("RUN EXPERIMENT")
    # First bring up the cluster
    import IPython

    IPython.embed()
    # TODO vsoch, this should be a shared function

    # template = Template(read_file(template_file))

    # Run this many commands
    # for command in experiment["commands"]:
    #    experiment["command"] = command
    #    render = template.render(**experiment)
