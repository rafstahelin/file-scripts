# Config Manager

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](#)

A command-line tool for managing configuration folders and datasets efficiently. The Config Manager simplifies the process of creating new configurations based on existing ones or templates, ensuring consistency and reducing manual effort.

## Table of Contents
- [Features](#features)
- [Technical Details](#technical-details)
- [Usage Guide](#usage-guide)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Features
- Interactive CLI with user-friendly navigation
- Folder Management
  * Create from existing configurations
  * Use predefined templates (lora/lokr)
  * Automated version management
- Dataset Management
  * Organized dataset selection
  * Automatic dataset integration
- Configuration File Handling
  * Automatic token name updating
  * Version control integration
  * Path management

## Technical Details

### File Structure
```
config_folder/
├── config.json
├── user_prompt_library.json
└── multidatabackend.json
```

### Configuration Updates
- Token name replacement in all configuration files
- Version number management
- Dataset path integration
- Cache directory structure maintenance

## Usage Guide

### Basic Usage
1. Run the script:
   ```bash
   python config_manager.py
   ```

2. Select source type:
   - Existing folder
   - 'lora' template
   - 'lokr' template

3. Follow the interactive prompts

### Advanced Options
- Dataset Management
  * Use existing dataset: `y/n` option
  * New dataset selection from organized panels
- Version Control
  * Automatic version incrementing
  * Custom version specification

## Examples

### Creating New Configuration
```plaintext
=== Configuration Folder Management Tool ===
Select source folder type:
1. Use existing folder
2. Use 'lora' template
3. Use 'lokr' template

Enter choice: 1
[Displays available folders...]
```

### Version Management Example
```plaintext
Source Directory: lora-03
Token Name: lora
New Version: 04
New Folder Name: lora-04
Dataset: lulu-15
```

## Troubleshooting

### Common Issues
1. Permission Errors
   - Ensure write permissions in target directory
   - Check file ownership

2. Dataset Integration
   - Verify dataset path exists
   - Check path formatting in configuration

### Error Messages
- "No input given": Requires user input for selection
- "Invalid selection": Number outside available range
- "Directory already exists": Version conflict

## Version History
- v1.0.0: Initial release
  * Basic configuration management
  * Dataset integration
  * Template support