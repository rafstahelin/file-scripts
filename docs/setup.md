# Setup Tool Documentation
Version: 0.8.0
Last Updated: 2024-12-10

## Overview
The setup tool provides automated initialization and configuration of the file-scripts environment, including navigation shortcuts, dependencies, and workspace organization.

## Features
- Automated dependency installation
- Navigation shortcut configuration
- Git repository synchronization
- WANDB configuration (RunPod only)
- Tool launcher setup

## Navigation Shortcuts
The following shortcuts are configured for quick directory access:

| Shortcut | Path | Description |
|----------|------|-------------|
| `tools`  | N/A  | Launch tools menu |
| `config` | `/workspace/SimpleTuner/config` | Configuration directory |
| `data`   | `/workspace/SimpleTuner/datasets` | Datasets directory |
| `out`    | `/workspace/SimpleTuner/output` | Output directory |
| `flux`   | `/workspace/StableSwarmUI/Models/loras/flux` | Flux models directory |
| `scripts`| `/workspace/file-scripts` | Scripts directory |

## Usage
1. Initial Setup:
   ```bash
   python setup.py
   ```

2. Activating Shortcuts:
   ```bash
   source ~/.bashrc
   ```

## Environment Support
- Fully supported in RunPod environment
- WSL/local environment support with path adaptations
- Persistent shortcuts in network volume

## Technical Details
- Shortcuts are installed in `/usr/local/bin`
- Configuration persists in `~/.bashrc`
- Compatible with PyTorch240 container
- Automatic path validation and creation

## Best Practices
1. Run setup tool after container initialization
2. Verify shortcuts after setup
3. Use `source ~/.bashrc` if shortcuts don't activate automatically
4. Check environment variables for WANDB configuration