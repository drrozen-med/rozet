#!/bin/bash
# Install rozett command globally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Find a suitable bin directory
if [ -d "$HOME/.local/bin" ]; then
    BIN_DIR="$HOME/.local/bin"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
else
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

echo "Installing 'rozett' command to $BIN_DIR..."

# Create the wrapper script
cat > "$BIN_DIR/rozett" << 'ROZETT_SCRIPT'
#!/bin/bash
# Global rozett command - starts Rozet orchestrator from anywhere

# Find the project root (this script's location or common install locations)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try to find rozet project
if [ -f "$SCRIPT_DIR/../rozet" ]; then
    ROZET_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -f "$HOME/projects/rozet/rozet" ]; then
    ROZET_DIR="$HOME/projects/rozet"
elif [ -f "/opt/rozet/rozet" ]; then
    ROZET_DIR="/opt/rozet"
else
    # Try to find it in common locations
    for dir in "$HOME/projects" "$HOME/code" "$HOME/workspace" "$HOME"; do
        if [ -f "$dir/rozet/rozet" ]; then
            ROZET_DIR="$dir/rozet"
            break
        fi
    done
fi

if [ -z "$ROZET_DIR" ] || [ ! -f "$ROZET_DIR/rozet" ]; then
    echo "Error: Could not find Rozet project directory." >&2
    echo "Please set ROZET_HOME environment variable:" >&2
    echo "  export ROZET_HOME=/path/to/rozet" >&2
    exit 1
fi

# Use ROZET_HOME if set
if [ -n "$ROZET_HOME" ]; then
    ROZET_DIR="$ROZET_HOME"
fi

# Change to project directory and run
cd "$ROZET_DIR"
exec "$ROZET_DIR/rozet" "$@"
ROZETT_SCRIPT

chmod +x "$BIN_DIR/rozett"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "⚠️  $BIN_DIR is not in your PATH."
    echo "Add this to your ~/.zshrc or ~/.bashrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then run: source ~/.zshrc  (or source ~/.bashrc)"
fi

echo "✅ 'rozett' command installed to $BIN_DIR"
echo ""
echo "You can now run 'rozett' from anywhere!"
echo "Try: rozett --repl"

