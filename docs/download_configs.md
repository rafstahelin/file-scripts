# Download Configs Documentation
Date: 2024-12-09
Status: Active Development
Version: v01

## Overview
Tool for downloading SimpleTuner configuration directories to Dropbox while maintaining proper folder structure and matching model names.

## Core Features
- Single and bulk config downloads
- Intelligent Dropbox folder matching
- Progress tracking and feedback
- Error handling and validation

## Usage
```python
from tools.download_configs import Tool

# Initialize and run
tool = Tool()
tool.run()
```

## Path Structure
```bash
Source:
/workspace/SimpleTuner/config/[config-name]
Example: /workspace/SimpleTuner/config/vivien-01

Destination:
dbx:/studio/ai/data/1models/[model-folder]/4training/config/[config-name]
Example: dbx:/studio/ai/data/1models/023-viviensolari/4training/config/vivien-01
```

## Features
1. Path Handling
   - Automatic directory creation
   - Proper path normalization
   - Excluded directories handling

2. File Operations
   - Checksum verification
   - Progress tracking
   - .ipynb_checkpoints exclusion

3. Folder Matching
   - Smart model name matching
   - Score-based selection
   - Case-insensitive comparison

## Requirements
- Configured rclone with Dropbox access
- SimpleTuner directory structure
- Network volume access