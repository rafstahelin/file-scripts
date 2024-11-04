#!/bin/bash

# This script:
# 1. Reads a config file with key-value pairs (folder patterns and Dropbox paths).
# 2. Searches for local folders matching these patterns in /workspace/SimpleTuner/config.
# 3. Uses rclone to copy entire folders to their corresponding Dropbox paths, excluding .ipynb_checkpoints.
# 4. Displays progress with visual separators and waits for each rclone process to finish before starting the next.

# Fixed paths
CONFIG_FILE="/workspace/rclone_config.yaml"
BASE_PATH="/workspace/SimpleTuner/config"

# ANSI color codes
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print colored progress
print_progress() {
    local current=$1
    local total=$2
    local prefix=$3
    local suffix=$4
    local length=50
    local filled=$(printf "%.0f" $(echo "scale=2; $current/$total*$length" | bc))
    local empty=$((length - filled))
    
    printf "\r${GREEN}${prefix}${NC}["
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' ' '
    printf "] ${GREEN}${suffix}${NC}"
}

# Function to print separator
print_separator() {
    local text="$1"
    local width=80
    local padding=$(( (width - ${#text} - 2) / 2 ))
    local line=$(printf '%*s' "$width" | tr ' ' '|')
    
    echo -e "${GREEN}$line"
    printf "${GREEN}|%*s%s%*s|${NC}\n" $padding "" "$text" $padding ""
    echo -e "${GREEN}$line${NC}"
}

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at $CONFIG_FILE"
    echo "Please ensure the config file is present at /workspace/rclone_config.yaml"
    echo "The config file should contain key-value pairs of folder patterns and Dropbox paths."
    exit 1
fi

# Read configuration file
mapfile -t config_lines < "$CONFIG_FILE"

# Count total number of entries
total_entries=${#config_lines[@]}

# Process each line in the configuration file
for ((i=0; i<${#config_lines[@]}; i++)); do
    line="${config_lines[$i]}"
    key=$(echo "$line" | cut -d':' -f1 | tr -d ' ')
    value=$(echo "$line" | cut -d':' -f2- | tr -d '"' | tr -d ' ')
    
    echo -e "\n"
    print_separator "Processing config entry: $key"
    
    # Find matching subfolders
    matching_folders=$(find "$BASE_PATH" -type d -name "${key}*")
    
    # Process each matching folder
    while IFS= read -r folder; do
        if [ -n "$folder" ]; then
            folder_name=$(basename "$folder")
            destination_path="${value}/${folder_name}"
            print_separator "Processing: $folder_name"
            echo "Source folder: $folder"
            echo "Destination path: $destination_path"
            
            # Run rclone command to copy the entire folder, excluding .ipynb_checkpoints
            rclone copy --checksum "$folder" "$destination_path" -v -P --ignore-existing --exclude ".ipynb_checkpoints/**" &
            
            # Get PID of the rclone process
            rclone_pid=$!
            
            # Wait for rclone to finish while showing progress
            start_time=$(date +%s)
            while kill -0 $rclone_pid 2>/dev/null; do
                current_time=$(date +%s)
                elapsed=$((current_time - start_time))
                print_progress $((i+1)) $total_entries "Progress: " "Elapsed: ${elapsed}s"
                sleep 1
            done
            echo -e "\nCompleted: $folder"
        fi
    done <<< "$matching_folders"
done

print_separator "All operations completed"