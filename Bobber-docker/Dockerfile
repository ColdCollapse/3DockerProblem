# Base image
#double check this
FROM ubuntu/python

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone the Bobber repository
RUN git clone https://github.com/Flangvik/Bobber.git .

# Install the required Python modules
RUN pip install \
    colorama==0.4.6 \
    paramiko==3.3.1 \
    Requests==2.31.0 \
    roadlib==0.19.1 \
    roadrecon==1.1.4 \
    roadtools==0.0.1 \
    roadtx==1.4.3 \
    selenium==4.14.0 \
    selenium_wire==5.1.0 \
    blinker==1.7.0

# Expose any necessary ports (customize based on Bobber's requirements)
#EXPOSE 8080

# Set the entrypoint or command to run the Bobber tool (modify according to its usage)
CMD ["python", "bobber.py"]
