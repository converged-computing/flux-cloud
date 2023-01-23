
echo
brokerPod=""
brokerPrefix="${JOB}-0"
while [[ "${brokerPod}" == "" ]]; do
    for pod in $(kubectl get pods --namespace ${NAMESPACE} --field-selector=status.phase=Running --output=jsonpath='{.items[*].metadata.name}'); do
        if [[ "${pod}" == ${brokerPrefix}* ]]; then
            echo
            brokerPod=${pod}
            break
        fi
    done
done

echo
serverReady="false"
print_blue "Waiting for Flux Restful API Server to be ready..."
while [[ "${serverReady}" == "false" ]]; do
    echo -n "."
    sleep 2
    logs=$(kubectl logs --namespace ${NAMESPACE} ${brokerPod} | grep "Uvicorn running")
    retval=$?
    if [[ "${retval}" == "0" ]]; then
            echo
            serverReady="true"
            print_green "🌀️ Flux RestFul API Server is Ready."
            break
    fi
done
