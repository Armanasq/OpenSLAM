FROM codercom/code-server:latest
USER root
RUN apt-get update && apt-get install -y python3 python3-pip git curl build-essential && rm -rf /var/lib/apt/lists/*
RUN pip3 install numpy opencv-python
USER coder
WORKDIR /home/coder
RUN mkdir -p /home/coder/algorithms
RUN mkdir -p /home/coder/backend
RUN mkdir -p /home/coder/shared
RUN mkdir -p /home/coder/data
RUN mkdir -p /home/coder/.config/code-server
RUN echo 'bind-addr: 0.0.0.0:8080\nauth: none\npassword: \ndisable-telemetry: true\n' > /home/coder/.config/code-server/config.yaml
EXPOSE 8080

