# Examples

The easiest thing to do is arguably to start with an example,
and then customize it. Here we will add examples as we create them.

- [minikube](https://github.com/converged-computing/flux-cloud/tree/main/examples/minikube)
  - [basic](https://github.com/converged-computing/flux-cloud/tree/main/examples/minikube/basic)
  - [volumes](https://github.com/converged-computing/flux-cloud/tree/main/examples/minikube/volumes)
  - [resources](https://github.com/converged-computing/flux-cloud/tree/main/examples/minikube/resources)
  - [osu-benchmarks](https://github.com/converged-computing/flux-cloud/tree/main/examples/minikube/osu-benchmarks)
- [google](https://github.com/converged-computing/flux-cloud/tree/main/examples/google)
  - [osu-benchmarks](https://github.com/converged-computing/flux-cloud/tree/main/examples/google/osu-benchmarks)

All of the examples above (for MiniKube) are tested, and can be adopted for another cloud typically by adding
the "machines" directive under "matrix" and then any custom variables. As a reminder, you can generate
a blank template for any cloud (including variables) via:

```bash
$ flux-cloud experiment init --cloud minikube
$ flux-cloud experiment init --cloud aws
$ flux-cloud experiment init --cloud google
```


New examples for AWS will be coming soon - I didn't have credits to test when I wrote these.
