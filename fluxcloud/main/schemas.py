# Copyright 2022 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

import copy

import fluxcloud.main.clouds as clouds

schema_url = "http://json-schema.org/draft-07/schema"

# This is also for latest, and a list of tags

# The simplest form of aliases is key/value pairs
keyvals = {
    "type": "object",
    "patternProperties": {
        "\\w[\\w-]*": {"type": "string"},
    },
}

job_spec = {
    "type": "object",
    "properties": {
        "command": {"type": "string"},
        "repeats": {"type": "number"},
        "workdir": {"type": "string"},
        "image": {"type": "string"},
    },
    "required": ["command"],
}

jobs_properties = {
    "type": "object",
    "patternProperties": {
        "\\w[\\w-]*": job_spec,
    },
}


single_experiment_properties = {
    "machine": {"type": "string"},
    "size": {"type": "integer"},
}

cloud_properties = {"zone": {"type": "string"}, "machine": {"type": "string"}}
google_cloud_properties = copy.deepcopy(cloud_properties)
google_cloud_properties["project"] = {"type": ["null", "string"]}
aws_cloud_properties = {
    "region": {"type": "string"},
    "machine": {"type": "string"},
    "private_networking": {"type": ["null", "boolean"]},
    "efa_enabled": {"type": ["null", "boolean"]},
    "ssh_key": {"type": ["string", "null"]},
}

kubernetes_properties = {"version": {"type": "string"}}
kubernetes_cluster_properties = {
    "tags": {
        "type": "array",
        "items": {"type": "string"},
        "version": {"type": "string"},
    },
}

minicluster_properties = {
    "name": {"type": "string"},
    "namespace": {"type": "string"},
}
minicluster = {
    "type": "object",
    "properties": minicluster_properties,
    "additionalProperties": False,
    "required": ["name", "namespace"],
}


operator_properties = {
    "repository": {"type": "string"},
    "branch": {"type": "string"},
}

# Currently all of these are required
settings_properties = {
    "default_cloud": {"type": "string"},
    "config_editor": {"type": "string"},
    "aws": {
        "type": "object",
        "properties": aws_cloud_properties,
        "additionalProperties": False,
        "required": ["region", "machine"],
    },
    "google": {
        "type": "object",
        "properties": google_cloud_properties,
        "additionalProperties": False,
        "required": ["zone", "machine", "project"],
    },
    "minicluster": minicluster,
    "kubernetes": {
        "type": "object",
        "properties": kubernetes_properties,
        "additionalProperties": False,
        "required": ["version"],
    },
    "operator": {
        "type": "object",
        "properties": operator_properties,
        "additionalProperties": False,
        "required": ["repository", "branch"],
    },
    "clouds": {
        "type": "array",
        "items": {"type": "string", "enum": clouds.cloud_names},
    },
}

single_experiment = {
    "type": "object",
    "properties": single_experiment_properties,
    "additionalProperties": False,
    "required": ["machine", "size"],
}

experiment_schema = {
    "$schema": schema_url,
    "title": "Experiment Schema",
    "type": "object",
    "properties": {
        "jobs": jobs_properties,
        "variables": keyvals,
        "experiments": {
            "type": "array",
            "items": single_experiment,
        },
        "experiment": single_experiment,
        "minicluster": minicluster,
        "cluster": {
            "type": "object",
            "properties": kubernetes_cluster_properties,
            "additionalProperties": False,
        },
        "matrix": {
            "type": "object",
            "patternProperties": {
                "\\w[\\w-]*": {
                    "type": "array",
                    "items": {"type": ["number", "boolean", "string"]},
                }
            },
            "required": ["machine", "size"],
        },
    },
    "additionalProperties": False,
}


settings = {
    "$schema": schema_url,
    "title": "Settings Schema",
    "type": "object",
    "required": [
        "minicluster",
        "operator",
        "clouds",
        "aws",
        "google",
        "kubernetes",
    ],
    "properties": settings_properties,
    "additionalProperties": False,
}
