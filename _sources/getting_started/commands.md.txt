# Commands

The following commands are provided by Flux Cloud.

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

The main command is a "run" that is going to, for each cluster:

1. Create the cluster
2. Run each of the experiments, saving output and timing
3. Bring down the cluster

And output will be organized based on machine, size, and command identifier. E.g.,:

```bash
$ tree ./data/
├── meta.json
├── n1-standard-1-2
│   └── reaxc-hns
│       └── log.out
└── n1-standard-1-4
    └── reaxc-hns
        └── log.out
```

That looks like this:

```bash
$ flux-cloud run
```

or for entirely headless (no ask for confirmation to create/delete clusters):

```bash
$ flux-cloud run --force-cluster
```

To force overwrite of existing results (by default they are skipped)

```bash
$ flux-cloud run -e n1-standard-1-2 --force
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

And then run experiments (as you feel) with "apply."

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

Note that by default, we always wait for a previous run to be cleaned up
before continuing.

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
data/k8s-size-4-n1-standard-1/.scripts/
├── cluster-destroy.sh
├── minicluster-run-lmp-1-minicluster-size-2.sh
├── minicluster-run-lmp-1-minicluster-size-4.sh
├── minicluster-run-lmp-2-minicluster-size-2.sh
├── minicluster-run-lmp-2-minicluster-size-4.sh
└── minicluster.yaml
0 directories, 6 files
```

And that's it! I think there might be a more elegant way to determine what cluster is running,
however if the user decides to launch more than one, it might be harder. More thinking / docs / examples coming soon.
