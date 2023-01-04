# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import itertools
import os

import jinja2
import jsonschema

import fluxcloud.defaults as defaults
import fluxcloud.main.settings as settings
import fluxcloud.utils as utils
from fluxcloud.logger import logger


class ExperimentSetup:
    def __init__(
        self,
        experiments,
        template=None,
        outdir=None,
        validate=True,
        test=False,
        quiet=False,
        **kwargs,
    ):
        """
        An experiment setup.
        """
        self.experiment_file = os.path.abspath(experiments)
        self.template = os.path.abspath(template) if template is not None else None
        self._outdir = outdir
        self.test = test
        self.settings = settings.Settings
        self.quiet = quiet

        # Show the user the template file
        if template:
            logger.debug(f"Using template {self.template}")

        # Rewrite existing outputs
        self.force = kwargs.get("force") or False
        # Don't ask for confirmation to create/destroy
        self.force_cluster = kwargs.get("force_cluster") or False

        if validate:
            self.validate()
        # Prepare the matrices for the setup
        self.prepare_matrices()

    def prepare_matrices(self):
        """
        Given an experiments.yaml, prepare matrices to run.
        """
        self.spec = utils.read_yaml(self.experiment_file)
        validate_experiments(self.spec)

        # Sploot out into matrices
        matrices = expand_experiments(self.spec)
        if not matrices:
            raise ValueError(
                "No matrices generated. Did you include any empty variables in your matrix?"
            )

        # Test mode means just one run
        if self.test:
            matrices = [matrices[0]]
        if not self.quiet:
            logger.info(f"🧪 Prepared {len(matrices)} experiment matrices")
        self.matrices = matrices

    def get_single_experiment(self):
        """
        Given a set of experiments, get a single one.
        """
        if "matrix" in self.spec:
            logger.warning("Matrix found - will use first entry.")
        return self.matrices[0]

    def generate_crd(self, experiment, job):
        """
        Given an experiment, generate the custom resource definition for it.
        """
        template = jinja2.Template(utils.read_file(self.template))
        experiment = copy.deepcopy(experiment)

        # If the experiment doesn't define a minicluster, add our default
        if "minicluster" not in experiment:
            experiment["minicluster"] = self.settings.minicluster
        if "jobs" in experiment:
            del experiment["jobs"]
        experiment["job"] = job
        result = template.render(**experiment)
        logger.debug(result)
        return result

    @property
    def outdir(self):
        """
        Handle creation of the output directory if it doesn't exist.
        """
        if self._outdir and os.path.exists(self._outdir):
            return self._outdir

        self._outdir = self._outdir or utils.get_tmpdir()
        if not os.path.exists(self._outdir):
            logger.info(f"💾 Creating output directory {self._outdir}")
            utils.mkdir_p(self._outdir)
        return self._outdir

    # Shared "getter" functions to be used across actions
    def get_size(self, experiment):
        return str(experiment.get("size") or self.settings.google["size"])

    def get_minicluster(self, experiment):
        """
        Get mini cluster definition, first from experiment and fall back to settings.
        """
        minicluster = experiment.get("minicluster") or self.settings.minicluster
        if "namespace" not in minicluster or not minicluster["namespace"]:
            minicluster["namespace"] = defaults.default_namespace
        return minicluster

    def get_machine(self, experiment):
        return experiment.get("machine") or self.settings.google["machine"]

    def get_tags(self, experiment):
        return experiment.get("cluster", {}).get("tags")

    def get_cluster_name(self, experiment):
        return (
            experiment.get("cluster", {}).get("name") or defaults.default_cluster_name
        )

    def validate(self):
        """
        Validate that all paths exist (create output if it does not)
        """
        if self.template is not None and not os.path.exists(self.template):
            raise ValueError(f"Template file {self.template} does not exist.")

        # This file must always be provided and exist
        if not os.path.exists(self.experiment_file):
            raise ValueError(f"Experiments file {self.experiment_file} does not exist.")


def expand_experiments(experiments):
    """
    Given a valid experiments.yaml, expand out into experiments
    """
    # We should only have one of these keys
    count = 0
    for key in ["experiment", "experiments", "matrix"]:
        if key in experiments:
            count += 1

    if count > 1:
        raise ValueError(
            "You can either define a matrix OR experiment OR experiments, but not more than one."
        )

    if "matrix" in experiments:
        matrix = expand_experiment_matrix(experiments)
    elif "experiment" in experiments:
        matrix = expand_single_experiment(experiments)
    elif "experiments" in experiments:
        matrix = expand_experiment_list(experiments)
    else:
        raise ValueError(
            'The key "experiment" or "experiments" or "matrix" is required.'
        )
    # Add ids to all entries
    matrix = add_experiment_ids(matrix)
    return matrix


def add_experiment_ids(matrix):
    """
    Add experiment identifiers based on machine and size.
    """
    for entry in matrix:
        entry["id"] = f"{entry['machine']}-{entry['size']}"
    return matrix


def expand_jobs(jobs):
    """
    Expand out jobs based on repeats
    """
    final = {}
    for jobname, job in jobs.items():
        if "repeats" in job:
            repeats = job["repeats"]
            if repeats < 1:
                raise ValueError(
                    f'"repeats" must be a positive number greater than 0. Found {repeats} for {job["command"]}'
                )

            # Start at 1 and not 0
            for i in range(1, repeats + 1):
                final[f"{jobname}-{i}"] = job
        else:
            final[jobname] = job
    return final


def expand_experiment_list(experiments):
    """
    Given a list of experiments, expand out jobs
    """
    listing = experiments["experiments"]
    for entry in listing:
        for key in experiments:
            if key == "experiments":
                continue
            if key == "jobs":
                entry[key] = expand_jobs(experiments[key])
                continue
            entry[key] = experiments[key]
    return listing


def expand_single_experiment(experiments):
    """
    Expand a single experiment, ensuring to add the rest of the config.
    """
    experiment = experiments["experiment"]
    for key in experiments:
        if key == "experiment":
            continue
        if key == "jobs":
            experiment[key] = expand_jobs(experiments[key])
            continue
        experiment[key] = experiments[key]
    return [experiment]


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
            if key == "jobs":
                experiment[key] = expand_jobs(experiments[key])
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
