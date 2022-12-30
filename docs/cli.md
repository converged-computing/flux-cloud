# flux-cloud

This is early notes / documentation for the flux-cloud client.

## Setup

Note that if you first want to create user-level settings, do:

```bash
$ flux-cloud inituser
```

You should then edit the defaults in your settings.yml, either via directly editing
the settings file, via the command line.

```bash
$ flux-cloud config get default_cloud
default_cloud                  google

$ flux-cloud config get google:project
google:project                 unset

$ flux-cloud config set google:project dinosaur
Updated google:project to be dinosaur

$ flux-cloud config get google:project
google:project                 dinosaur
```

Also set your editor of choice, and then you can edit in it (it defaults to vim)

```bash
$ flux-cloud config get config_editor
config_editor                  vim
```

```bash
$ flux-cloud config edit
```

## Google Cloud GKE

The main functionality that flux-cloud provides are easy wrappers (and templates) to running
the Flux Operator on GKE. We use "run" for that, and require a few scripts available on your
system to interact with Kubernetes.

### Pre-requisites

You should first [install gcloud](https://cloud.google.com/sdk/docs/quickstarts)
and ensure you are logged in and have kubectl installed:

```bash
$ gcloud auth login
```

Depending on your install, you can either install with gcloud:

```bash
$ gcloud components install kubectl
```
or just [on your own](https://kubernetes.io/docs/tasks/tools/).

### Run Experiments

Each experiment is defined by the matrix and variables in an `experiment.yaml` that is used to
populate a `minicluster-template.yaml` that you can either provide, or use a template provided by the
library. One of the goals of the Flux Cloud Experiment runner is not just to run things, but to
provide this library for you to easily edit and use! Take a look at the [examples](../examples)
directory for a few that we provide. We will walk through a generic one here to launch
an experiment on a Kubernetes cluster. Note that before doing this step you should
have installed flux-cloud, along with kubectl and gcloud, and set your defaults (e.g., project zone)
in your settings.

```bash
$ flux-cloud run experiments.yaml
```

Note that since the experiments file defaults to that name, you can also just do:

```bash
$ flux-cloud run
```

Given an experiments.yaml in the present working directory. Take a look at an `experients.yaml` in an example directory.
Note that machines and size are required for the matrix, and variables get piped into all experiments (in full). Under variables,
both "commands" and "ids" are required, and must be equal in length (each command is assigned to one id
for output). To just run the first entry in the matrix (test mode) do:

```bash
$ flux-cloud run experiments.yaml --test
```

By default, results will be written to a temporary output directory, but you can customize this with `--outdir`.

## Partial Commands

Instead of a "run" command that does the following:

1. Creates the cluster
2. Runs each of the experiments, saving output and timing
3. Brings down the cluster

If you want to have more control, you can run one step at a time,
each of "up" "apply" and "down."

### up

Here is how to bring up a cluster (with the operator installed).
