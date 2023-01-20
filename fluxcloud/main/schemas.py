# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
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
        "\\w[\\w-]*": {"type": ["string", "number", "integer", "array", "boolean"]},
    },
}

job_spec = {
    "type": "object",
    "properties": {
        "command": {"type": "string"},
        "repeats": {"type": "number"},
        "workdir": {"type": "string"},
        "image": {"type": "string"},
        "machine": {"type": "string"},
        "machines": {"type": "array", "items": {"type": "string"}},
        "size": {"type": "number"},
        "sizes": {"type": "array", "items": {"type": "number"}},
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

cloud_properties = {
    "zone": {"type": "string"},
    "machine": {"type": "string"},
    "variables": keyvals,
}

google_cloud_properties = copy.deepcopy(cloud_properties)
google_cloud_properties["project"] = {"type": ["null", "string"]}

# These are aws extra variables we want to control extra types for
aws_variables = {
    "private_networking": {"type": ["null", "boolean"]},
    "efa_enabled": {"type": ["null", "boolean"]},
    "ssh_key": {"type": ["string", "null"]},
    "availability_zones": {"type": "array", "items": {"type": "string"}},
}

aws_cloud_properties = copy.deepcopy(cloud_properties)
aws_cloud_properties.update(
    {
        "region": {"type": "string"},
        "machine": {"type": "string"},
        "variables": {
            "oneOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": aws_variables,
                },
            ]
        },
    }
)

kubernetes_properties = {"version": {"type": "string"}}
kubernetes_cluster_properties = {
    "tags": {
        "type": "array",
        "items": {"type": "string"},
    },
    "version": {"type": "string"},
}

minicluster_properties = {
    "name": {"type": "string"},
    "namespace": {"type": "string"},
    "size": {"items": {"type": "number"}, "type": "array"},
    "local_deploy": {"type": "boolean"},
    "verbose": {"type": "boolean"},
}
minicluster = {
    "type": "object",
    "properties": minicluster_properties,
    # Allow any extra args to be flexible to MiniCluster CRD
    "additionalProperties": True,
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
    "required": ["size"],
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
        "kubernetes": {
            "type": "object",
            "properties": kubernetes_cluster_properties,
            "additionalProperties": False,
        },
        "operator": {
            "type": "object",
            "properties": operator_properties,
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
            "required": ["size"],
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
