:hide-navigation:

Flux-Cloud
==========

.. image:: images/logo-transparent.png

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

For all of the above, there are two modes of execution. If you have different containers you want to run for jobs,
then you would want to use **run** or **apply** to create separate sets of pods, each time bringing them up and down.
That can be done with either run with one command `flux-cloud run` or broken into three:

.. code-block:: console

    $ flux-cloud up
    $ flux-cloud apply
    $ flux-cloud down

If you want to instead run one or more commands *across the same set of pods* meaning that your container(s)
base(s) do not need to change, you can use **submit**:

.. code-block:: console

    $ flux-cloud up
    $ flux-cloud submit
    $ flux-cloud down

And for the single command equivalent, do `flux-cloud batch`. The difference in the latter is that we will actually
be using Flux as a scheduler, and have much more efficient runs in that we don't need to bring down pods and bring them
back up each time.

For either approach, given any failure of a command, you are given the option to try again or exit and cancel. E.g.,
when you are developing, you can run "apply" and then easily debug until you are done and ready to bring the cluster
down.

This project is currently 🚧️ Under Construction! 🚧️ and optimized for the creator @vsoch's use case
to run experiments in Google Cloud (GKS) and Amazon Web Services (EKS). We likely will add more features
and clouds as they are needed or requested. This is a *converged computing* project that aims
to unite the worlds and technologies typical of cloud computing and
high performance computing.

To get started, check out the links below!
Would you like to request a feature or contribute? `Open an issue <https://github.com/flux-framework/flux-cloud/issues>`_.


.. toctree::
  :caption: Getting Started
  :maxdepth: 2

  getting_started/index.md
  tutorials/index.md

.. toctree::
  :caption: About
  :maxdepth: 1

  contributing.md
  about/license
