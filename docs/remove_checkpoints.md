# Remove Checkpoints Documentation
Date: 2024-12-09
Project: File-Scripts
Version: v01
Status: Active Development

## Overview
A specialized maintenance tool for cleaning up .ipynb_checkpoints directories in SimpleTuner dataset folders. The tool provides:
- Automated detection of checkpoint directories
- Two-level recursive scanning
- Safe removal with confirmation
- Progress tracking and feedback

## Core Features
1. Directory Management
   - Automatic checkpoint detection
   - Dataset root and model subdirectory scanning
   - Safe directory removal
   - Progress tracking

2. Safety Features
   - User confirmation
   - Simple Enter/quit interface
   - Path validation
   - Error handling

## Usage Examples

### Basic Usage
```python
from tools.remove_checkpoints import Tool

# Initialize tool
cleanup_tool = Tool()

# Run interactive interface
cleanup_tool.run()
```

### Path Structure
```bash
/workspace/SimpleTuner/datasets/
└── [dataset_name]/
    ├── .ipynb_checkpoints/    # Root level checkpoint
    └── [model_dir]/
        └── .ipynb_checkpoints/  # Model level checkpoint
```

## Environment Setup
```python
# Default paths used by the tool
self.workspace_path = Path('/workspace')
self.datasets_path = self.workspace_path / 'SimpleTuner/datasets'
```

## Features in Detail

### Directory Scanning
- Root level checkpoint detection
- Model subdirectory scanning
- Path validation
- Error handling for permissions and access

### Cleanup Operations
```python
# Cleanup workflow
1. Scan dataset directories
2. Display found checkpoints
3. Await user confirmation (Enter to proceed, 'q' to cancel)
4. Remove directories with progress tracking
5. Report completion status
```

## Integration Notes
- Part of file-scripts toolset
- Integrated with RunPod environment
- Uses BaseTool functionality
- Rich console integration

## Error Handling
- Path validation
- Directory access verification
- Removal confirmation
- Exception management

## Best Practices
1. Directory Management
   - Regular cleanup maintenance
   - Verify before removal
   - Monitor cleanup completion

2. Operation Safety
   - Review directories before removal
   - Use cancellation option if unsure
   - Check completion status