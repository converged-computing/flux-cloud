# Commands

Welcome to the commands section! You can learn the details of each command below, or
check out an [example](examples.md) or [cloud tutorial](../tutorials/index.md).
The general steps you want to take are:

1. Generate or find an `experiments.yaml` configuration.
2. Decide if you want to use `submit` or `apply`
3. Create the cluster, run experiments, and clean up.

If you don't want to use an existing example, see [experiment init](#init) for how to create an `experiments.yaml` from scratch.

> What's the difference between submit and apply?

For `apply`, we are running one job per Minicluster (the Flux Operator custom resource definition). This means
we bring up an entire set of pods for each container (each entry under "jobs" in your experiment.yaml),
run the single job directly with `flux start -> flux submit` to provide the command to the broker, and then
when it finished the container will exit and the job clean up. This approach likely is suited to fewer jobs
that are longer running, and if you want to see output appear as it's available (we stream the log from the broker pod).
For `apply` we also skip creating the [Flux RESTFul API](https;//github.com/flux-framework/flux-restful-api) server,
so it's one less dependency to worry about, and you also don't need to think about exposing an API or users.

For `submit`, we take advantage of Flux as a scheduler, bringing up the fewest number of MiniClusters we can
derive based on the unique containers and sizes in your `experiments.yaml`. This means that, for each unique
set, we bring up one MiniCluster, and then submit all your jobs at once, allowing Flux to act as a scheduler.
We poll the server every 30 seconds to get an update on running jobs, and when they are all complete, jobs
output and results are saved. This approach is more ideal for many smaller jobs, as the MiniClusters are
only brought up once (and you don't need to wait for pods to go up and down for each job). The cons of this
approach are getting logs at the end, unless you decide to interact with the Flux RESTFul API on your own
earlier.

Next, read about how to use these commands in detail.

## experiment

### init

When you want to create a new experiment, do:

```bash
$ mkdir -p my-experiment
$ cd my-experiment

# Create a new experiment for minikube
$ flux-cloud experiment init --cloud minikube
$ flux-cloud experiment init --cloud aws
$ flux-cloud experiment init --cloud google
```

This will create an `experiments.yaml` template with custom variables for your
cloud of choice, and robustly commented.

<details>

<summary>View Example Output of flux-cloud experiment init</summary>

```bash
$ flux-cloud experiment init --cloud google > experiments.yaml
```
```yaml
matrix:
  size: [4]

  # This is a Google Cloud machine
  machine: [n1-standard-1]

variables:
    # Customize zone just for this experiment
    # otherwise defaults to your settings.yml
    zone: us-central1-a

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
```

</details>

## list

After creating an experiments.yaml file, you might want to know how your matrix maps out into kubernetes
clusters. To see all identifiers generated, you can use list:

```bash
$ flux-cloud list
k8s-size-8-m5.large
  sizes:
    2: k8s-size-8-m5.large 2
    4: k8s-size-8-m5.large 4
    6: k8s-size-8-m5.large 6
    8: k8s-size-8-m5.large 8
```
The above shows for the kubernetes cluster of size 8 with machine type `m5.large` we are experiments
with MiniClusters of sizes 2, 4, 6, 8

```yaml
# This can obviously be expanded to more sizes or machines,
matrix:
  size: 8
  machine: ["n1-standard-1", "n1-standard-2"]

minicluster:
  size: [2, 4, 6, 8]
```

You can also target a specific experiment cluster (meaning Kubernetes size)
with `-e` for any command, e.g.,

```bash
$ flux-cloud apply -e k8s-size-8-m5.large
```
And this will run across sizes. To ask for a specific size:

```bash
$ flux-cloud apply -e k8s-size-8-m5.large --size 2
```

### up

Here is how to bring up a cluster (with the operator installed). For this command,
we will either select the first in the matrix (default):

```bash
$ flux-cloud up
```
```console
No experiment ID provided, assuming first experiment n1-standard-1-2.
```

or if you want to specify an experiment identifier based on the machine and size, you can do that:

```bash
$ flux-cloud up -e n1-standard-1-2
```
```console
Selected experiment n1-standard-1-2.
```

And to force up without a prompt:

```bash
$ flux-cloud up -e n1-standard-1-2 --force-cluster
```

## Ways to run jobs

The following commands are provided by Flux Cloud. For running jobs, you can either do:

- **apply**/**run**: A single/multi job submission intended for different containers to re-create pods each time.
- **batch**/**submit**: A batch mode, where we submit / schedule many jobs on the fewest MiniClusters

Both are described in the following sections.

### apply / run

> Ideal for running multiple jobs with different containers.

An apply assumes that you want to create a separate MiniCluster each time, meaning
bringing up an entire set of pods, running a single command, and then bringing everything
down. This is ideal for longing running experiments, but note that it does not take advantage
of using Flux as a scheduler. Flux is basically running one job and going away.

#### apply

After "up" you can choose to run experiments (as you feel) with "apply."

```bash
$ flux-cloud apply
```

The same convention applies - not providing the identifier runs the
first entry, otherwise we use the identifier you provide.

```bash
$ flux-cloud apply -e n1-standard-1-2
```

To force overwrite of existing results (by default they are skipped)

```bash
$ flux-cloud apply -e n1-standard-1-2 --force
```

Apply is going to be creating on CRD per job, so that's a lot of
pod creation and deletion. This is in comparison to "submit" that
brings up a MiniCluster once, and then executes commands to it, allowing
Flux to serve as the scheduler. Note that by default, we always wait for a previous run to be cleaned up
before continuing.

#### run

The main command is a "run" that is going to, for each cluster:

1. Create the cluster
2. Run each of the experiments, saving output and timing
3. Bring down the cluster

And output will be organized based on executor, machine, size, and command identifier. E.g.,:

```bash
data/
└── aws
    └── k8s-size-8-hpc6a.48xlarge
        ├── _lmp-8-1-minicluster-size-8
        │   └── log.out
        ├── lmp-8-2-minicluster-size-8
        │   └── log.out
        ├── lmp-8-3-minicluster-size-8
        │   └── log.out
        ├── lmp-8-4-minicluster-size-8
        │   └── log.out
        ├── lmp-8-5-minicluster-size-8
        │   └── log.out
        └── meta.json
```

In the above, the top level directory `aws` corresponds to the flux-cloud cloud backend,
the second level `k8s-size-64-hpc6a.48xlarge` corresponds to our
Kubernetes cluster size and machine type, and the subdirectories under that correspond
to specific jobs and repeat numbers and sizes, and the `meta.json` includes a summary
of your experiments across those in json. Thus, to run everything:

```bash
$ flux-cloud run
```

or for entirely headless (no ask for confirmation to create/delete clusters):

```bash
$ flux-cloud run --force-cluster
```

To force overwrite of existing results (by default they are skipped)

```bash
$ flux-cloud run --force
```

Ask for a specific cloud:

```bash
$ flux-cloud run --cloud aws
```

If you want to have more control, you can run one Kubernetes size (across MiniCluster sizes) at a time,
each of "up" "apply" and "down":

```bash
$ flux-cloud up -e n1-standard-1-2
$ flux-cloud apply -e n1-standard-1-2
$ flux-cloud down -e n1-standard-1-2
```

### submit / batch

> Ideal for one or more commands and/or containers across persistent MiniClusters.

These commands submit multiple jobs to the same MiniCluster and actually use Flux
as a scheduler! This means we get the unique set of images and MiniCluster sizes for
your experiments, and then bring up each one, submitting the matching jobs to it.
We submit all jobs at once, and then poll Flux until they are completed to get output.

#### submit

The entire flow might look like:

```bash
$ flux-cloud up --cloud minikube
$ flux-cloud submit --cloud minikube
$ flux-cloud down --cloud minikube
```

The submit will always check if the MiniCluster is already created, and if not, create it
to submit jobs. For submit (and the equivalent to bring it up and down with batch)
your commands aren't provided in the CRD,
but rather to the Flux Restful API. Submit / batch will also generate one CRD
per MiniCluster size, but use the same MiniCluster across jobs. This is different
from apply, which generates one CRD per job to run.

#### batch

This is the equivalent of "submit" but includes the up and down for the larger
Kubernetes cluster.

```bash
$ flux-cloud batch --cloud aws
```

This command is going to:

1. Create the cluster
2. Run each of the experiments, saving output and timing, on the same pods
3. Bring down the cluster

The output is organized in the same way,

Note that since we are communicating with the FluxRestful API, you are required to
provide a `FLUX_USER` and `FLUX_TOKEN` for the API. If you are running this programmatically,
the Flux Restful Client will handle this, however if you, for example, press control C to
cancel a run, you'll need to copy paste the username and token that was previously shown
before running submit again to continue where you left off. Batch is equivalent to:

```bash
$ flux-cloud up
$ flux-cloud submit
$ flux-cloud down
```

## down

And then bring down your first (or named) cluster:

```bash
$ flux-cloud down
$ flux-cloud down -e n1-standard-1-2
```

Or all your experiment clusters:

```bash
$ flux-cloud down --all
```

You can also use `--force-cluster` here:

```bash
$ flux-cloud down --force-cluster
```

## debug

For any command, you can add `--debug` as a main client argument to see additional information. E.g.,
the cluster config created for eksctl:

```bash
$ flux-cloud --debug up
```
```console
No experiment ID provided, assuming first experiment m5.large-2.
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: flux-cluster
  region: us-east-1
  version: 1.23

# availabilityZones: ["us-east-1a", "us-east-1b", "us-east-1d"]
managedNodeGroups:
  - name: workers
    instanceType: m5.large
    minSize: 2
    maxSize: 2
    labels: { "fluxoperator": "true" }
...
```

## scripts

Flux cloud (prior to version 0.2.0) ran each job with a script, and it would save each script. Since version 0.2.0,
we refactored to do everything with Python APIs/SDKs, so we no longer save submit scripts. However, we still save
scripts for bringing up an down each cluster, along with node and pod metadata (as json). We save this in in the
hidden `.scripts` directory.

```console
$ tree -a ./data/
./data/
└── minikube
    └── k8s-size-4-local
        ├── lmp-size-2-minicluster-size-2
        │   └── log.out
        ├── lmp-size-4-minicluster-size-4
        │   └── log.out
        ├── meta.json
        └── .scripts
            ├── minicluster-size-2-lammps-job-ghcr.io-rse-ops-lammps-flux-sched-focal-v0.24.0.json
            ├── nodes-2-lammps-job-ghcr.io-rse-ops-lammps-flux-sched-focal-v0.24.0.json
            └── pods-size-2-lammps-job-ghcr.io-rse-ops-lammps-flux-sched-focal-v0.24.0.json
```

And that's it! We recommend you look at [examples](examples.md) or [tutorials](../tutorials/index.md) for
getting started. If you are brave, just run `flux-cloud experiment init --cloud <cloud>` to create
your own experiment from scratch.
