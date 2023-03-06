# AWS

> Running on Amazon Elastic Kubernetes Service EKS
Flux Cloud (as of version 0.1.0) can run on MiniKube! There are two primary use cases for using flux-cloud:

 - **apply** is good for many larger experiments that require different container bases and / or take a longer time to run.
 - **submit** is good for smaller experiments that might use the same container bases and / or take a shorter time to run.

For the latter (submit) we will bring up the minimum number of MiniClusters required (unique based on container image size)
and launch all jobs across them, using Flux as a scheduler. As of version 0.2.0 both commands both use the fluxoperator Python
SDK, so we only use bash scripts to bring up and down cloud-specific clusters.

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

## Run Experiments

**IMPORTANT** for any experiment when you choose an instance type, you absolutely
need to choose a size that has [IsTrunkingCompatible](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/pkg/aws/vpc/limits.go)
true. E.g., `m5.large` has it set to true so it would work. Each experiment is defined by the matrix and variables in an `experiment.yaml`. It's recommended you
start with a template populated for aws:

```bash
$ flux-cloud experiment init --cloud aws
```

And see the [custom variables](#custom-variables) defined below to learn more about them,
or the [examples](https://github.com/converged-computing/flux-cloud/tree/main/examples)
directory for a few examples that we provide. We will walk through a generic one here to launch
an experiment on a Kubernetes cluster. Note that before doing this step you should
have installed flux-cloud, along with ekctl, and set your defaults (e.g., project zone)
in your settings.

Given an experiments.yaml in the present working directory, you can do an apply,
meaning creating a separate MiniCluster per job:

```bash
# Up / apply / down
$ flux-cloud run --cloud aws

# Manual up / apply / down (recommended)
$ flux-cloud up --cloud aws
$ flux-cloud apply --cloud aws
$ flux-cloud down --cloud aws
```

Or submit, creating shared MiniClusters to submit multiple jobs to:

```bash
# Up / submit / down
$ flux-cloud batch --cloud aws

# Manual up / submit / down (recommended)
$ flux-cloud up --cloud aws
$ flux-cloud submit --cloud aws
$ flux-cloud down --cloud aws
```

Note that machines and size are required for the matrix.


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

    # Customize region just for this experiment
    region: us-east-2

    # Customize availability zones for this experiment
    availability_zones: [us-east-1a, us-east-1b]

    # Important for instance types only in one zone (hpc instances)
    # Select your node group availability zone:
    node_group_availability_zone: us-east-2b
```

Note that we currently take a simple approach for boolean values - if it's present (e.g., the examples)
above) it will be rendered as true. Don't put False in there, but rather just delete the key.
