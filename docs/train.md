# Train Tool
Date: 2024-12-10
Version: 0.8.2
Status: Active Development

## Overview
A specialized tool for managing and launching SimpleTuner training that provides:
- Interactive config selection interface
- Automatic config directory scanning
- Direct training launch capability
- Environment variable handling

## Core Features
1. Configuration Management
   - Automatic config scanning
   - Base name grouping
   - Visual config listing
   - Path verification

2. Training Launch
   - Direct training execution
   - Environment variable setup
   - Virtual environment handling
   - Progress tracking

## Usage Examples

### Basic Usage
```python
from tools.train import Tool

# Initialize tool
train_tool = Tool()

# Run interactive interface
train_tool.run()
```

### Path Structure
```bash
/workspace/SimpleTuner/
└── config/
    ├── templates/        # Template configs (excluded)
    └── [config-name]/   # Training configurations
```

## Environment Setup
```python
# Default paths
self.simpletuner_path = Path('/workspace/SimpleTuner')
self.config_path = self.simpletuner_path / 'config'
```

## Features in Detail

### Configuration Scanning
- Automatic config detection
- Skip templates directory
- Group by base names
- Visual panel display

### Training Launch
```python
# Launch workflow
1. Select config from list
2. Setup environment variables
3. Activate virtual environment
4. Execute training script
5. Monitor progress
```

## Integration Notes
- Pre-configured for SimpleTuner
- Part of file-scripts toolset
- Requires working venv
- Progress tracking support

## Error Handling
- Path validation
- Config verification
- Launch monitoring
- Exception management

## Best Practices
1. Configuration Management
   - Review configs before launch
   - Verify SimpleTuner setup
   - Check virtual environment

2. Training Launch
   - Monitor initial output
   - Verify GPU availability
   - Check disk space