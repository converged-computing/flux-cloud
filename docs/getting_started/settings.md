# Settings

The following settings can be found in your settings.yml. Remember that you can
either edit this file directly, e.g.,

```bash
$ vim fluxcloud/settings.yml
```

or

```bash
$ flux-cloud config edit
```

Or you can use the config command to set or get values.

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

## Table

The following settings are available for Flux Cloud

| Name | Type |Description | Default | Required |
|------|------|------------|---------|----------|
| clouds | list | List of clouds active | "google" is currently the only supported | true |
| config_editor | string | The default executable name to edit with | vim | true |
| default_cloud | string | The default cloud to use | google | true |
| operator | object | A group of settings for the operator | NA | true |
| operator.repository | string | The operator repository to install from | flux-framework/flux-operator | true |
| operator.branch | string | The branch to install from | main | true |
| minicluster | object | A group of settings for the Flux MiniCluster | NA | true |
| minicluster.name | string | A default name for your minicluster if not set in the experiment | flux-sample | true |
| minicluster.namespace | string | A default namespace for your minicluster | flux-operator | true |
| kubernetes | object | A group of settings for the Kubernetes cluster | NA | true |
| kubernetes.version | string | The version of Kubernetes to use | 1.23 | true |
| google | object | A group of settings for Google Cloud GKE | NA | true |
| google.zone | string | The default zone to use in Google Cloud | us-central1-a | true |
| google.machine | string | The default machine to use | n2-standard-1 | true |
| google.project | string | The default google project to use | unset | true |

For the above, you'll notice the only setting you really need to define (per the user guide)
is your Google Cloud project.
