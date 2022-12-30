#!/bin/bash

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

function run_echo() {
    # Show the user the command then run it
    echo "$@"
    $@
    retval=$?
    if [[ "${retval}" != "0" ]]; then
        prompt "That command was not successful. Do you want to continue?"
    fi
}

function prompt() {
    # Prompt the user with a yes/no command to continue or exit
    read -p "$@ (yes/no) " answer
    case ${answer} in
	    yes ) echo ok, we will proceed;;
        no ) echo exiting...;
	         exit;;
	    * ) echo invalid response;
		    exit 1;;
    esac
}
