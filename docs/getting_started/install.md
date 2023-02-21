# Installation

## Setup

Note that if you first want to create user-level settings, do:

```bash
$ flux-cloud config inituser
```

You should then edit the defaults in your settings.yml, either via directly editing
the settings file, via the command line.

```bash
$ flux-cloud config get default_cloud
default_cloud                  google

$ flux-cloud config get google:project
google:project                 unset

$ flux-cloud config set google:project dinosaur
Updated google:project to be dinosaur

$ flux-cloud config get google:project
google:project                 dinosaur
```

Ensure your default cloud is set to the one you want!

```bash
$ flux-cloud config get default_cloud
default_cloud                 aws

$ flux-cloud config set default_cloud google
default_cloud                 google
```

We don't discriminate or judge about clouds, we like them all!
Also set your editor of choice, and then you can edit in it (it defaults to vim)

```bash
$ flux-cloud config get config_editor
config_editor                  vim
```

```bash
$ flux-cloud config edit
```

See the [documentation about settings](settings.md) for more detail about what you can set,
and defaults.

## flux-cloud

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
