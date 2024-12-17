# Set User Prompts Tool Specification
Date: 2024-12-14
Version: 0.1.0
Status: Development

## Overview
A specialized tool for managing prompt libraries in SimpleTuner configurations that provides:
- Config-based prompt template management
- Template token replacement functionality
- Interactive prompt selection interface
- Visual prompt organization and display

## Directory Structure
```bash
/workspace/SimpleTuner/
└── prompts/
    ├── templates/         # Template prompts with tokens
    │   └── *.json        # JSON files containing template prompts
    └── libraries/        # Pre-configured prompt libraries
        └── *.json        # JSON files with model-specific prompts
```

## Core Features

### 1. Config Selection Interface
- Display configs grouped by base names
- Interactive panel-based selection
- Visual grouping of related configs
- Base name extraction and organization

### 2. Prompt Organization
- Two-panel prompt display system:
  - Templates panel (top)
  - Libraries panel (bottom)
- Sequential numbering across all boxes
- Panel headers showing source file names
- Individual prompt entries displayed in boxes

### 3. Prompt Formats

#### Template Format
```json
{
    "prompt_name_token": "Prompt text with token placeholder",
    "another_name_token": "Another prompt with token"
}
```

#### Library Format
```json
{
    "prompt_name_modelname": "Prompt text with model name",
    "another_name_modelname": "Another prompt with model name"
}
```

### 4. Processing Logic
- Template Selection:
  1. Load template file
  2. Extract config base name
  3. Replace "token" with base name
  4. Save to config's user_prompt_library.json

- Library Selection:
  1. Load library file
  2. Verify prompt compatibility
  3. Save directly to config's user_prompt_library.json

## Implementation Requirements

### 1. UI Standards
- Follow file-scripts UI guidelines
- Blue panel borders
- Yellow numbering
- White text content
- Consistent panel widths

### 2. Error Handling
- File access verification
- JSON validation
- Token replacement validation
- Config compatibility checks

### 3. Backup Management
- Create backups before modification
- Timestamp-based backup naming
- Backup verification

## Integration Points
- Tools menu integration
- SimpleTuner config system
- File-scripts UI framework

## Success Criteria
1. Successful template token replacement
2. Proper config selection interface
3. Clear prompt organization display
4. Error-free prompt library updates
5. Reliable backup creation

## Notes
- Templates must use "token" as placeholder
- Libraries contain fully-formed prompts
- All JSON files must be valid format
- Maintain original prompt structure