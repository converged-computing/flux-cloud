#!/bin/bash

# Source shared helper scripts
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
    repository=${1}
    branch=${2}
    cleanup=${3}
    tmpfile=$(mktemp /tmp/flux-operator.XXXXXX.yaml)
    rm -rf $tmpfile
    run_echo wget -O $tmpfile https://raw.githubusercontent.com/${REPOSITORY}/${BRANCH}/examples/dist/flux-operator.yaml
    kubectl apply -f $tmpfile
    if [[ "${CLEANUP}" == "true" ]]; then
        rm -rf $tmpfile
    else
        echo "Cleanup is false, keeping operator install file ${tmpfile}"
    fi
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

# Defaults - these are in the config but left here for information
CLUSTER_NAME="flux-cluster"
CLUSTER_VERSION="1.22"
FORCE_CLUSTER="false"
SIZE=4
REPOSITORY="flux-framework/flux-operator"
BRANCH="main"
CLEANUP="true"

print_magenta "   cluster  : ${CLUSTER_NAME}"
print_magenta "    version : ${CLUSTER_VERSION}"
print_magenta "     size   : ${SIZE}"
print_magenta "repository  : ${REPOSITORY}"
print_magenta "     branch : ${BRANCH}"

is_installed minikube
is_installed wget

# Check if it already exists
minikube status
retval=$?
if [[ "${retval}" == "0" ]]; then
    print_blue "A MiniKube cluster already exists."
    install_operator ${REPOSITORY} ${BRANCH} ${CLEANUP}
    echo
    exit 0
fi

if [[ "${FORCE_CLUSTER}" != "true" ]]; then
    prompt "Do you want to create this cluster?"
fi

# Create the cluster
run_echo minikube start --nodes=${SIZE}
install_operator ${REPOSITORY} ${BRANCH} ${CLEANUP}

# Show nodes
run_echo kubectl get nodes

run_echo kubectl get namespace
run_echo kubectl describe namespace operator-system