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
    
# Add Graphgrabber.sh to image.

# Install necessary PowerShell modules
RUN pwsh -Command "Install-Module -Name Az -Force -AllowClobber -Scope AllUsers"

# Clone the entire GraphRunner repository from GitHub
RUN git clone https://github.com/dafthack/GraphRunner /app/GraphRunner

# Ensure all scripts in the repository are executable
RUN chmod -R +x /app/GraphRunner 

# Set the default command to run the main GraphRunner.ps1 script with PowerShell
CMD ["pwsh", "-File", "/app/GraphRunner/GraphRunner.ps1"]
