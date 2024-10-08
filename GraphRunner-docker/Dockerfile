# Use the official Kali Linux image as a base
FROM kalilinux/kali-rolling:latest

# Set working directory inside the container
WORKDIR /app

# Update the package list and install dependencies
RUN apt-get update && \
    apt-get install -y wget git software-properties-common && \
    wget -q "https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb" && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y powershell && \
    apt-get clean

# Install necessary PowerShell modules
RUN pwsh -Command "Install-Module -Name Az -Force -AllowClobber -Scope AllUsers"

# Download GraphRunner.ps1 from the GitHub repository
ADD https://raw.githubusercontent.com/dafthack/GraphRunner/main/GraphRunner.ps1 /app/GraphRunner.ps1

# Ensure the script is executable
RUN chmod +x /app/GraphRunner.ps1

# Set the default command to run GraphRunner.ps1 with PowerShell
CMD ["pwsh", "-File", "/app/GraphRunner.ps1"]
