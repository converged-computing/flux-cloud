# Experiments

Welcome to the Flux Cloud experiments user guide! If you come here, we are assuming you want
to run jobs with the Flux Operator on GKE, and that you have [installed](install.md) flux-cloud.
Note this project is early in development so this could change or bugs could be introduced.
Let's get started with talking about experiments. Your experiments will typically be defined by two files:

 - experiments.yaml: a yaml file that describes sizes, machines, and jobs to run
 - minicluster-template.yaml: a completely or partially filled template custom resource definition.

We will walk through example experiment files here, along with a full set of fields you can use.

### Experiment Definition

> experiments.yaml

You can choose one of the following:

 - A matrix of experiments, with sizes by machines
 - A single experiment (ideal for a demo or one-off run)
 - A list of experiments (when you want >1 but not a matrix)

#### Matrix of Experiments

A matrix might look like this:

```yaml
matrix:
  size: [2, 4]
  machine: ["n1-standard-1", "n1-standard-2"]
```

This would run each size across each machine, for a total of 4 Kubernetes clusters created.
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

### MiniCluster Definition

The minicluster is suggested to be defined, although it's not required (by default we will use the name and namespace in your settings).
As an example, here is setting a custom name and namespace:

```yaml
# Flux Mini Cluster experiment attributes
minicluster:
  name: osu-benchmarks
  namespace: flux-operator
```

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

```yaml
# Each job can have a command and working directory
jobs:
  osu_get_latency:
    command: './osu_get_latency'
    image: ghcr.io/awesome/science:latest
    workdir: /path/to/science
```

Note that likely in the future we can provide a default template and require all these variables
defined. For now we require you to provide the template.

### Custom Resource Definition

> minicluster-template.yaml

The custom resource definition template "CRD" is currently required, and is used by flux-cloud
to populate your job metadata and then submit one or more jobs to your Kubernetes cluster.
Here is an example that uses a shared working directory (so it's hard coded) and a variable
for the command:

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
  size: {{ size }}

  # Disable verbose output
  test: true

  # This is a list because a pod can support multiple containers
  containers:
    # The container URI to pull (currently needs to be public)
    - image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0

      # You can set the working directory if your container WORKDIR is not correct.
      workingDir: /home/flux/examples/reaxff/HNS
      command: {{ job.command }}
```
