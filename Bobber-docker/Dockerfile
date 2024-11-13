FROM python:3.9-slim

# Define Go version and GOPATH for AzureHound
ARG GOLANG_VERSION=1.20
ARG GOPATH=/opt/go

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Go
RUN wget https://dl.google.com/go/go${GOLANG_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GOLANG_VERSION}.linux-amd64.tar.gz \
    && rm go${GOLANG_VERSION}.linux-amd64.tar.gz

# Add Go to PATH
ENV PATH="/usr/local/go/bin:${PATH}"

# Set GOPATH for AzureHound
ENV GOPATH=${GOPATH}

# Install GeckoDriver (latest version)
RUN wget -O /tmp/geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar xvz -f /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && rm /tmp/geckodriver.tar.gz

# Clone AzureHound repository
RUN git clone https://github.com/BloodHoundAD/AzureHound.git ${GOPATH}/src/azurehound

# Build AzureHound with version info and make it executable
RUN cd ${GOPATH}/src/azurehound \
    && go mod tidy \
    && go mod download \
    && go build -ldflags="-s -w -X github.com/bloodhoundad/azurehound/v2/constants.Version=$(git describe --tags --exact-match 2>/dev/null || git rev-parse HEAD)" -o /app/azurehound.exe \
    && chmod +x /app/azurehound.exe

# Copy the custom Bobber script (3DP_Bobber.py) into the image
COPY ./Bobber-docker/3DP_Bobber.py /app/3DP_Bobber.py

# Install required Python modules for Bobber
RUN pip install --no-cache-dir \
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
RUN wget https://github.com/rclone/rclone/releases/download/v1.64.0/rclone-v1.64.0-linux-amd64.tar.gz \
    && tar -xzf rclone-v1.64.0-linux-amd64.tar.gz \
    && mv rclone-v1.64.0-linux-amd64/rclone /usr/local/bin/ \
    && chmod +x /usr/local/bin/rclone \
    && rm -rf rclone-v1.64.0-linux-amd64*

# Make TeamFiltration executable
RUN chmod +x TeamFiltration/TeamFiltration

# Set default command to run the Bobber script
#CMD ["python", "3DP_Bobber.py"]
