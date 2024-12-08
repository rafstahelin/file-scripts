# Setup Tool Documentation

## Overview
The setup tool provides automated environment configuration for the file-scripts project. It handles git synchronization, command shortcuts, and environment-specific configurations.

## Features
- Git repository synchronization
- Tools command shortcut setup
- WANDB configuration (RunPod environments)
- Directory structure cleanup

## Usage
```bash
# Through tools menu
tools
> Select 'setup' or shortcut 'st'

# After setup
source ~/.bashrc  # Enable tools command
tools  # Run from any directory
```

## Implementation Details

### Git Synchronization
- Fetches latest updates
- Switches to dev branch
- Pulls latest changes
- Handles merge conflicts

### Tools Command Setup
- Creates system-wide 'tools' command
- Installs in /usr/local/bin
- Updates PATH in .bashrc
- Enables running tools menu from any directory

### WANDB Configuration (RunPod Only)
- Configures Weights & Biases API token
- Tests connection
- Handles authentication

### Directory Structure
- Cleans up temporary files
- Removes unnecessary configurations
- Maintains consistent structure

## Environment Support
- RunPod: Full support with WANDB integration
- Container: Same as RunPod without WANDB
- WSL: Basic functionality (future support planned)

## Requirements
- Python 3.6+
- Rich library
- Git installation
- Container or RunPod environment

## Error Handling
- Git sync issues
- Permission problems
- Missing dependencies
- Environment detection