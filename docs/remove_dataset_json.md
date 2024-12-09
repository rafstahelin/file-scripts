# Remove Dataset JSON
Date: 2024-12-09
Project: FSCRIPT
Version: 0.7.0
Status: Active Development

## Overview
A specialized maintenance tool for SimpleTuner datasets that provides:
- Safe removal of aspect ratio bucket JSON files
- Interactive model directory selection
- Grouped dataset organization
- Visual progress tracking

## Core Features
1. File Management
   - Pattern-based JSON file detection
   - Safe file removal procedures
   - Batch operation support
   - Progress tracking

2. Directory Organization
   - Model directory scanning
   - Dataset grouping
   - System directory filtering
   - Visual directory listing

3. Safety Features
   - Path validation
   - Operation confirmation
   - Error handling
   - Skip logic for system directories

## Usage Examples

### Basic Usage
```python
from tools.remove_dataset_json import Tool

# Initialize tool
json_tool = Tool()

# Run interactive interface
json_tool.run()
```

### Path Structure
```bash
/workspace/
└── SimpleTuner/
    └── datasets/
        └── [dataset_name]/
            └── [model_dir]/
                ├── aspect_ratio_bucket_indices_*.json
                └── aspect_ratio_bucket_metadata_*.json
```

## Features in Detail

### Directory Scanning
- Root-level dataset scanning
- Subdirectory traversal
- Skip filters for system directories (.ipynb_checkpoints, __pycache__)
- Path validation and verification

### File Operations
```python
# Processing workflow
1. Scan for target JSON files
2. Group by dataset/model directory
3. Display interactive selection menu
4. Process removal command
5. Track progress and completion
```

### Interactive Interface
- Dataset grouping display
- Numbered directory selection
- Group operation support
- Progress visualization

## Integration Notes
- Pre-configured for SimpleTuner
- Part of file-scripts toolset
- Progress tracking support
- Rich console integration

## Error Handling
- Path validation
- Directory access verification
- Operation monitoring
- Exception management

## Best Practices
1. File Management
   - Review before removal
   - Use group operations efficiently
   - Verify completion status

2. Directory Organization
   - Maintain clean structure
   - Regular maintenance
   - Verify dataset integrity

3. Operation Safety
   - Double-check selections
   - Monitor progress
   - Verify successful completion