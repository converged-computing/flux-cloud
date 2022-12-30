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

single_experiment_properties = {
    "machine": {"type": "string"},
    "size": {"type": "integer"},
}

cloud_properties = {"zone": {"type": "string"}, "machine": {"type": "string"}}
google_cloud_properties = copy.deepcopy(cloud_properties)
google_cloud_properties["project"] = {"type": "string"}

kubernetes_properties = {"version": {"type": "string"}}
kubernetes_cluster_properties = {
    "tags": {"type": "array", "items": {"type": "string"}},
}

minicluster_properties = {
    "name": {"type": "string"},
    "namespace": {"type": "string"},
}


# Currently all of these are required
settings_properties = {
    "default_cloud": {"type": "string"},
    "config_editor": {"type": "string"},
    "google": {
        "type": "object",
        "properties": google_cloud_properties,
        "additionalProperties": False,
        "required": ["zone", "machine", "project"],
    },
    "kubernetes": {
        "type": "object",
        "properties": kubernetes_properties,
        "additionalProperties": False,
        "required": ["version"],
    },
    "clouds": {
        "type": "array",
        "items": {"type": "string", "enum": clouds.cloud_names},
    },
}


variables = copy.deepcopy(keyvals)
variables["required"] = ["commands", "ids"]

experiment_schema = {
    "$schema": schema_url,
    "title": "Experiment Schema",
    "type": "object",
    "properties": {
        "commands": keyvals,
        "variables": keyvals,
        "experiment": {
            "type": "object",
            "properties": single_experiment_properties,
            "additionalProperties": False,
            "required": ["machine", "size"],
        },
        "minicluster": {
            "type": "object",
            "properties": minicluster_properties,
            "additionalProperties": False,
        },
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
        "clouds",
        "google",
        "kubernetes",
    ],
    "properties": settings_properties,
    "additionalProperties": False,
}
