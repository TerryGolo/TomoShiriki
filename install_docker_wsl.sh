#!/bin/bash
# Automate Docker installation inside WSL Ubuntu
# Usage: ./install_docker_wsl.sh

set -e

echo -e "\e[32m==========================================\e[0m"
echo -e "\e[32m    Installing Docker inside WSL Ubuntu   \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo "Note: This script will ask for your sudo password."

# 1. Update package list and install dependencies
echo -e "\n\e[36m1. Updating apt package index...\e[0m"
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 2. Add GPG key for Docker repository
echo -e "\n\e[36m2. Configuring Docker GPG key...\e[0m"
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Add repository to Apt sources
echo -e "\n\e[36m3. Configuring Docker Apt repository...\e[0m"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Install Docker Engine
echo -e "\n\e[36m4. Installing Docker Engine...\e[0m"
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Add user to docker group to allow running without sudo
echo -e "\n\e[36m5. Adding user '$USER' to the 'docker' group...\e[0m"
sudo usermod -aG docker $USER

# 6. Start the Docker service
echo -e "\n\e[36m6. Starting Docker daemon service...\e[0m"
sudo service docker start || sudo systemctl start docker

echo -e "\n\e[32m==========================================\e[0m"
echo -e "\e[32m      Docker installation completed!     \e[0m"
echo -e "\e[32m==========================================\e[0m"
echo "Please restart your WSL session (or open a new terminal tab/window)"
echo "for the docker group permissions to take effect."
echo ""
echo "To test your installation: docker run hello-world"
echo "=========================================="
