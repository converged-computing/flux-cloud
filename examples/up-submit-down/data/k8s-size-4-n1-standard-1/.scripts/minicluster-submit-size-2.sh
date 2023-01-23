#!/bin/bash

# This is a template that will be populated with variables by Flux-Cloud
# We only run it to check if a MiniCluster is running. An apply is only
# needed if the MiniCluster is not created yet.

# Include shared helper scripts
# Colors
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
clear='\033[0m'

function print_red() {
    echo -e "${red}$@${clear}"
}
function print_yellow() {
    echo -e "${yellow}$@${clear}"
}
function print_green() {
    echo -e "${green}$@${clear}"
}
function print_blue() {
    echo -e "${blue}$@${clear}"
}
function print_magenta() {
    echo -e "${magenta}$@${clear}"
}
function print_cyan() {
    echo -e "${cyan}$@${clear}"
}

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

function install_operator() {
    # Shared function to install the operator from a specific repository branch and cleanup
    script_dir=${1}
    repository=${2}
    branch=${3}
    tmpfile="${script_dir}/flux-operator.yaml"
    run_echo wget -O $tmpfile https://raw.githubusercontent.com/${repository}/${branch}/examples/dist/flux-operator.yaml
    kubectl apply -f $tmpfile
}


function run_echo() {
    # Show the user the command then run it
    echo
    print_green "$@"
    retry $@
}

function run_echo_allow_fail() {
    echo
    print_green "$@"
    $@ || true
}

function retry() {
    # Retry an unsuccessful user command, per request
    while true
    do
        $@
        retval=$?
        if [[ "${retval}" == "0" ]]; then
            return
        fi
        print_blue "That command was not successful. Do you want to try again? 🤔️"
        read -p " (yes/no) " answer
        # Exit with non-zero response so we know to stop in script.
        case ${answer} in
	       yes ) continue;;
           no ) echo exiting...;
	            exit 1;;
	       * )  echo invalid response;
		        exit 1;;
        esac
    done
}


function prompt() {
    # Prompt the user with a yes/no command to continue or exit
    print_blue "$@ 🤔️"
    read -p " (yes/no) " answer
    case ${answer} in
	    yes ) echo ok, we will proceed;;
        no ) echo exiting...;
	         exit 1;;
	    * )  echo invalid response;
		     exit 1;;
    esac
}


function with_exponential_backoff {
    # Run with exponential backoff - assume containers take a while to pull
    local max_attempts=100
    local timeout=1
    local attempt=0
    local exitcode=0

    while [[ $attempt < $max_attempts ]]; do
      "$@"
      exitcode=$?

      if [[ $exitcode == 0 ]]; then
        break
      fi

      echo "Failure! Retrying in $timeout.." 1>&2
      sleep $timeout
      attempt=$(( attempt + 1 ))
      timeout=$(( timeout * 2 ))
    done

    if [[ $exitCode != 0 ]]; then
      echo "You've failed me for the last time! ($@)" 1>&2
    fi
    return $exitcode
}

NAMESPACE="flux-operator"
CRD="/home/vanessa/Desktop/Code/flux/flux-cloud/examples/up-submit-down/data/k8s-size-4-n1-standard-1/.scripts/minicluster-size-2.yaml"
JOB="lammps-job"

# Size -1 to account for certificate generator
SIZE=2

print_magenta "  apply : ${CRD}"
print_magenta "    job : ${JOB}"

is_installed kubectl

# Create the namespace (ok if already exists)
run_echo_allow_fail kubectl create namespace ${NAMESPACE}

# Always cleanup a previous one so tokens don't get stale
run_echo_allow_fail kubectl delete -f ${CRD}
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

# Ensure we have a MiniCluster of the right namespace running
echo
print_green "🌀️ Creating MiniCluster in ${NAMESPACE}"
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
