#!/bin/bash

echo "Initializing Bobber" >&2

# Read configuration from config.json
config_file="config.json"
Remote=$(jq -r '.Bobber.Remote' "$config_file")
Host_IP=$(jq -r '.Bobber.Host_IP' "$config_file")
SSH_User=$(jq -r '.Bobber.SSH_User' "$config_file")
SSH_Pwd=$(jq -r '.Bobber.SSH_Pwd' "$config_file")
Rclone=$(jq -r '.Rclone' "$config_file")
opsgenie_api_key=$(jq -r '.Opsgenie_API_Key' "$config_file") 
Active_Host=0
ops_gen=0
freshdir="/shared-data/fresh-data"
useddir="/shared-data/used-data"

# Check if Remote is empty or not "true" or "false" (case-insensitive)
if [ -z "$Remote" ] || { [[ "${Remote,,}" != "true" ]] && [[ "${Remote,,}" != "false" ]]; }; then
    echo "Remote is either empty or not true/false (case-insensitive)."
    exit 1
fi

if [ -z "$Rclone" ]; then
    echo "Error: 'Rclone' is missing." >&2
    exit 1
fi

if [ -z "$opsgenie_api_key" ]; then
    echo "Error: 'opsgenie_api_key' is missing." >&2
    exit 1
else 
    ops_gen=1
fi

if [ "${Remote,,}" == "true" ]; then
    echo "Remote Monitoring Enabled"

    mkdir -p $freshdir $useddir
    
    if [ ! -d "$freshdir" ]; then
        echo "$freshdir does not exist."
        exit 1
    fi
    
    if [ ! -d "$useddir" ]; then
        echo "$useddir does not exist."
        exit 1
    fi

    if [ -z "$Host_IP" ]; then
        echo "Error: 'host_ip' is missing." >&2
        exit 1
    fi

    if [ -z "$SSH_User" ]; then
        echo "Error: 'SSH_User' is missing." >&2
        exit 1
    fi

    if [ -z "$SSH_Pwd" ]; then
        echo "Error: 'SSH_Pwd' is missing." >&2
        exit 1
    fi

    sshpass -p "$SSH_Pwd" ssh -o BatchMode=yes -o ConnectTimeout=5 "$SSH_User@$$Host_IP" exit

    # Capture the exit status
    if [ $? -eq 0 ]; then
        echo "SSH connectivity to $Host_IP is successful."
        # Active_Host=1
    else
        echo "Failed to connect to $Host_IP via SSH. Check the client host has SSH installed."
        exit 1
    fi
    
else
    echo "Local Monitoring Enabled"
fi

# Remote Setup:
# if [ "$Active_Host" -eq 1 ] && [[ "${Remote,,}" == "true" ]]; then
if [[ "${Remote,,}" == "true" ]]; then
    #Add as seperate flagsets
    Gexflags="--driver-path /usr/local/bin/geckodriver"
    TFflags="--tf-path /app/TeamFiltration/TeamFiltration --all --keep-open"
    AZflags="--azhd_path /app/azurehound.exe --azhd"

    if [ "$ops_gen" -eq 1]; then
        OPSflag="--ops_api $opsgenie_api_key"

        # If the --password argument is provided, it will use password-based authentication.
        # If the --key argument is provided and password is not specified, it will fall back to key-based authentication using the specified private key.
        python bobber.py "/root/.evilginx/data.db" --host $Host_IP --username $SSH_User --password $SSH_Pwd $Gexflags $TFflags $AZflags $OPSflag
    else
        python bobber.py "/root/.evilginx/data.db" --host $Host_IP --username $SSH_User --password $SSH_Pwd $Gexflags $TFflags $AZflags
    fi
else
    if [ ! -d "$freshdir" ]; then
        echo "$freshdir directory has been created."
        mkdir -p $freshdir
    fi
    
    if [ ! -d "$useddir" ]; then
        echo "$useddir directory has been created."
        mkdir -p $useddir
    fi

    if [ "$ops_gen" -eq 1]; then
        OPSflag="--ops_api $opsgenie_api_key"
        python bobber.py /shared-data/data.db $Gexflags $TFflags $AZflags $OPSflag
    else
        python bobber.py /shared-data/data.db $Gexflags $TFflags $AZflags

fi
