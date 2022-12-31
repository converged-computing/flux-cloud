# Flux-Cloud

![Flux Cloud Logo](images/logo-transparent.png)

Welcome to the Flux Cloud Documentation!

This is a small helper tool to deploy experiments on the cloud using the [Flux Operator](https://github.com/flux-framework/flux-operator).
The goal was to to be able to define one or more experiments in an `experiments.yaml` file, either via a matrix or single listing,
and then alongside a custom resource definition template, to most efficiently bring up a cluster, run the experiments
and save the output, and bring it down. This is what flux cloud does! With Flux Cloud, you can:

1. Define your experiments in a yaml file
2. Pair that alongside a custom resource definition template
3. Create the cluster and install the operator
4. Run the experiments (each a MiniCluster) and save output and timings.
5. Bring down the cluster as soon as you are done.

For all of the above, you can either run with one command `flux-cloud run` or break into three:

```bash
$ flux-cloud up
$ flux-cloud apply
$ flux-cloud down
```

And given any failure of a command, you are given the option to try again or exit and cancel. E.g.,
when you are developing, you can run "apply" and then easily debug until you are done and ready to bring the cluster
down.

This project is currently 🚧️ Under Construction! 🚧️ and optimized for the creator @vsoch's use case
to run experiments in Google Cloud. We likely will add more features and clouds as they are needed
or requested. This is a *converged computing* project that aims
to unite the worlds and technologies typical of cloud computing and
high performance computing.

To get started, check out the links below!
Would you like to request a feature or contribute?
[Open an issue](https://github.com/flux-framework/flux-cloud/issues).

```{toctree}
:caption: Getting Started
:maxdepth: 1
getting_started/index.md
```

```{toctree}
:caption: About
:maxdepth: 1
contributing.md
about/license
```
