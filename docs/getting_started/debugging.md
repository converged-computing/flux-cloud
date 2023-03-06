# Debugging

> Oh no, my MiniCluster jobs aren't running!

Kubernetes is a complex beast, so here are some debugging tips that might help you figure out what
is going on. We are generally going to be looking at objects owned by the Flux Operator - pods,
config maps, and (sometimes volumes or services). Note that the object deployed by the Flux Operator
custom resource definition is called a `minicluster`:

```bash
$ kubectl get -n flux-operator minicluster
```
```console
NAME             AGE
osu-benchmarks   57s
```

## 0. kubectl pro tips

These tips come from the amazing [Claudia](https://github.com/cmisale)!

It's fairly arduous to copy paste or type complete pod names, especially for indexed jobs where there is a random
set of characters. You can enable kubectl to autocomplete by adding this to your bash profile (`~/.bashrc`):

```bash
source <(kubectl completion bash)
```

Another shortcut that is nice to have is to make an alias for `kubectl` to just be `k`:

```bash
alias k=kubectl
```

Another tip is how to get an interactive session to a pod:

```bash
$ kubectl exec -n flux-operator -it <pod> -- bash
```

Yes, it's very docker-like! I've found I'm much faster having these tricks than before.


## 1. Start with logs

You can usually first look to pod logs to see what pods are there, and their various states:

```bash
$ kubectl get -n flux-operator pods
```

Remember that if you use `flux-cloud` apply without debug, you won't see output after it finds the broker pod,
but you'll see it being printed to logs in your `data` folder. If you want to see output, either add `--debug`
after `flux-cloud` or look at the log and add `-f` to keep it hanging:

```bash
# See instant of a log
$ kubectl logs -n flux-operator osu-benchmarks-0-vxnfq

# Stream to the terminal until the container is done
$ kubectl logs -n flux-operator osu-benchmarks-0-vxnfq -f
```

Here is looking at output for the certificate generator pod:

```bash
$ kubectl logs -n flux-operator osu-benchmarks-cert-generator
```

For `flux-cloud apply` if you want to see output consistently, it's suggested to add `--debug`,
as the miniclusters are going to be created / deleted and you'd need to grab the pod logs
multiple times!

### What should I expect to see?

The certificate generator pod runs first. It's output should *only* be
the certificate:

```console
#   ****  Generated on 2023-03-04 04:24:46 by CZMQ  ****
#   ZeroMQ CURVE **Secret** Certificate
#   DO NOT PROVIDE THIS FILE TO OTHER USERS nor change its permissions.

metadata
    name = "osu-benchmarks-cert-generator"
    time = "2023-03-04T04:24:46"
    userid = "0"
    hostname = "osu-benchmarks-cert-generator"
curve
    public-key = "l12&OlN-DwF*6rhx##Y#ZQ^9w1zON039Vxh2&+8r"
    secret-key = "o^(dM0R96q-d=2Jk-tEjgh=syRjW?q6%Kq{Q8Y4H"
```

If you see any error message about "invalid curve cert" this means that something was incorrectly
generated. As an example, you should use `preCommand` for any logic that is shared between
the certificate generator and worker/broker pods (e.g., sourcing an environment for Flux) and commands->pre
for anything else that is just for the worker/broker pods (printing to debug, etc.)

For the broker pod, you should expect to see debugging output (if logging->debug is true) and then the
Flux Broker starting. The quorum should be reported to be full. E.g.,

```console
🌀 flux start -o --config /etc/flux/config -Scron.directory=/etc/flux/system/cron.d   -Stbon.fanout=256   -Srundir=/run/flux   -Sstatedir=/var/lib/flux   -Slocal-uri=local:///run/flux/local   -Slog-stderr-level=6    -Slog-stderr-mode=local
broker.info[1]: start: none->join 13.3684ms
broker.info[1]: parent-ready: join->init 1.14525s
broker.info[1]: configuration updated
broker.info[1]: rc1.0: running /etc/flux/rc1.d/01-sched-fluxion
broker.info[1]: rc1.0: running /etc/flux/rc1.d/02-cron
broker.info[1]: rc1.0: /etc/flux/rc1 Exited (rc=0) 0.2s
broker.info[1]: rc1-success: init->quorum 0.234173s
broker.info[1]: quorum-full: quorum->run 0.204937s
```

If you see any error messages from the broker, this should be looked into.
Warnings can sometimes be OK. Ask if you aren't sure.

## 2. Use describe

You can describe any object in Kubernetes space to debug. Describe is especially important when you are debugging
storage and want to figure out why something isn't mounting. Typically you might start by looking at pods in all
namespaces:

```bash
$ kubectl get pods --all-namespaces -o wide
```

The wide format is useful because it will show you the node each pod is assigned to, which can be useful
for debugging resource limits and requests. You then might want to describe a particular pod,
maybe to look at annotations or volume mounts:

```bash
$ kubectl describe pod -n flux-operator osu-benchmarks-1-tj6bt
```

You can get json output with a get for the pod (or object):

```bash
$ kubectl get pod -n flux-operator osu-benchmarks-1-tj6bt -o json
```

And pipe that into `jq` to look for specific attributes! So let's say you see that a volume
failed for your pod. You likely want to next check your persistent volumes "pv" and claims "pvc":

```bash
$ kubectl describe -n flux-operator pv
$ kubectl describe -n flux-operator pvc
```

For volumes, if you are using a container storage interface (CSI) you likely are using a daemon set that
deploys pods. Try looking at the logs for the pods, and/or the daemonset for issues:

```bash
$ kubectl describe daemonset --all-namespaces
```

Finally, services (svc) can be useful if you suspect a permission or credential is wonky.

## 3. Advanced

Often when I'm debugging something complex I try to create the object I'm interested in so it is in a
continuously running state. As an example, to test a pod for a daemonset, I will get the raw YAML
for the daemonset and change the entrypoint to `sleep infinity`. I can then shell in and manually run
commands to see their output.
