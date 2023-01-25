# Commands

The following commands are provided by Flux Cloud. For running jobs, you can either do:

- **apply**/**run**: A single/multi job submission intended for different containers to re-create pods each time.
- **batch**/**submit**: A single/multi job submission intended for a common container base where we use the same set of pods.

Both are described in the following sections.

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

## run

> Up, apply, down in one command, ideal for completely headless runs and jobs with different containers.

The main command is a "run" that is going to, for each cluster:

1. Create the cluster
2. Run each of the experiments, saving output and timing
3. Bring down the cluster

And output will be organized based on machine, size, and command identifier. E.g.,:

```bash
data/
└── k8s-size-64-hpc6a.48xlarge
    ├── lmp-16-10-minicluster-size-16
    │   └── log.out
    ├── lmp-16-11-minicluster-size-16
    │   └── log.out
    ...
    ├── lmp-64-9-minicluster-size-64
    │   └── log.out
    └── meta.json
```

In the above, the top level directory `k8s-size-64-hpc6a.48xlarge` corresponds to our
Kubernetes cluster size and machine type. The subdirectories under that correspond
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

These commands are discussed in more next.

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

## apply

> Ideal for running multiple jobs with different containers.

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

## submit

> Ideal for one or more commands across the same container(s) and MiniCluster size.

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

## batch

> Up, submit, down in one command, ideal for jobs with the same container(s)

The "batch" command is comparable to "run" except we are running commands
across the same set of containers. We don't need to bring pods up/down each time,
and we are using Flux in our cluster to handle scheduling.
This command is going to:

1. Create the cluster
2. Run each of the experiments, saving output and timing, on the same pods
3. Bring down the cluster

The output is organized in the same way, and as before, you can choose to run a single
command with "submit"

```bash
$ flux-cloud batch --cloud aws
```

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

## ui

If you are interested in interactive submission on your own, either in the user interface
or via one of our client SDKs, you can bring up the MiniCluster and it's interface with
the Flux Restful API with `ui`:

```bash
$ flux-cloud ui --cloud minikube
```

If you have many sizes of MiniClusters, you'll need to specify the one that you want:

```bash
$ flux-cloud ui --cloud minikube --size 4
```

By default, it will use your single MiniCluster size.

<script id="asciicast-ie6CeWWNIw3NnNpEYGKfRTFpr" src="https://asciinema.org/a/ie6CeWWNIw3NnNpEYGKfRTFpr.js" data-speed="2" async></script>

Which then looks like this in the browser, available for submission via the interface itself
or the restful API until the user presses control+c to close the port forward and delete
the MiniCluster.

![img/ui.png](img/ui.png)

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

By default, flux cloud keeps all scripts that the job renders in the experiment output directory under `.scripts`. If you
want to cleanup instead, you can add the `--cleanup` flag. We do this so you can inspect a script to debug, or if you
just want to keep them for reproducibility. As an example, here is outfrom from a run with multiple repeats of the
same command, across two MiniCluster cluster sizes (2 and 4):

```console
$ tree data/k8s-size-4-n1-standard-1/.scripts/
├── cluster-create.sh
├── cluster-destroy.sh
├── eksctl-config.yaml
├── flux-operator.yaml
├── minicluster-run-lmp-16-10-minicluster-size-16.sh
├── minicluster-run-lmp-16-11-minicluster-size-16.sh
├── minicluster-run-lmp-16-12-minicluster-size-16.sh
...
├── minicluster-run-lmp-64-8-minicluster-size-64.sh
├── minicluster-run-lmp-64-9-minicluster-size-64.sh
└── minicluster.yaml
```

And that's it! I think there might be a more elegant way to determine what cluster is running,
however if the user decides to launch more than one, it might be harder. More thinking / docs / examples coming soon.
