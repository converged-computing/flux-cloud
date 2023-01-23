# Apply the job, get pods
run_echo kubectl apply -f ${CRD}
run_echo kubectl get -n ${NAMESPACE} pods

# continue until we find the index-0 pod
brokerPrefix="${JOB}-0"
brokerReady="false"

echo
print_blue "Waiting for broker pod with prefix ${brokerPrefix} to be created..."
while [[ "${brokerReady}" == "false" ]]; do
    echo -n "."
    sleep 2
    for pod in $(kubectl get pods --selector=job-name=${JOB} --namespace ${NAMESPACE} --output=jsonpath='{.items[*].metadata.name}'); do
        if [[ "${pod}" == ${brokerPrefix}* ]]; then
            echo
            print_green "🌀️ Broker pod is created."
            brokerReady="true"
            break
        fi
    done
done

# Now broker pod needs to be running
echo
print_blue "Waiting for broker pod with prefix ${brokerPrefix} to be running..."
brokerReady="false"
while [[ "${brokerReady}" == "false" ]]; do
    echo -n "."

    # TODO - we likely want to check for running OR completed, it's rare but sometimes they can complete too fast.
    for pod in $(kubectl get pods --namespace ${NAMESPACE} --field-selector=status.phase=Running --output=jsonpath='{.items[*].metadata.name}'); do
        if [[ "${pod}" == ${brokerPrefix}* ]]; then
            echo
            print_green "🌀️ Broker pod is running."
            brokerReady="true"
            break
        fi
    done
done
