FROM python:latest

LABEL maintainer="KhulnaSoft Lab <info@khulnasoft.com>"

# Installs depedency.
RUN pip install readyapi pyyaml

# Adds entrypoint file.
ADD entrypoint.py /entrypoint.py

# Runs entrypoint on docker run.
ENTRYPOINT python /entrypoint.py
