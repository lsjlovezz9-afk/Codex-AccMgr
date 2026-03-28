#!/bin/bash
# Codex AccMgr - One-Click Installer for macOS/Linux

set -e

REPO_URL="https://github.com/lsjlovezz9-afk/Codex-AccMgr.git"
INSTALL_DIR="$HOME/.codex/codex-accmgr-app"
ALIAS_NAME="codex-accmgr"

echo "========================================"
echo "    Codex AccMgr - Auto Installer"
echo "========================================"

# Check requirements
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: python3/python is not installed. Please install Python 3.6+ first."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Clone or update repository
echo "[1/3] Cloning/Updating repository..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists. Updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    mkdir -p "$HOME/.codex"
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Make scripts executable
chmod +x run.sh

# Install alias based on shell
echo "[2/3] Configuring shell alias..."
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ] || [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [[ "$SHELL" == *"bash"* ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
else
    echo "Warning: Unsupported shell. Please add the alias manually:"
    echo "alias $ALIAS_NAME='\"$INSTALL_DIR/run.sh\"'"
fi

if [ -n "$SHELL_CONFIG" ]; then
    ALIAS_STR="alias $ALIAS_NAME='\"$INSTALL_DIR/run.sh\"'"
    if grep -q "alias ${ALIAS_NAME}=" "$SHELL_CONFIG"; then
        echo "Alias '$ALIAS_NAME' already exists in $SHELL_CONFIG. Skipping."
    else
        echo -e "\n# Codex AccMgr" >> "$SHELL_CONFIG"
        echo "$ALIAS_STR" >> "$SHELL_CONFIG"
        echo "Added '$ALIAS_NAME' alias to $SHELL_CONFIG"
    fi
fi

echo "[3/3] Installation Complete! 🎉"
echo "========================================"
echo ""
echo "To start using Codex AccMgr, please restart your terminal or run:"
if [ -n "$SHELL_CONFIG" ]; then
    echo "  source $SHELL_CONFIG"
fi
echo ""
echo "Then simply type: $ALIAS_NAME"
echo "========================================"
