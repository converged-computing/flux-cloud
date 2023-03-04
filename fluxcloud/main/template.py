# Copyright 2023 Lawrence Livermore National Security, LLC and other
# This is part of Flux Framework. See the COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0

experiment_base = """
# Flux MiniCluster experiment attributes
minicluster:
  name: my-job
  namespace: flux-operator
  # Each of these sizes will be brought up and have commands run across it
  # They must be smaller than the Kubernetes cluster size or not possible to run!
  size: [2, 4]

# Under jobs should be named jobs (output orgainzed by name) where
# each is required to have a command and image. Repeats is the number
# of times to run each job
jobs:
  reaxc-hns:
    command: 'lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite'
    image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
    repeats: 5
    working_dir: /home/flux/examples/reaxff/HNS
  sleep:
    command: 'sleep 5'
    image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
    repeats: 5
    working_dir: /home/flux/examples/reaxff/HNS
  hello-world:
    command: 'echo hello world'
    image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
    repeats: 5
    working_dir: /home/flux/examples/reaxff/HNS
"""

google_experiment_template = f"""
matrix:
  size: [4]

  # This is a Google Cloud machine
  machine: [n1-standard-1]

variables:
    # Customize zone just for this experiment
    # otherwise defaults to your settings.yml
    zone: us-central1-a

{experiment_base}
"""

minikube_experiment_template = f"""
# This is intended for MiniKube, so no machine needed
matrix:

  # This is the size of the MiniKube cluster (aka Kubernetes cluster) to bring up
  size: [4]

{experiment_base}
"""

aws_experiment_template = f"""
matrix:

  # This is the size of the MiniKube cluster (aka Kubernetes cluster) to bring up
  size: [4]

  # This is an EC2 machine
  machine: [m5.large]

variables:
    # Enable private networking
    private_networking: false

    # Enable efa (requires efa also set under the container limits)
    efa_enabled: false

    # Add a custom placement group name to your workers managed node group
    placement_group: eks-efa-testing

    # Customize region just for this experiment
    region: us-east-2

    # Customize availability zones for this experiment
    availability_zones: [us-east-1a, us-east-1b]

    # Important for instance types only in one zone (hpc instances)
    # Select your node group availability zone:
    node_group_availability_zone: us-east-2b

{experiment_base}
"""
