# AWS

> Running on Amazon Elastic Kubernetes Service EKS

The flux-cloud software provides are easy wrappers (and templates) to running
the Flux Operator on Amazon. The main steps of running experiments are:

 - **up** to bring up a cluster
 - **apply** to apply one or more experiments defined by an experiments.yaml
 - **down** to destroy a cluster

Each of these commands can be run in isolation, and we provide a single command **run** to
automate the entire thing. We emphasize the term "wrapper" as we are using scripts on your
machine to do the work (e.g., kubectl and gcloud) and importantly, for every step we show
you the command, and if it fails, give you a chance to bail out. We do this so if you
want to remove the abstraction at any point and run the commands on your own, you can.

## Pre-requisites

You should first [install eksctrl](https://github.com/weaveworks/eksctl) and make sure you have access to an AWS cloud (e.g.,
with credentials or similar in your environment). E.g.,:

```bash
export AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxx
export AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export AWS_SESSION_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The last session token may not be required depending on your setup.
We assume you also have [kubectl](https://kubernetes.io/docs/tasks/tools/).

### Setup SSH

You'll need an ssh key for EKS. Here is how to generate it:

```bash
ssh-keygen
# Ensure you enter the path to ~/.ssh/id_eks
```

This is used so you can ssh (connect) to your workers!

### Cloud

Finally, ensure that aws is either your default cloud (the `default_cloud` in your settings.yml)
or you specify it with `--cloud` when you do run.

## Custom Variables

The following custom variables are supported in the "variables" section (key value pairs)
for Amazon in an `experiments.yaml`

```yaml
variables:
    # Enable private networking
    private_networking: true

    # Enable efa (requires efa also set under the container limits)
    efa_enabled: true

    # Add a custom placement group name to your workers managed node group
    placement_group: eks-efa-testing
```

Note that we currently take a simple approach for boolean values - if it's present (e.g., the examples)
above) it will be rendered as true. Don't put False in there, but rather just delete the key.

## Run Experiments

**IMPORTANT** for any experiment when you choose an instance type, you absolutely
need to choose a size that has [IsTrunkingCompatible](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/pkg/aws/vpc/limits.go)
true. E.g., `m5.large` has it set to true so it would work.

Each experiment is defined by the matrix and variables in an `experiment.yaml` that is used to
populate a `minicluster-template.yaml` that you can either provide, or use a template provided by the
library. One of the goals of the Flux Cloud Experiment runner is not just to run things, but to
provide this library for you to easily edit and use! Take a look at the [examples](https://github.com/converged-computing/flux-cloud/tree/main/examples)
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

Note that you can also use the other commands in place of a single run, notably "up" "apply" and "down."
By default, results will be written to a temporary output directory, but you can customize this with `--outdir`.
