# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import itertools
import os
import shutil

import jinja2
import jsonschema

import fluxcloud.defaults as defaults
import fluxcloud.main.settings as settings
import fluxcloud.utils as utils
from fluxcloud.logger import logger
from fluxcloud.main.clouds.templates import Script


class ExperimentSetup:
    def __init__(
        self,
        experiments,
        template=None,
        outdir=None,
        validate=True,
        cleanup=True,
        test=False,
        quiet=False,
        **kwargs,
    ):
        """
        An experiment setup is a light wrapper around a group of experiments.
        """
        self.experiment_file = os.path.abspath(experiments)
        self.template = (
            os.path.abspath(template)
            if template is not None and os.path.exists(template)
            else None
        )
        self.outdir = outdir
        self.test = test
        self.settings = settings.Settings
        self.quiet = quiet
        self.run_cleanup = cleanup

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

    def iter_experiments(self):
        """
        yield experiments that are not run yet.
        """
        for experiment in self.matrices:
            # Don't bring up a cluster if experiments already run!
            if not self.force and experiment.is_run():
                logger.info(
                    f"Experiment on machine {experiment.expid} was already run and force is False, skipping."
                )
                continue
            yield experiment

    def cleanup(self, experiments):
        """
        Cleanup the experiment script directory, if cleanup is true
        """
        if not isinstance(experiments, list):
            experiments = [experiments]
        if not self.run_cleanup:
            return

        for experiment in experiments:
            experiment.cleanup()

    def set_minicluster_size(self, size):
        """
        Set the minicluster size across experiments.
        """
        for experiment in self.matrices:
            experiment.set_minicluster_size(size)

    def prepare_matrices(self):
        """
        Given an experiments.yaml, prepare matrices to run.
        """
        self.spec = utils.read_yaml(self.experiment_file)
        validate_experiments(self.spec)

        # Sploot out into matrices
        matrices = expand_experiments(self.spec, self.outdir, self.template)
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

    def validate(self):
        """
        Validate that all paths exist (create output if it does not)
        """
        # This file must always be provided and exist
        if not os.path.exists(self.experiment_file):
            raise ValueError(f"Experiments file {self.experiment_file} does not exist.")


class Experiment:
    """
    An experiment wrapper to make it easy to get variables in templates.
    """

    def __init__(self, experiment, outdir=None, template=None):
        self.experiment = experiment
        self.settings = settings.Settings
        self._outdir = outdir
        self.template = template or defaults.default_minicluster_template

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

    @property
    def variables(self):
        return self.experiment.get("variables", {})

    @property
    def root_dir(self):
        """
        Consistent means to get experiment, also namespaced to cloud/runner.
        """
        return os.path.join(self.outdir, self.expid)

    def iter_jobs(self):
        """
        Iterate through experiment jobs
        """
        minicluster = self.minicluster

        # Iterate through all the cluster sizes
        for size in minicluster["size"]:

            # We can't run if the minicluster > the experiment size
            if size > self.size:
                logger.warning(
                    f"Cluster of size {self.size} cannot handle a MiniCluster of size {size}, skipping."
                )
                continue

            # Jobname is used for output
            for jobname, job in self.jobs.items():

                # Do we want to run this job for this size and machine?
                if not self.check_job_run(job, size):
                    logger.debug(
                        f"Skipping job {jobname} as does not match inclusion criteria."
                    )
                    continue

                yield size, jobname, job

    def get_persistent_variables(self, size, required=None):
        """
        Get persistent variables that should be used across the MiniCluster
        """
        jobvars = {}
        for _, job in self.jobs.items():

            # Skip jobs targeted for a different size
            if "size" in job and job["size"] != size:
                continue

            for key, value in job.items():
                if key not in jobvars or (key in jobvars and jobvars[key] == value):
                    jobvars[key] = value
                    continue
                logger.warning(
                    f'Inconsistent job variable between MiniCluster jobs: {value} vs. {jobvars["value"]}'
                )

        # If we get here and we don't have an image
        for req in required or []:
            if req not in jobvars:
                raise ValueError(
                    f'Submit requires a "{req}" field under at least one job spec to create the MiniCluster.'
                )
        return jobvars

    @property
    def script_dir(self):
        """
        Save scripts to script directory for reproducing (if desired)
        """
        return os.path.join(self.root_dir, ".scripts")

    def get_script(self, name, cloud, render_kwargs=None, ext="sh", suffix=""):
        """
        Get a named script from the cloud's script folder
        """
        ext = ext.strip(".")
        render_kwargs = render_kwargs or {}
        script = Script(cloud, name)
        outfile = os.path.join(self.script_dir, f"{name}{suffix}.{ext}")
        outdir = os.path.dirname(outfile)
        if not os.path.exists(outdir):
            logger.info(f"Creating output directory {outdir} for scripts.")
            utils.mkdir_p(outdir)
        return script.render(outfile=outfile, **render_kwargs)

    def get_shared_script(self, name, render_kwargs=None, suffix="", ext="sh"):
        """
        Get a named shared script
        """
        render_kwargs = render_kwargs or {}
        return self.get_script(
            name, cloud="shared", render_kwargs=render_kwargs, suffix=suffix, ext=ext
        )

    def cleanup(self):
        """
        Cleanup the scripts directory for the experiment!
        """
        if os.path.exists(self.script_dir):
            logger.debug(f"Cleaning up {self.script_dir}")
            shutil.rmtree(self.script_dir)

    def generate_crd(self, job, minicluster_size):
        """
        Generate a custom resource definition for the experiment
        """
        template = jinja2.Template(utils.read_file(self.template))
        experiment = copy.deepcopy(self.experiment)

        # If the experiment doesn't define a minicluster, add our default
        if "minicluster" not in experiment:
            experiment["minicluster"] = self.settings.minicluster

        # Update minicluster size to the one we want
        experiment["minicluster"]["size"] = minicluster_size

        if "jobs" in experiment:
            del experiment["jobs"]
        experiment["job"] = job
        result = template.render(**experiment).strip(" ")
        logger.debug(result)

        # Write to output directory
        outfile = os.path.join(
            self.script_dir, f"minicluster-size-{minicluster_size}.yaml"
        )
        outdir = os.path.dirname(outfile)
        if not os.path.exists(outdir):
            logger.info(f"Creating output directory for scripts {outdir}")
            utils.mkdir_p(outdir)
        return utils.write_file(result, outfile)

    @property
    def jobs(self):
        return self.experiment.get("jobs", {})

    def is_run(self):
        """
        Determine if all jobs are already run in an experiment
        """
        if not self.jobs:
            logger.warning(f"Experiment {self.expid} has no jobs, nothing to run.")
            return True

        # If all job output files exist, experiment is considered run
        for size in self.minicluster["size"]:

            # We can't run if the minicluster > the experiment size
            if size > self.size:
                logger.warning(
                    f"Cluster of size {self.size} cannot handle a MiniCluster of size {size}, not considering."
                )
                continue

            # Jobname is used for output
            for jobname, job in self.jobs.items():

                # Do we want to run this job for this size and machine?
                if not self.check_job_run(job, size):
                    logger.debug(
                        f"Skipping job {jobname} as does not match inclusion criteria."
                    )
                    continue

                # Add the size
                jobname = f"{jobname}-minicluster-size-{size}"
                job_output = os.path.join(self.root_dir, jobname)
                logfile = os.path.join(job_output, "log.out")

                # Do we have output?
                if not os.path.exists(logfile):
                    return False
        return True

    def check_job_run(self, job, size):
        """
        Determine if a job is marked for a MiniCluster size.
        """
        if "sizes" in job and size not in job["sizes"]:
            return False
        if "size" in job and job["size"] != size:
            return False
        if "machine" in job and self.machine and job["machine"] != self.machine:
            return False
        if "machines" in job and self.machine and self.machine not in job["machines"]:
            return False
        return True

    def save_metadata(self, times, info=None):
        """
        Save experiment metadata, loading an existing meta.json, if present.
        """
        experiment_dir = self.root_dir
        info = info or {}

        # The experiment is defined by the machine type and size
        if not os.path.exists(experiment_dir):
            utils.mkdir_p(experiment_dir)
        meta_file = os.path.join(experiment_dir, "meta.json")

        # Load existing metadata, if we have it
        meta = {"times": times, "info": info}
        if os.path.exists(meta_file):
            meta = utils.read_json(meta_file)

            # Don't update cluster-up/down if already here
            frozen_keys = ["create-cluster", "destroy-cluster"]
            for timekey, timevalue in times.items():
                if timekey in meta and timekey in frozen_keys:
                    continue
                meta["times"][timekey] = timevalue

            # Update info
            if "info" not in meta and info:
                meta["info"] = {}
            for key, value in info.items():
                meta["info"][key] = value

        # TODO we could add cost estimation here - data from cloud select
        for key, value in self.experiment.items():
            meta[key] = value

        # Do not add empty info (only for batch mode)
        if "info" in meta and not meta["info"]:
            del meta["info"]

        utils.write_json(meta, meta_file)
        return meta

    def set_minicluster_size(self, size):
        """
        Set the minicluster size for an experiment.
        """
        if size not in self.minicluster["size"]:
            logger.exit(
                f"Size {size} is not a known MiniCluster size for this experiment."
            )

        logger.debug(f"MiniCluster size {size} selected to run for {self.expid}")
        self.minicluster["size"] = [size]

    # Shared "getter" functions to be used across actions
    @property
    def size(self):
        return self.experiment.get("size") or self.settings.google["size"]

    @property
    def operator_branch(self):
        return (
            self.experiment.get("operator", {}).get("branch")
            or self.settings.operator["branch"]
            or "main"
        )

    @property
    def operator_repository(self):
        return (
            self.experiment.get("operator", {}).get("repository")
            or self.settings.operator["repository"]
            or "flux-framework/flux-operator"
        )

    @property
    def minicluster(self):
        """
        Get mini cluster definition, first from experiment and fall back to settings.
        """
        minicluster = self.experiment.get("minicluster") or self.settings.minicluster
        if "namespace" not in minicluster or not minicluster["namespace"]:
            minicluster["namespace"] = defaults.default_namespace
        return minicluster

    @property
    def machine(self):
        return self.experiment.get("machine") or self.settings.google["machine"]

    @property
    def tags(self):
        return self.experiment.get("kubernetes", {}).get("tags")

    @property
    def expid(self):
        """
        Return the experiment id
        """
        if "machine" not in self.experiment:
            return f"k8s-size-{self.experiment['size']}-local"
        return f"k8s-size-{self.experiment['size']}-{self.experiment['machine']}"

    @property
    def cluster_name(self):
        return (
            self.experiment.get("kubernetes", {}).get("name")
            or defaults.default_cluster_name
        )

    @property
    def kubernetes_version(self):
        return (
            self.experiment.get("kubernetes", {}).get("version")
            or self.settings.kubernetes["version"]
        )


def expand_experiments(experiments, outdir, template=None):
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

    # Put in final matrix form
    final = []
    for entry in matrix:
        final.append(Experiment(entry, outdir, template))
    return final


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
