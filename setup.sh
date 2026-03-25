#!/bin/bash
set -e

echo "Starting NITPICKERS Setup..."

# 1. Verify Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# 2. Verify Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed or not working correctly."
    exit 1
fi

echo "Docker and Docker Compose found."

# 3. Build the Docker image
echo "Building the Docker container..."
docker compose build

# 4. Prompt for alias
echo ""
read -p "Do you want to add the 'nitpick' alias to your .bashrc? [y/N]: " add_alias

if [[ "$add_alias" =~ ^[Yy]$ ]]; then
    # Get the absolute path of this directory
    TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    COMPOSE_FILE="$TOOL_DIR/docker-compose.yml"

    # Create the alias string
    ALIAS_STR="alias nitpick='TARGET_PROJECT_PATH=\$(pwd) docker compose -f $COMPOSE_FILE run --rm nitpick nitpick'"

    # Check if the alias already exists in ~/.bashrc
    if grep -q "alias nitpick=" ~/.bashrc; then
        echo "The 'nitpick' alias already exists in ~/.bashrc. Skipping."
    else
        echo "" >> ~/.bashrc
        echo "# NITPICKERS alias" >> ~/.bashrc
        echo "$ALIAS_STR" >> ~/.bashrc
        echo "Alias added successfully! Please run 'source ~/.bashrc' to apply the changes in your current terminal."
    fi
else
    echo "Skipping alias creation."
fi

echo "Setup complete!"
