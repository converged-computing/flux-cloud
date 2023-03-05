# Google Cloud

> Running on Google Kubernetes Engine, GKE

The main functionality that flux-cloud provides are easy wrappers (and templates) to running
the Flux Operator on GKE. The main steps of running experiments are:

 - **up** to bring up a cluster
 - **apply/submit** to apply or submit one or more experiments defined by an experiments.yaml
 - **down** to destroy a cluster

Each of these commands can be run in isolation, and we provide single commands **run/batch** to
automate the entire thing. For Google Cloud, you can see a small collection of [examples here](https://github.com/converged-computing/flux-cloud/tree/main/examples/google).

## Pre-requisites

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

## Cloud

Finally, ensure that google is either your default cloud (the `default_cloud` in your settings.yml)
or you specify it with `--cloud` when you do run.

## Custom Variables

The following custom variables are supported in the "variables" section (key value pairs)
for Google in an `experiments.yaml`

```yaml
variables:
    # Customize zone just for this experiment
    zone: us-central1-a
```


## Run Experiments

You can create an empty experiment template as follows:

```bash
$ flux-cloud experiment init --cloud google
```

Each experiment is defined by the matrix and variables in an `experiment.yaml`
One of the goals of the Flux Cloud Experiment runner is not just to run things, but to
provide this library for you to easily edit and use! Take a look at the [examples](https://github.com/converged-computing/flux-cloud/tree/main/examples)
directory for a few that we provide. We will walk through a generic one here to launch
an experiment on a Kubernetes cluster. Note that before doing this step you should
have installed flux-cloud, along with gcloud, and set your defaults (e.g., project zone)
in your settings.

Given an experiments.yaml in the present working directory, you can do an apply,
meaning creating a separate MiniCluster per job:

```bash
# Up / apply / down
$ flux-cloud run --cloud google

# Manual up / apply / down (recommended)
$ flux-cloud --debug up --cloud google
$ flux-cloud --debug apply --cloud google
$ flux-cloud --debug down --cloud google
```

For any of the commands here, add `--debug` after `flux-cloud` to see more verbosity.
Or submit, creating shared MiniClusters to submit multiple jobs to:

```bash
# Up / submit / down
$ flux-cloud batch --cloud google

# Manual up / submit / down (recommended)
$ flux-cloud --debug up --cloud google
$ flux-cloud --debug submit --cloud google
$ flux-cloud --debug down --cloud google
```

Note that machines and size are required for the matrix. See our [debugging guide](../getting-started/debugging.md)
for the Flux Operator for interacting with Flux Operator containers or debugging.
