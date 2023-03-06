# Persistent

This is a trick to get a MiniCluster up and running (and have it stay running)!

 - For **submit** we run a job that will never complete
 - For **apply** we do the same!

I typically use this case to debug one or the other. E.g., (given MiniKube is running with the operator installed):

```bash
$ flux-cloud --debug submit --cloud minikube
```

Then get the pod

```bash
$ kubectl get -n flux-operator pods
NAME                       READY   STATUS      RESTARTS   AGE
sleep-job-0-pm28c          1/1     Running     0          73s
sleep-job-1-h824z          1/1     Running     0          73s
sleep-job-cert-generator   0/1     Completed   0          73s
```

And ssh in!

```bash
$ kubectl exec -it -n flux-operator sleep-job-0-pm28c -- bash
```

For either submit or apply, we can connect to the instance with the broker URI

```bash
$ export FLUX_URI=local:///run/flux/local
$ sudo -u flux flux proxy $FLUX_URI
```
and then see our infinite flux job!

```bash
$ flux jobs -a
       JOBID USER     NAME       ST NTASKS NNODES     TIME INFO
    ƒCvGx8CX flux     sleep       R      1      1   2.432m sleep-job-1
```

The main difference is that submit is going to periodically ping the restful API to check
on the job. So you are probably better off with apply in that it's almost the same
thing (a flux start -> flux submit instead of starting the flux broker) without
the poll.

See the [minikube tutorials](https://converged-computing.github.io/flux-cloud/tutorials/minikube.html) for how to run this tutorial.
