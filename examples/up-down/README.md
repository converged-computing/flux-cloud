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

## Down

To bring it down:

```bash
$ flux-cloud down
```
