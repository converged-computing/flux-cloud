echo
podsCleaned="false"
print_blue "Waiting for previous MiniCluster to be cleaned up..."
while [[ "${podsCleaned}" == "false" ]]; do
    echo -n "."
    sleep 2
    state=$(kubectl get pods --namespace ${NAMESPACE} 2>&1)
    lines=$(echo $state | wc -l)
    if [[ "${lines}" == "1" ]] && [[ "${state}" == *"No resources found in"* ]]; then
        echo
        print_green "🌀️ Previous pods are cleaned up."
        podsCleaned="true"
        break
    fi
done
