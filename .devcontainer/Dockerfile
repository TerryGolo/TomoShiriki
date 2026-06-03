FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system tools and keyring packages
RUN apt-get update && apt-get install -y sqlite3 git curl dbus-x11 gnome-keyring

# Copy requirements and install python packages
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Run as non-root user vscode
USER vscode

# Install Antigravity CLI (agy)
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash

# Add agy to vscode user's PATH
ENV PATH="/home/vscode/.local/bin:${PATH}"
