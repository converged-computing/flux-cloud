# Apply the job, get pods
run_echo kubectl apply -f ${CRD}
run_echo kubectl get -n ${NAMESPACE} pods

# continue until we find the index-0 pod
podsReady="false"

echo
print_blue "Waiting for MiniCluster of size ${SIZE} to be ready..."
while [[ "${podsReady}" == "false" ]]; do
    echo -n "."
    sleep 2
    pods=$(kubectl get pods --namespace ${NAMESPACE} --field-selector=status.phase=Running --output=name | wc -l)
    if [[ "${pods}" == "${SIZE}" ]]; then
            echo
            print_green "🌀️ All pods are running."
            podsReady="true"
            break
    fi
done
