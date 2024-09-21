# Use the official PowerShell image as a base
FROM mcr.microsoft.com/azure-powershell:latest

# Set working directory inside the container
WORKDIR /app

# Install required dependencies
RUN apt-get update && \
    apt-get install -y wget git && \
    apt-get clean

# Install necessary PowerShell modules
RUN pwsh -Command "Install-Module -Name Az -Force -AllowClobber -Scope AllUsers"

# Download GraphRunner.ps1 from the GitHub repository
ADD https://raw.githubusercontent.com/dafthack/GraphRunner/main/GraphRunner.ps1 /app/GraphRunner.ps1

# Ensure the script is executable
RUN chmod +x /app/GraphRunner.ps1

# Set the default command to run GraphRunner.ps1 with PowerShell
CMD ["pwsh", "-File", "/app/GraphRunner.ps1"]
