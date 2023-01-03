# Commands

The following commands are provided by Flux Cloud.

## list

After creating an experiments.yaml file, you might want to know how your matrix maps out into kubernetes
clusters. To see all identifiers generated, you can use list:

```bash
$ flux-cloud list
n1-standard-1-2
n1-standard-2-2
n1-standard-1-4
n1-standard-2-4
n1-standard-1-6
n1-standard-2-6
```
The above shows the format `<machine>-<size>`, and is generated from this matrix:

```yaml
# This can obviously be expanded to more sizes or machines,
matrix:
  size: [2, 4, 6]
  machine: ["n1-standard-1", "n1-standard-2"]
```

We have these identifiers for the purposes of output. This means that if you use
`flux-cloud run`, the cluster sizes and machines will be written to the correct
place by way of iterating through the matrices. If you are using this in more of
an "expert" mode and running "apply" or "up" or "down" on your own, you will
need to target a specific identifier (one of the above) otherwise the tool won't
know which cluster you want to interact with.

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

If you want to have more control, you can run one step at a time,
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

And that's it! I think there might be a more elegant way to determine what cluster is running,
however if the user decides to launch more than one, it might be harder. More thinking / docs / examples coming soon.