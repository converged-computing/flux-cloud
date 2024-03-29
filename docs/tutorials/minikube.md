# MiniKube

> Running on a local MiniKube cluster

Flux Cloud (as of version 0.1.0) can run on MiniKube! There are two primary use cases for using flux-cloud:

 - **apply** is good for many larger experiments that require different container bases and / or take a longer time to run.
 - **submit** is good for smaller experiments that might use the same container bases and / or take a shorter time to run.

For the latter (submit) we will bring up the minimum number of MiniClusters required (unique based on container image size)
and launch all jobs across them, using Flux as a scheduler. As of version 0.2.0 both commands both use the fluxoperator Python
SDK, so we only use bash scripts to bring up and down cloud-specific clusters.


## Pre-requisites

You should first [install minikube](https://minikube.sigs.k8s.io/docs/start/)
and kubectl.

## Run Experiments

Let's start with a simple `experiments.yaml` file, where we have defined a number of different
experiments to run on MiniKube. `flux-cloud submit` relies entirely on this experiment file,
and programmatically generates the MiniCluster [custom resource definitions](https://flux-framework.org/flux-operator/getting_started/custom-resource-definition.html#workingdir)
for you, so you don't need to provide any kind of template.

<details>

<summary>How does it work?</summary>

A YAML file (such as the experiments.yaml) can be serialized to JSON, so each section under "jobs" is
also json, or actually (in Python) a dictionary of values. Since the values are passed to the
[Flux Operator Python SDK](https://github.com/flux-framework/flux-operator/tree/main/sdk/python/v1alpha1),
we can map them easily according to the following convention. Let's say we have a job in the experiments listing:

```yaml
jobs:
  # This is the start of the named job
  reaxc-hns:

    # These are attributes for the MiniCluster (minus repeats)
    command: 'lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite'
    image: ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
    repeats: 5
    working_dir: /home/flux/examples/reaxff/HNS
```

The content under the job name "reaxc-hns" would be mapped to the MiniCluster container as follows:

```python
from fluxoperator.models import MiniClusterContainer

container = MiniClusterContainer(
    image="ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0",
    working_dir="/home/flux/examples/reaxff/HNS",
    command="lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite",
    run_flux=True,
)
```

Note that in the above, since Go is in camel case and the Python SDK turns it into snake case,
`workingDir` is changed to `working_dir`.

</details>


Let's start with this set of experiments. Note that we've provided the same container
for all of them, meaning that we will only be creating one MiniCluster with that container.
If you provide jobs with separate containers, they will be brought up as separate clusters
to run (per each unique container, with all jobs matched to it).

```yaml
# This is intended for MiniKube, so no machine needed.
# We will create a MiniKube cluster of size 2
matrix:
  size: [2]

# Flux Mini Cluster experiment attributes
minicluster:
  name: submit-jobs
  namespace: flux-operator
  # Each of these sizes will be brought up and have commands run across it
  size: [2]

# Each of command and image are required to do a submit!
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
```

Each experiment is defined by the matrix and variables in an `experiment.yaml`, as shown above.
Note that the easiest way to get started is to use an existing example, or run:

```bash
$ flux-cloud experiment init --cloud minikube
```

In the example above, we are targeting minikube.


### Apply / Run

> Ideal if you need to run multiple jobs on different containers

This apply/run workflow will create a new MiniCluster each time (pods up and down)
and not use Flux as a scheduler proper. A workflow might look like:

```bash
$ flux-cloud up --cloud minikube
$ flux-cloud apply --cloud minikube
$ flux-cloud down --cloud minikube
```
Or achieve all three with:

```bash
$ flux-cloud run --cloud minikube
```

Let's run this with our `experiments.yaml` above in the present working directory,
and after having already run `up`:

```bash
# Also print output to the terminal (so you can watch!)
$ flux-cloud --debug apply --cloud minikube

# Only save output to output files
$ flux-cloud apply --cloud minikube
```

At the end of the run, you'll have an organized output directory with all of your
output logs, along with saved metadata about the minicluster, pods, and nodes.

```bash

```

### Submit

> Ideal for one or more commands across the one or more containers and MiniCluster sizes

The idea behind a submit is that we are going to create the minimal number of MiniClusters you
need (across the set of unique sizes and images) and then submit all jobs to Flux within
the MiniCluster. The submit mode is actually using Flux as a scheduler and not just a
"one job" running machine. A basic submit workflow using the config above might look like this:

```bash
$ flux-cloud up --cloud minikube
$ flux-cloud submit --cloud minikube
$ flux-cloud down --cloud minikube
```

Instead of running one job at a time and waiting for output (e.g., apply) we instead
submit all the jobs, and then poll every 30 seconds to get job statuses.

<details>

<summary>View full output of submit command</summary>

```bash
$ flux-cloud --debug submit --cloud minikube
```
```console
No experiment ID provided, assuming first experiment k8s-size-4-n1-standard-1.
Job experiments file generated 1 MiniCluster(s).

🌀 Bringing up MiniCluster of size 2 with image ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
All pods are in states "Running" or "Completed"
💾 Creating output directory /home/vanessa/Desktop/Code/flux/flux-cloud/examples/up-submit-down/data/minikube
MiniCluster created with credentials:
  FLUX_USER=fluxuser
  FLUX_TOKEN=d467215d-d07d-4c32-b2b9-41643cda3d7d
All pods are in states "Running" or "Completed"
Found broker pod lammps-job-0-ng8pz

Waiting for http://lammps-job-0-ng8pz.pod.flux-operator.kubernetes:5000 to be ready
🪅️  RestFUL API server is ready!
.
Port forward opened to http://lammps-job-0-ng8pz.pod.flux-operator.kubernetes:5000
Submitting reaxc-hns-1-minicluster-size-2: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Submitting reaxc-hns-2-minicluster-size-2: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Submitting reaxc-hns-3-minicluster-size-2: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Submitting reaxc-hns-4-minicluster-size-2: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Submitting reaxc-hns-5-minicluster-size-2: lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Submitting sleep-1-minicluster-size-2: sleep 5
Submitting sleep-2-minicluster-size-2: sleep 5
Submitting sleep-3-minicluster-size-2: sleep 5
Submitting sleep-4-minicluster-size-2: sleep 5
Submitting sleep-5-minicluster-size-2: sleep 5
Submitting hello-world-1-minicluster-size-2: echo hello world
Submitting hello-world-2-minicluster-size-2: echo hello world
Submitting hello-world-3-minicluster-size-2: echo hello world
Submitting hello-world-4-minicluster-size-2: echo hello world
Submitting hello-world-5-minicluster-size-2: echo hello world
Submit 15 jobs! Waiting for completion...
15 are active.
            lmp is in state RUN
            lmp is in state RUN
            lmp is in state SCHED
            lmp is in state SCHED
            lmp is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
15 are active.
            lmp is finished COMPLETED in 28.64 seconds.
            lmp is finished COMPLETED in 29.1 seconds.
            lmp is in state RUN
            lmp is in state RUN
            lmp is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
13 are active.
            lmp is in state RUN
            lmp is in state RUN
            lmp is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
          sleep is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
13 are active.
            lmp is finished COMPLETED in 36.56 seconds.
            lmp is finished COMPLETED in 35.89 seconds.
            lmp is in state RUN
          sleep is finished COMPLETED in 5.02 seconds.
          sleep is finished COMPLETED in 5.02 seconds.
          sleep is finished COMPLETED in 5.02 seconds.
          sleep is in state RUN
          sleep is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
           echo is in state SCHED
8 are active.
            lmp is finished COMPLETED in 24.6 seconds.
          sleep is finished COMPLETED in 5.02 seconds.
          sleep is finished COMPLETED in 5.02 seconds.
           echo is finished COMPLETED in 0.01 seconds.
           echo is finished COMPLETED in 0.02 seconds.
           echo is finished COMPLETED in 0.02 seconds.
           echo is finished COMPLETED in 0.01 seconds.
           echo is finished COMPLETED in 0.01 seconds.
All jobs are complete! Cleaning up MiniCluster...
All pods are terminated.
```

</details>

After submit, you will still have an organized output directory with job output files
and metadata.

```bash
$ tree -a data/minikube/
data/minikube/
└── k8s-size-4-n1-standard-1
    ├── hello-world-1-minicluster-size-2
    │   └── log.out
    ├── hello-world-2-minicluster-size-2
    │   └── log.out
    ├── hello-world-3-minicluster-size-2
    │   └── log.out
    ├── hello-world-4-minicluster-size-2
    │   └── log.out
    ├── hello-world-5-minicluster-size-2
    │   └── log.out
    ├── meta.json
    ├── reaxc-hns-1-minicluster-size-2
    │   └── log.out
    ├── reaxc-hns-2-minicluster-size-2
    │   └── log.out
    ├── reaxc-hns-3-minicluster-size-2
    │   └── log.out
    ├── reaxc-hns-4-minicluster-size-2
    │   └── log.out
    ├── reaxc-hns-5-minicluster-size-2
    │   └── log.out
    └── .scripts
        └── minicluster-size-2-lammps-job-ghcr.io-rse-ops-lammps-flux-sched-focal-v0.24.0.json
```
