#!/bin/bash
# This script 
# - copies and renames Lora safetensors to the correct destination subdirectories
# - copies LoRA's from SimpleTuner output path to StableSwarmUI LORA PATH
# - copies all JSON files to the destination path
# - copies the "validation_images" folder to the corresponding destination
# - supports running from model_name directory with version subdirectories
#
# ===== USAGE INSTRUCTIONS =====
# 1. Make the script executable with: chmod +x /workspace/rename-models.sh
# 2. Navigate to your model name directory:
#    cd /workspace/SimpleTuner/output/MODEL_TYPE/YOUR_MODEL_NAME
#    where MODEL_TYPE is either "1subject" or "2style"
# 3. Run the script with: /workspace/rename-models.sh
# ===============================

set -e  # Exit immediately if a command exits with a non-zero status.

# Enable debug mode
set -x

# Get the current path
current_path=$(pwd)
echo "Current path: $current_path"

# Determine the directory level and extract necessary information
dir_parts=(${current_path//\// })
array_length=${#dir_parts[@]}

if [[ ${dir_parts[array_length-2]} == "1subject" || ${dir_parts[array_length-2]} == "2style" ]]; then
    model_name=${dir_parts[array_length-1]}
    model_type=${dir_parts[array_length-2]}
    search_path="$current_path"
else
    echo "Error: Invalid directory structure. Please run from MODEL_TYPE/model_name directory."
    exit 1
fi

echo "Model type: $model_type"
echo "Model name: $model_name"
echo "Search path: $search_path"

# New base path for copying files
base_copy_path="/workspace/StableSwarmUI/Models/Lora"
echo "Base copy path: $base_copy_path"

# Array to store copied safetensor files
copied_files=()

# Function to process each safetensor file
process_file() {
    local file="$1"
    echo "Processing file: $file"
    local rel_path="${file#$search_path/}"
    local dir_name=$(dirname "$rel_path")
    local file_name=$(basename "$file")
    
    # Extract version from the parent directory name
    local version=$(echo "$dir_name" | cut -d'/' -f1)
    
    # Extract step count from the directory name
    local stepcount=$(echo "$dir_name" | grep -oP '(?<=checkpoint-)\d+')
    if [[ -z "$stepcount" ]]; then
        echo "Error: Could not extract valid step count from directory name: $dir_name"
        return 1
    fi
    
    # Remove leading zeros and pad to 4 digits
    stepcount=$(echo "$stepcount" | sed 's/^0*//')
    local padded_stepcount=$(printf "%04d" "$stepcount")
    
    # Construct the new name for the destination file
    local new_name="${model_name}-${version}-${padded_stepcount}.safetensors"
    
    # Create the directory structure if it doesn't exist
    local copy_dir="${base_copy_path}/${model_type}/${model_name}/${version}"
    mkdir -p "$copy_dir"
    
    # Copy the file to the new directory with the new name
    cp "$file" "$copy_dir/$new_name"
    
    # Add the new name to the array of copied files
    copied_files+=("${version}/${new_name}")
    echo "Copied $file to $copy_dir/$new_name"
}

echo "Searching for safetensors files..."
# Find all safetensors files and process them
find "$search_path" -maxdepth 3 -name "pytorch_lora_weights.safetensors" -type f
find "$search_path" -maxdepth 3 -name "pytorch_lora_weights.safetensors" -type f | while read -r file; do
    process_file "$file"
done

# Copy all JSON files
echo "Copying JSON files..."
json_files_copied=false
find "$search_path" -maxdepth 2 -name "*.json" -type f
find "$search_path" -maxdepth 2 -name "*.json" -type f | while read -r json_file; do
    rel_path="${json_file#$search_path/}"
    destination="${base_copy_path}/${model_type}/${model_name}/${rel_path}"
    mkdir -p "$(dirname "$destination")"
    cp "$json_file" "$destination"
    echo "Copied $json_file to $destination"
    json_files_copied=true
done

# Copy validation_images folder to the corresponding destination
echo "Copying validation_images folder..."
validation_images_copied=false
find "$search_path" -maxdepth 2 -type d -name "validation_images" | while read -r validation_dir; do
    rel_path="${validation_dir#$search_path/}"
    destination="${base_copy_path}/${model_type}/${model_name}/${rel_path}"
    mkdir -p "$(dirname "$destination")"
    cp -r "$validation_dir" "$(dirname "$destination")"
    echo "Copied $validation_dir to $(dirname "$destination")"
    validation_images_copied=true
done

# Print custom output
echo "##################################################"
for file in "${copied_files[@]}"; do
    echo "copied $file"
done
if [ "$json_files_copied" = true ]; then
    echo "copied json files"
fi
if [ "$validation_images_copied" = true ]; then
    echo "copied validation_images"
fi
echo "#################################################"

echo "Processing complete."

# Disable debug mode
set +x