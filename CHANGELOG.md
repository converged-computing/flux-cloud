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
 - support for adding a job size to a job (to only run on that minicluster size) (0.1.1)
 - bug with config edit, and adding support for settings availability zones (0.1.0)
   - refactor of experiment design to handle separate minicluster size
   - add support for running experiments with local (MiniKube)
 - support for custom cloud variables in the experiments config (0.0.13)
 - support for Amazon EKS and running commands over iterations (0.0.12)
 - better control of exit codes, addition of force cluster (0.0.11)
 - support for experiment id selection, addition of osu-benchmarks example (0.0.1)
 - initial skeleton release of project (0.0.0)
