# Use a Go base image with the desired version, adding Python
FROM golang:1.23 AS builder

# Install Python dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3 \
    libicu-dev \ 
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set GOPATH and working directory for AzureHound
ENV GOPATH=/opt/go
WORKDIR /app

# Install GeckoDriver (latest version)
RUN wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar xvz -f /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && rm /tmp/geckodriver.tar.gz

# Clone AzureHound repository and build it
RUN git clone https://github.com/BloodHoundAD/AzureHound.git ${GOPATH}/src/azurehound \
    && cd ${GOPATH}/src/azurehound \
    && go mod tidy \
    && go mod download \
    && go build -ldflags="-s -w -X github.com/bloodhoundad/azurehound/v2/constants.Version=$(git describe --tags --exact-match 2>/dev/null || git rev-parse HEAD)" -o /app/azurehound.exe \
    && chmod +x /app/azurehound.exe

# Copy the custom Bobber script (3DP_Bobber.py) into the image
COPY ./Bobber-docker/3DP_Bobber.py /app/3DP_Bobber.py

# Install required Python modules for Bobber
RUN pip3 install --no-cache-dir --break-system-packages\
    colorama==0.4.6 \
    paramiko==3.3.1 \
    requests==2.31.0 \
    roadlib==0.19.1 \
    roadrecon==1.1.4 \
    roadtools==0.0.1 \
    roadtx==1.4.3 \
    selenium==4.14.0 \
    selenium_wire==5.1.0 \
    blinker==1.7.0

# Download and unzip the precompiled TeamFiltration release
RUN wget https://github.com/Flangvik/TeamFiltration/releases/download/v3.5.4/TeamFiltration-v3.5.4-linux-x86_64.zip -O TeamFiltration.zip \
    && unzip TeamFiltration.zip -d TeamFiltration \
    && rm TeamFiltration.zip

# Install Rclone from GitHub
RUN wget https://github.com/rclone/rclone/releases/download/v1.68.2/rclone-v1.68.2-linux-amd64.zip \
    && unzip rclone-v1.68.2-linux-amd64.zip \
    && mv rclone-v1.68.2-linux-amd64/rclone /usr/local/bin/ \
    && chmod +x /usr/local/bin/rclone \
    && rm -rf rclone-v1.68.2-linux-amd64*

# Make TeamFiltration executable
RUN chmod +x TeamFiltration/TeamFiltration

# Set default command to run the Bobber script
#CMD ["python3", "3DP_Bobber.py"]
