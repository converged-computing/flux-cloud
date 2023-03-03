# CHANGELOG

This is a manually generated log to track changes to the repository for each release.
Each section should include general headers such as **Implemented enhancements**
and **Merged pull requests**. Critical items to know are:

 - renamed commands
 - deprecated / removed commands
 - changed defaults
 - backward incompatible changes (recipe file format? image file format?)
 - migration guidance (how to convert images?)
 - changed behaviour (recipe sections work differently)

The versions coincide with releases on pip. Only major versions will be released as tags on Github.

## [0.0.x](https://github.com/converged-computing/flux-cloud/tree/main) (0.0.x)
 - refactor flux submit and apply to use fluxoperator Python SDK (0.2.0)
   - This reduces scripts in output folder, but is a good tradeoff for fewer errors
 - fix bash script bugs (0.1.19)
 - support for node group level aws avail. zones, save times on each experiment apply (0.1.18)
 - data should be namespaced by cloud type (so multiple experiments can be run alongside) (0.1.17)
 - add flux-cloud ui to just bring up (and down) a user interface (0.1.16)
 - support for submit and batch, to run jobs on the same MiniCluster (0.1.15)
 - minikube docker pull needs message, update tests and typo (0.1.14)
 - wait until pods terminated and removed between applies (0.1.13)
 - add support for custom placement group name (0.1.12)
   - experiment class to support better template rendering
   - scripts are generated from templates (jinja2) without getopt
   - scripts are saved to `<experiment-dir>/.scripts` unless `--cleanup` set
   - more verbose debug about template generation
 - support for adding a job size to a job (to only run on that minicluster size) (0.1.1)
 - bug with config edit, and adding support for settings availability zones (0.1.0)
   - refactor of experiment design to handle separate minicluster size
   - add support for running experiments with local (MiniKube)
 - support for custom cloud variables in the experiments config (0.0.13)
 - support for Amazon EKS and running commands over iterations (0.0.12)
 - better control of exit codes, addition of force cluster (0.0.11)
 - support for experiment id selection, addition of osu-benchmarks example (0.0.1)
 - initial skeleton release of project (0.0.0)
