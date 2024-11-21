# File Scripts Project

A collection of tools for managing machine learning workflows, file organization, and environment setup.

## Quick Links
* `tools`
  - Launch tools menu from any directory
* `source ~/.bashrc`
  - Reload shell after installation

## Available Tools

### Environment
* **Setup** (st)
  - Environment configuration and setup
  - Git synchronization
  - Command shortcuts installation
  - WANDB configuration (RunPod)

### Model Management
* **Config Manager** (cm)
  - Training configuration management
  - Template-based configuration
  - Version control integration

* **LoRA Mover** (lm)
  - Process and organize LoRA models
  - Automated file organization
  - Version management

### Cleanup
* **Remove Configs** (rc)
  - Remove configuration files
  - Batch cleanup support

* **Dataset Cache** (rd)
  - Clear dataset cache
  - Free up disk space

* **Dataset JSON** (rj)
  - Clear dataset JSON files
  - Reset training metadata

* **Checkpoints** (cp)
  - Delete .ipynb_checkpoints directories
  - Clean workspace structure

* **Delete Models** (dm)
  - Remove model files and data
  - Selective cleanup options

### Utilities
* **Download Configs** (dc)
  - Sync configurations with Dropbox
  - Cloud backup integration

* **Debug Crops** (db)
  - Debug image preparation issues
  - Visual feedback system

## Installation
```bash
# Clone repository
git clone https://github.com/rafstahelin/file-scripts.git /workspace/file-scripts

# Run setup
cd /workspace/file-scripts
python tools.py  # Select 'setup' or 'st'
source ~/.bashrc
```

## Project Structure
```bash
/workspace/file-scripts/
├── tools/          # Tool implementations
├── docs/          # Documentation
└── tools.py       # Main menu system
```

## Environment Support
* ✓ RunPod 
  - Full support with cloud integrations
  - WANDB integration
  - Network volume support

* ✓ Container
  - Standard functionality
  - Local development features

* ~ WSL
  - Basic functionality
  - Future enhancements planned

## Development
Tools follow a standardized pattern:
* Python module in tools directory
* Tool class with run() method
* Rich console interface
* Error handling and user feedback

## Support
For issues and feature requests, please open an issue on the GitHub repository.