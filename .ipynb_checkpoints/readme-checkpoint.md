# File Management Scripts

[![Version](https://img.shields.io/badge/version-0.2.0--dev-orange)](#) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

A collection of utility scripts for managing and processing files in AI model development workflows.

## Table of Contents
- [Overview](#overview)
- [Scripts](#scripts)
  - [Config Manager](#config-manager)
  - [LoRA Model Manager](#lora-model-manager)
- [Installation](#installation)
- [Requirements](#requirements)
- [Development](#development)
- [License](#license)

## Overview
This repository contains utility scripts designed to streamline file management tasks in AI model development workflows. Current tools include configuration management and LoRA model file organization.

## Scripts

### Config Manager
A command-line tool for managing configuration folders and datasets efficiently.

#### Features
- Interactive CLI with user-friendly navigation
- Create configurations from existing folders or templates
- Automated dataset management
- Cross-platform support
- Configuration file auto-updating

#### Usage
```bash
python config_manager.py
```

[Detailed Config Manager Documentation](docs/config_manager.md)

### LoRA Model Manager
A comprehensive tool for managing LoRA model files with features for renaming, organizing, and syncing to cloud storage.

#### Features
- Process single or multiple model versions
- Automatic file renaming with consistent patterns
- Cloud synchronization with Dropbox
- Interactive CLI with visual progress tracking
- Error handling and validation

#### Usage
```bash
python lora_mover.py
```

[Detailed LoRA Model Manager Documentation](docs/lora_mover.md)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rafstahelin/file-scripts.git
cd file-scripts
```

2. Install required packages:
```bash
pip install rich
```

3. Configure required services:
- Rclone with Dropbox access (for LoRA Model Manager)

## Requirements
- Python 3.6 or higher
- rich library for enhanced console output
- rclone (for cloud sync features)

## Development

### Current Status
- Version: 0.2.0-dev
- Branch: dev

### Versioning
We use [Semantic Versioning](https://semver.org/):
- MAJOR.MINOR.PATCH (e.g., 1.0.0)
- Development versions append `-dev` (e.g., 0.2.0-dev)
- Beta versions append `-beta` (e.g., 0.2.0-beta)

### Branches
- `main`: Production-ready code
- `dev`: Development branch for ongoing work

### Contributing
1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/my-new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.