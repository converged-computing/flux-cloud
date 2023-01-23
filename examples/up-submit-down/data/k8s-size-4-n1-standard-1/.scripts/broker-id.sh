#!/bin/bash

NAMESPACE="flux-operator"
JOB="lammps-job"
brokerPrefix="${JOB}-0"

for pod in $(kubectl get pods --namespace ${NAMESPACE} --field-selector=status.phase=Running --output=jsonpath='{.items[*].metadata.name}'); do
    if [[ "${pod}" == ${brokerPrefix}* ]]; then
        echo ${pod}
        break
    fi
done
