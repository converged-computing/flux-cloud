# MiniKube

> Running on a local MiniKube cluster

Flux Cloud (as of version 0.1.0) can run on MiniKube! The main steps of running experiments with
different container bases are:

 - **up** to bring up a cluster
 - **apply** to apply one or more CRDs from experiments defined by an experiments.yaml
 - **down** to destroy a cluster

or one or more commands with the same container base(s):

 - **up** to bring up a cluster
 - **submit** to submit one or more experiments to the same set of pods defined by an experiments.yaml
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

- TODO make a table that shows mapping of CRD variables to experiment.yaml
- TODO there should be a command to generate an "empty" experiment.yaml template
- TODO there should be a tutorial to do this
- TODO move other tutorials under this section after testing


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
If you want to make an empty template to start with:

```bash
# TODO
$ flux-cloud experiment init
```



### Apply / Run

> Ideal if you need to run multiple jobs on different containers

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
  # Number of pods to create for MiniCluster
  size: {{ minicluster.size }}

  # Disable verbose output
  logging:
    quiet: true

  # This is a list because a pod can support multiple containers
  containers:
    # The container URI to pull (currently needs to be public)
    - image: {{ job.image }}

      # You can set the working directory if your container WORKDIR is not correct.
      workingDir: /home/flux/examples/reaxff/HNS
      command: {{ job.command }}
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
