# Use an official Ubuntu image with Python installed
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN set -ex \
    && wget https://dl.google.com/go/go${GOLANG_VERSION}.src.tar.gz && tar -C /usr/local -xzf go$GOLANG_VERSION.src.tar.gz \
    && rm go${GOLANG_VERSION}.src.tar.gz \
    && cd /usr/local/go/src && ./make.bash \

# Add GeckoDriver (latest version) from GitHub
RUN wget -qO- https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz | tar xvz -C /usr/local/bin

# Clone TeamFiltration repository and install its requirements
RUN git clone https://github.com/Flangvik/TeamFiltration.git /app/teamfiltration
RUN pip install --no-cache-dir -r /app/teamfiltration/requirements.txt

# Copy the custom Bobber script (3DP_Bobber.py) into the image
COPY 3DP_Bobber.py /app/3DP_Bobber.py

# Install the required Python modules for Bobber
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

# Expose any necessary ports (customize based on tool requirements)
# EXPOSE 8080

# Set entrypoint to run the Bobber tool, modify as necessary for TeamFiltration
CMD ["python", "3DP_Bobber.py"]
