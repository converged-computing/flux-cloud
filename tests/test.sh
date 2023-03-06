#!/bin/bash

# Usage: /bin/bash script/test.sh $name 30
HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT=$(dirname ${HERE})
cd ${ROOT}

set -eEu -o pipefail

name=${1}

function is_installed () {
    # Determine if a command is available for use!
    cmd="${1}"
    if command -v $cmd >/dev/null; then
        echo "$cmd is installed"
    else
        echo "$cmd could not be found"
        exit 1
    fi
}

# Ensure flux-cloud is installed / on path
is_installed flux-cloud

echo "   Name: ${name}"

# Output and error files
testdir="${ROOT}/tests/${name}"
cd ${testdir}

# Create temporary directory
output=$(mktemp -d -t ${name}-data-XXXXXX)

# Quick helper script to run a test
echo "flux-cloud run --cloud minikube --output ${output} --force-cluster"
flux-cloud run --cloud minikube --output ${output} --force-cluster
retval=$?

if [[ ${retval} -ne 0 ]]; then
    echo "Issue running Flux Cloud, return value ${retval}"
    exit ${retval}
fi

echo ${output}
rm -rf ${output}
