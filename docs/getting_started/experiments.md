# Experiments

Welcome to the Flux Cloud experiments user guide! If you come here, we are assuming you want
to run jobs with the Flux Operator on GKE, and that you have [installed](install.md) flux-cloud.
Note this project is early in development so this could change or bugs could be introduced.
Let's get started with talking about experiments. As of version 0.2.0, your experiments will be defined by one file:

 - experiments.yaml: a yaml file that describes sizes, machines, miniclusters, and jobs to run

We will walk through example experiment files here, along with a full set of fields you can use.
Note that to get an example experiments.yaml template for any cloud, you can always do:

```bash
$ flux-cloud experiment init --cloud minikube
$ flux-cloud experiment init --cloud aws
$ flux-cloud experiment init --cloud google
```

The documentation here outlines the sections in details, however the above is the best
means to get an entire, holistic file.

## Experiment Definition

> experiments.yaml

You can choose one of the following:

 - A matrix of experiments, with sizes for machines and MiniClusters
 - A single experiment (ideal for a demo or one-off run)
 - A list of experiments (when you want >1 but not a matrix)

### Matrix of Experiments

A matrix might look like this:

```yaml
matrix:
  size: [2, 4]
  machine: ["n1-standard-1", "n1-standard-2"]
```

Note that the sizes at this level indicate *the size of the Kubernetes cluster*. We
will expand on this idea later. This would run each size across each machine, for a total of 4 Kubernetes clusters created.
The number of custom resource (CRD) definitions applied to each one would vary based on the number of jobs.
The idea here is that we might want to run multiple jobs in the same container, and size, and machine.

#### Single Experiment

A single experiment is ideal for perhaps a demo. It's basically the above, but a single entry:

```yaml
experiment:
  size: 2
  machine: n1-standard-1
```

#### Experiment Listing

And finally, a listing! This is when you don't quite want a matrix, but you have more than one study
to run (e.g., multiple Kubernetes cluster setups.)

```yaml
experiments:
  - size: 2
    machine: n1-standard-1
```

Note that it's a yaml list.

### Custom Variables

Each cloud provider is allowed to specify any number of custom variables, and these
are available in the "variables" section. As an example, let's say we want to customize networking
arguments for aws:

```yaml
variables:
    private_networking: true
    efa_enabled: true
```

You can look at each cloud page here to see what variables are known.

### Operator Definition

If you want to override your branch or repository to install the operator from (in your settings)
you can set them in the experiment file as follows:

```yaml
operator:
  branch: my-feature-branch
  repository: my-user/flux-operator
```

Note that the file location to install from is consistent under `examples/dist/flux-operator.yaml`,
and this file is updated with `make build-config`.

### MiniCluster Definition

The minicluster is suggested to be defined, although it's not required (by default we will use the name and namespace in your settings).
As an example, here is setting a custom name and namespace:

```yaml
# Flux Mini Cluster experiment attributes
minicluster:
  name: osu-benchmarks
  namespace: flux-operator
```

If you want your MiniCluster to use the full size of your cluster, then you can use the above. However, in many cases we
might want to do the following

1. Bring up a cluster of size 32
2. For each of MiniCluster sizes `[2, 4, 8, 16, 32]` run an experiment.

For the above, we would only want to bring up the Kubernetes cluster once,
and then just vary the experiment size that we provide. To do this, we would
add the size variable to our MiniCluster:

```yaml
# Flux Mini Cluster experiment attributes
minicluster:
  name: osu-benchmarks
  namespace: flux-operator
  size: [2, 4, 8, 16, 32]
```

And in fact this is an expected practice for an experiment where you want to be making
comparisons across your MiniCluster sizes, as once you bring down a cluster it cannot
be compared to another cluster that you bring up.

### Kubernetes

While it's recommended to define defaults for Kubernetes (e.g., version) in your `settings.yml`, you can one-off edit them
via a "cluster" attribute in your `experiments.yaml`. Unlike settings, this supports a field for "tags" that should be a list of strings:

```yaml
cluster:
  version: "1.23"
  tags:
    - lammps
```

Note that the above is for a Google GKE cluster - tags is a single list of tags. For AWS EKS, you need to provide key value pairs:

```yaml
cluster:
  version: "1.22"
  tags:
    - analysis=lammps
```

This is validated at runtime when you create the cluster. For both, they are converted to comma separated values to provide
to the command line client.

### Jobs

The jobs specification defines what commands (required) you want run across each Kubernetes cluster.
For each command, we technically create its own MiniCluster, which means using the operator to bring
up the pods, run the command, and then clean up. Minimally, the jobs should be a set of key value
pairs, where the key is the job name (used for output) and the value is a dictionary of items,
where minimally "command" is required.

```yaml
# Each job can have a command and working directory
jobs:
  osu_get_latency:
    command: './osu_get_latency'
```

If you have different working directories or container images, you can define that here:
Note that each job can have a command (required) and working directory, image,
and repeats (optional).

```yaml
jobs:
  osu_get_latency:
    command: './osu_get_latency'
    image: ghcr.io/awesome/science:latest
    working_dir: /path/to/science
    repeats: 3
```

For repeats, we add another level to the output directory, and represent the result data as
subdirectories of the machine and size from 1..N.

#### Flux Options

How do job parameters map to Flux, in the case of using `flux-cloud submit`? Good question! Here is the mapping:

```yaml
jobs:
  example-job:
    command: './osu_get_latency'
    flux_option_flags: "-ompi=openmpi@5"
    working_dir: /opt/osu-benchmark/build.openmpi/libexec/osu-micro-benchmarks/mpi/one-sided  # workdir
    image: ghcr.io/rse-ops/osu-microbench:test

    # osu benchmarks requires exactly 2 processes
    tasks: 2    # num_tasks
    cores: 1    # cores_per_task
    gpus: 0     # gpus_per_task
    nodes: 1    # num_nodes
```

#### Yaml Tricks

For your jobs, you likely will want to re-use parameters. There is a trick with YAML
to define a named section, and then re-use it. Here is an example running the OSU
benchmarks.

```yaml
# matrix of experiments to run - machine types and sizes are required
# This can obviously be expanded to more sizes or machines,
matrix:
  size: [2]
  machine: ["n1-standard-1", "n1-standard-2"]

# An example of shared container options!
x-container-options: &options
  fluxOptionFlags: "-ompi=openmpi@5"
  working_dir: /opt/osu-benchmark/build.openmpi/libexec/osu-micro-benchmarks/mpi/one-sided
  image: ghcr.io/rse-ops/osu-microbench:app-latest
  # This MUST be run for the certificate generator and workers/broker
  pre_command: source /etc/profile.d/z10_spack_environment.sh

# Flux Mini Cluster experiment attributes
minicluster:
  name: osu-benchmarks
  namespace: flux-operator

# Each job can have a command and working directory
jobs:
  osu_get_latency:
    command: './osu_get_latency'
    <<: *options
  osu_acc_latency:
    command: './osu_acc_latency'
    <<: *options
  osu_fop_latency:
    command: './osu_fop_latency'
    <<: *options
  osu_get_bw:
    command: './osu_get_bw'
    <<: *options
  osu_put_bibw:
    command: './osu_put_bibw'
    <<: *options
  osu_put_latency:
    command: './osu_put_latency'
    <<: *options
  osu_cas_latency:
    command: './osu_cas_latency'
    <<: *options
  osu_get_acc_latency:
    command: './osu_get_acc_latency'
    <<: *options
  osu_put_bw:
    command: './osu_put_bw'
    <<: *options
```
