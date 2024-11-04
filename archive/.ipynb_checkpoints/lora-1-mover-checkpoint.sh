#!/bin/bash
# This script 
# - renames Lora safetensors (without checkpoints)
# - copies LoRA's from SimpleTuner output path to StableSwarmUI LORA PATH
# - copies validation_images folder and JSON files from base path
#
# ===== USAGE INSTRUCTIONS =====
# 1. Make the script executable with: chmod +x /workspace/rename-models.sh
# 2. Navigate to your model version directory:
#    cd /workspace/SimpleTuner/output/MODEL_TYPE/YOUR_MODEL_NAME/YOUR_VERSION
#    where MODEL_TYPE is either "1subject" or "2style"
#    For example: cd /workspace/SimpleTuner/output/1subject/tom/01
# 3. Run the script with: /workspace/rename-models.sh
# ===============================

set -e  # Exit immediately if a command exits with a non-zero status.

# Get the current path (assumed to be the model version path)
current_path=$(pwd)
echo "Current path: $current_path"

# Extract the model version from the current path
model_version=$(basename "$current_path")
echo "Model version: $model_version"

# Extract the model name from the parent directory of the current path
model_name=$(basename "$(dirname "$current_path")")
echo "Model name: $model_name"

# Extract the MODEL_TYPE from the grandparent directory of the current path
model_type=$(basename "$(dirname "$(dirname "$current_path")")")
echo "Model type: $model_type"

# Validate MODEL_TYPE
if [[ "$model_type" != "1subject" && "$model_type" != "2style" ]]; then
    echo "Error: Invalid MODEL_TYPE. Must be either '1subject' or '2style'."
    exit 1
fi

# New base path for copying files
base_copy_path="/workspace/StableSwarmUI/Models/Lora"
echo "Base copy path: $base_copy_path"

# Function to process each safetensor file
process_file() {
    local file="$1"
    local subfolder=$(basename "$(dirname "$file")")
    
    # Extract step count
    local stepcount=${subfolder#checkpoint-}
    if [[ ! "$stepcount" =~ ^[0-9]+$ ]]; then
        echo "Error: Could not extract valid step count from subfolder name: $subfolder"
        return 1
    fi
    
    # Remove leading zeros and pad to 4 digits
    stepcount=$(echo "$stepcount" | sed 's/^0*//')
    local padded_stepcount=$(printf "%04d" "$stepcount")
    
    local new_name="${model_name}-${model_version}-${padded_stepcount}.safetensors"
    echo "Processing file: $file"
    echo "Subfolder: $subfolder"
    echo "Step count: $stepcount"
    echo "Padded step count: $padded_stepcount"
    echo "New name: $new_name"
    
    # Create the directory structure if it doesn't exist
    local copy_dir="${base_copy_path}/${model_type}/${model_name}/${model_version}"
    mkdir -p "$copy_dir"
    echo "Created directory (if it didn't exist): $copy_dir"
    
    # Copy the file to the new directory with the new name
    cp "$file" "$copy_dir/$new_name"
    echo "Copied to: $copy_dir/$new_name"
    echo "---"
}

echo "Searching for pytorch_lora_weights.safetensors files in subfolders..."
# Find all pytorch_lora_weights.safetensors files in immediate subfolders and process them
find "$current_path" -mindepth 2 -maxdepth 2 -name "pytorch_lora_weights.safetensors" -type f | while read -r file; do
    process_file "$file"
done

# Copy validation_images folder
validation_images_src="$current_path/validation_images"
validation_images_dest="${base_copy_path}/${model_type}/${model_name}/${model_version}/validation_images"
if [ -d "$validation_images_src" ]; then
    echo "Copying validation_images folder..."
    cp -r "$validation_images_src" "$validation_images_dest"
    echo "Copied validation_images to: $validation_images_dest"
else
    echo "Warning: validation_images folder not found in $current_path"
fi

# Copy JSON files from base path
echo "Copying JSON files from base path..."
find "$current_path" -maxdepth 1 -name "*.json" -type f | while read -r json_file; do
    json_filename=$(basename "$json_file")
    json_dest="${base_copy_path}/${model_type}/${model_name}/${model_version}/${json_filename}"
    cp "$json_file" "$json_dest"
    echo "Copied JSON file: $json_filename to $json_dest"
done

echo "Processing complete."