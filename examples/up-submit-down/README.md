``# Up, Submit, Down

This is an example of using flux cloud to bring up a cluster, install the Flux Operator
(and then you would use it as you please) and run jobs with submit (on the same
MiniCluster) and then bring it down.
You should have kubectl and gcloud OR minikube installed for this demo. Note that
we use the [experiments.yaml](experiments.yaml) file as a default,
and we only provide basic metadata needed for a single experiment.

## Up

```bash
$ flux-cloud up --cloud minikube
$ flux-cloud up --cloud google
```

This will bring up your cluster, per the size and machine type defined
in your experiments file, and install the operator.

## Submit

A "submit" means running the single (or multiple) experiments defined in your
experiments.yaml on the same MiniCluster, without bringing it down between jobs.
This means we are using Flux as the scheduler proper, and we don't need to bring pods
up and down unecessarily (and submit a gazillion YAML files). There is only the number
of YAML CRD needed to correspond to the sizes of MiniClusters you run across.

```bash
$ flux-cloud submit --cloud minikube
$ flux-cloud submit --cloud google
```

## Down

To bring it down:

```bash
$ flux-cloud down
```

## Batch

Run all three with one command:

```bash
$ flux-cloud batch --cloud minikube
$ flux-cloud batch --cloud google
```

## UI

If you want to just bring up the cluster and open the user interface to interact with:

```bash
$ flux-cloud up --cloud minikube
$ flux-cloud ui --cloud minikube
$ flux-cloud down --cloud minikube
```


## Plot

I threw together a script to compare running times with info and output times,
where:

running time < info < output

```bash
$ pip install pandas matplotlib seaborn
```
```bash
$ python plot_results.py data/k8s-size-4-n1-standard-1/meta.json
```
