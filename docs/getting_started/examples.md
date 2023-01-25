# Examples

The easiest thing to do is arguably to start with an example,
and then customize it. Here we will add examples as we create them.

- [up-apply-down](https://github.com/converged-computing/flux-cloud/tree/main/examples/up-apply-down): shows using `flux-cloud apply` for individual CRD submission.
- [osu-benchmarks](https://github.com/converged-computing/flux-cloud/tree/main/examples/osu-benchmarks)
- [up-submit-down](https://github.com/converged-computing/flux-cloud/tree/main/examples/up-submit-down): shows using `flux-cloud submit` for batch submission.

The above example runs a single command in a single Kubernetes cluster and MiniCluster,
and it's lammps!


## Demo

Here is a quick demo from the [up-apply-down](https://github.com/converged-computing/flux-cloud/tree/main/examples/up-apply-down) in the repository.

<script id="asciicast-548847" src="https://asciinema.org/a/548847.js" data-speed="2" async></script>

which was actually run as:

```bash
$ flux-cloud run
```

for the purposes of the demo, and runs a lammps job on two tiny nodes!
