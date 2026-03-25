#!/bin/bash
set -e

echo "=== NITPICKERS Setup Tool ==="

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

echo "Requirement Check: Docker and Docker Compose found."

# 3. Build the Docker image
echo "Step 1: Building the NITPICKERS Docker container..."
docker compose build

# 4. Handle Alias Registration
echo ""
read -p "Do you want to add/update the 'nitpick' alias in your .bashrc? [y/N]: " add_alias

if [[ "$add_alias" =~ ^[Yy]$ ]]; then
    BASHRC="$HOME/.bashrc"
    # Get the absolute path of the current tool directory
    TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    COMPOSE_FILE="$TOOL_DIR/docker-compose.yml"

    # Define the dynamic alias string
    # It captures the directory where you run 'nitpick' as the TARGET_PROJECT_PATH
    ALIAS_STR="alias nitpick='TARGET_PROJECT_PATH=\$(pwd) docker compose -f $COMPOSE_FILE run --rm nitpick nitpick'"

    echo "Step 2: Registering alias in $BASHRC..."

    # Create a temporary file to rebuild .bashrc without the old NITPICKERS block
    # This prevents duplicate lines and handles cleanup
    sed -i '/# NITPICKERS START/,/# NITPICKERS END/d' "$BASHRC"

    # Remove trailing empty lines at the end of the file to prevent accumulation
    sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$BASHRC"

    # Append the clean block
    cat << EOF >> "$BASHRC"

# NITPICKERS START
# NITPICKERS alias
$ALIAS_STR
# NITPICKERS END
EOF

    echo "Success: Alias has been set/updated."
    echo "Please run the following command to apply changes immediately:"
    echo "source ~/.bashrc"
else
    echo "Skipping alias registration."
fi

echo ""
# The final message in Green
echo -e "${GREEN} Setup complete! You can now run 'nitpick' from any project directory.${NC}"


docker system prune -f
