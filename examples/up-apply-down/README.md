# Up and Down

This is an example of using flux cloud to bring up a cluster, install the Flux Operator
(and then you would use it as you please) and then bring it down.
You should have kubectl and gcloud installed for this demo. Note that
we use the [experiments.yaml](experiments.yaml) file as a default,
and we only provide basic metadata needed for a single experiment.

## Up

```bash
$ flux-cloud up
```

This will bring up your cluster, per the size and machine type defined
in your experiments file, and install the operator.

## Apply

An "apply" means running the single (or multiple) experiments defined in your
experiments.yaml. While these don't need to be in the same file, for simplicity
we have also defined our experiment metadata and template (provided at [minicluster-template.yaml](minicluster-template.yaml))
in this directory. For this application we will run a simple llamps application.

```bash
$ flux-cloud apply
```

Note that apply will work for a single experiment OR a matrix, so be careful!

## Down

To bring it down:

```bash
$ flux-cloud down
```
