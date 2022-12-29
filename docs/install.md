# Installation

You can typically create an environment

```bash
$ python -m venv env
$ source env/bin/activate
```

You can install with no backends (defaults to just docker) or podman)
or specific ones:

```bash
$ pip install flux-cloud

# All dependencies including testing
$ pip install flux-cloud[all]
```

or install from the repository:

```bash
$ git clone https://github.com/converged-computing/flux-cloud
$ cd flux-cloud
$ pip install .
```

To do a development install (from your local tree):

```bash
$ pip install -e .
```

This should place an executable, `flux-cloud` in your path
along with cloud specific helper scripts. Note that since this is
primarily a wrapper, we (in addition) require kubectl and gcloud
to be on your path.