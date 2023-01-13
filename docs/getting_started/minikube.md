# MiniKube

> Running on a local MiniKube cluster

Flux Cloud (as of version 0.1.0) can run on MiniKube! The main steps of running experiments are:

 - **up** to bring up a cluster
 - **apply** to apply one or more experiments defined by an experiments.yaml
 - **down** to destroy a cluster

Each of these commands can be run in isolation, and we provide a single command **run** to
automate the entire thing. We emphasize the term "wrapper" as we are using scripts on your
machine to do the work (e.g., minikube and kubectl) and importantly, for every step we show
you the command, and if it fails, give you a chance to bail out. We do this so if you
want to remove the abstraction at any point and run the commands on your own, you can.

## Pre-requisites

You should first [install minikube](https://minikube.sigs.k8s.io/docs/start/)
and kubectl.


## Run Experiments

Each experiment is defined by the matrix and variables in an `experiment.yaml` that is used to
populate a `minicluster-template.yaml` that you can either provide, or use a template provided by the
library. One of the goals of the Flux Cloud Experiment runner is not just to run things, but to
provide this library for you to easily edit and use! Take a look at the [examples](https://github.com/converged-computing/flux-cloud/tree/main/examples)
directory for a few that we provide. We will walk through a generic one here to launch
an experiment on a MiniKube Kubernetes cluster. Note that before doing this step you should
have installed flux-cloud, along with kubectl and minikube. Note that if it's not the default,
you'll need to specify using MiniKube:

```bash
$ flux-cloud run --cloud minikube experiments.yaml
```

Or set to the default:

```bash
$ flux-cloud config set default_cloud:minikube
```

Given MiniKube is the default, since the experiments file defaults to that name, you can also just do:

```bash
$ flux-cloud run
```

Given an experiments.yaml in the present working directory. Take a look at an `experients.yaml` in an example directory.
Note that only size is required for the matrix for MiniKube (there is currently no concept of a machine,
although there could be), and variables get piped into all experiments (in full). Under variables,
both "commands" and "ids" are required, and must be equal in length (each command is assigned to one id
for output). To just run the first entry in the matrix (test mode) do:

```bash
$ flux-cloud run experiments.yaml --test
```

Note that you can also use the other commands in place of a single run, notably "up" "apply" and "down."
By default, results will be written to a temporary output directory, but you can customize this with `--outdir`.
Finally, since MiniKube often has trouble pulling images, we recommend you include the container image as a variable
in the experiment.yaml so it can be pulled before the experiment is run. E.g., this experiment:

```yaml
matrix:
  size: [4]

# Flux Mini Cluster experiment attributes
minicluster:
  name: lammps
  namespace: flux-operator
  size: [2, 4]

# Each job can have a command and working directory
jobs:
  lmp:
    command: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
    repeats: 2
    image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
```

And this config file:

```yaml
apiVersion: flux-framework.org/v1alpha1
kind: MiniCluster
metadata:
  name: {{ minicluster.name }}
  namespace: {{ minicluster.namespace }}
spec:
  # localDeploy needs to be false
  localDeploy: false

  # Number of pods to create for MiniCluster
  size: {{ minicluster.size }}

  # Disable verbose output
  test: true

  # This is a list because a pod can support multiple containers
  containers:
    # The container URI to pull (currently needs to be public)
    - image: {{ job.image }}

      # You can set the working directory if your container WORKDIR is not correct.
      workingDir: /home/flux/examples/reaxff/HNS
      command: {{ job.command }}
```
