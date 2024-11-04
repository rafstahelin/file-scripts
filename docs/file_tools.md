# File Management Tools

[![Version](https://img.shields.io/badge/version-0.3.0--dev-orange)](#) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](#license)

Additional utilities for managing files, caches, and configurations in AI model development workflows.

## Table of Contents
- [Overview](#overview)
- [Tools](#tools)
  - [Remove Configs](#remove-configs)
  - [Download Configs](#download-configs)
  - [Delete Models](#delete-models)
  - [Remove Dataset JSON](#remove-dataset-json)
  - [Remove Dataset Cache](#remove-dataset-cache)
  - [Remove Checkpoints](#remove-checkpoints)
  - [Debug Crops](#debug-crops)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)

## Overview

This module extends the file-scripts collection with tools for managing SimpleTuner configurations, caches, and datasets.

## Tools

### Remove Configs
- Removes configuration files from `/workspace/SimpleTuner/config/{token_name}/{token_name}-{token_version}`
- Interactive selection of configs to remove

### Download Configs
- Downloads configurations to Dropbox using rclone
- Supports single config or batch downloads
- Uses paths.json for destination mapping

### Delete Models
- Removes model files and associated data
- Cleans up related configuration files

### Remove Dataset JSON
- Cleans up dataset JSON files from `/workspace/SimpleTuner/{token_name}-{version_number}/`
- Handles multiple resolution files:
  - `aspect_ratio_bucket_indices_{resolution}.json`
  - `aspect_ratio_bucket_metadata_{resolution}.json`

### Remove Dataset Cache
- Clears cache directories:
  - `/workspace/SimpleTuner/cache/vae/{token_name}-{datasets_name}/{resolution}`
  - `/workspace/SimpleTuner/cache/text/{token_name}-{datasets_name}/`

### Remove Checkpoints
- Removes `.ipynb_checkpoints` directories from dataset paths
- Uses direct bash command execution

### Debug Crops
- Runs image preparation debug routine
- Executes with environment variables for debugging

## Installation

1. Project is part of file-scripts:
```bash
cd /workspace/file-scripts
```

2. Create required directories:
```bash
mkdir -p tools
touch tools/__init__.py
```

3. Install dependencies (if not already present):
```bash
pip install rich
```

## Usage

Run the main script:
```bash
python file_tools.py
```

Select desired tool from the interactive menu.

## Development

### Structure
```
/workspace/file-scripts/
├── file_tools.py
├── tools/
│   ├── __init__.py
│   ├── remove_configs.py
│   ├── download_configs.py
│   ├── delete_models.py
│   ├── remove_dataset_json.py
│   ├── remove_dataset_cache.py
│   ├── remove_checkpoints.py
│   └── debug_crops.py
└── docs/
    └── file_tools.md
```

### Current Status
- Version: 0.3.0-dev
- Integration with existing file-scripts tools
- All tools use consistent UI/UX with rich library