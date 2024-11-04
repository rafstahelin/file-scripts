#!/bin/bash

# This script recursively searches for specific JSON config files in the current directory and its subdirectories.
# It renames these files by appending the parent directory name to the original filename.
# Usage: Place this script in the root directory containing your config folders and run it.

# Target files
declare -a target_files=("config.json" "multidatabackend.json" "user_prompt_library.json" "lycoris_config.json")

# Function to rename files in the specified directory
rename_files() {
    local dir="$1"
    local parent_dir=$(basename "$dir")
    
    echo "Processing folder: $dir"
    
    # Loop through the files in the directory
    for file in "$dir"/*.json; do
        if [[ -f "$file" ]]; then
            base_name=$(basename "$file")
            if [[ " ${target_files[@]} " =~ " $base_name " ]]; then
                # Extract the base name and rename the file by appending the parent directory name
                new_name="${dir}/${base_name%.*}-${parent_dir}.json"
                # Rename the file and print verbose output
                mv -v "$file" "$new_name"
                # Show success message
                if [ $? -eq 0 ]; then
                    echo "Renamed $file to $new_name successfully."
                else
                    echo "Error renaming $file in $dir."
                fi
            else
                # Print files that are not part of the target list
                echo "File '$file' is not a target file and was not processed."
            fi
        fi
    done
}

# Function to recursively process directories
process_directory() {
    local dir="$1"
    
    # Check if any of the target files exist in the current directory
    local found_target_file=false
    for target_file in "${target_files[@]}"; do
        if [ -f "$dir/$target_file" ]; then
            found_target_file=true
            break
        fi
    done
    
    if $found_target_file; then
        rename_files "$dir"
    else
        # If no target files found, recurse into subdirectories
        for subdir in "$dir"/*/; do
            if [ -d "$subdir" ]; then
                process_directory "$subdir"
            fi
        done
    fi
}

# Get the current directory path
current_dir=$(pwd)

# Notify the user that processing is starting
echo "Starting to process folders: please wait..."

# Start processing from the current directory
process_directory "$current_dir"

echo "Processing complete."