# Start from Python base image
FROM python:3.9-slim

# Define Go version and GOPATH for AzureHound
ARG GOLANG_VERSION=1.16
ARG GOPATH=/opt/go

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Go
RUN set -ex \
    && wget https://dl.google.com/go/go${GOLANG_VERSION}.linux-amd64.tar.gz \
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
    
# Clone TeamFiltration repository and install its requirements
RUN git clone https://github.com/Flangvik/TeamFiltration.git /app/teamfiltration
#RUN pip install --no-cache-dir -r /app/teamfiltration/requirements.txt

# Clone and build AzureHound
RUN git clone https://github.com/BloodHoundAD/AzureHound.git ${GOPATH}/src/azurehound \
    && cd ${GOPATH}/src/azurehound \
    && go mod download \
    && go build -o /app/azurehound.exe .

# Copy the custom Bobber script (3DP_Bobber.py) into the image
COPY ./3DP_Bobber.py /app/3DP_Bobber.py

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

# Set default command to run the Bobber script
CMD ["python", "3DP_Bobber.py"]
