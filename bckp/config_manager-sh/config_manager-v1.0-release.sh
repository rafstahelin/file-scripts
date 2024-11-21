#!/bin/bash

# Function for colored output
print_color() {
    local color=$1
    shift
    echo -e "\e[${color}m$@\e[0m"
}

# Function to show rainbow progress bar
show_progress() {
    local duration=$1
    local cols=$(($(tput cols) - 10))
    local progress=0
    local colors=(31 33 32 36 34 35)

    while [ $progress -le $cols ]; do
        let color_index=$progress%${#colors[@]}
        printf "\r["
        for ((i=0; i<$cols; i++)); do
            if [ $i -lt $progress ]; then
                printf "\e[${colors[$color_index]}m#\e[0m"
            else
                printf " "
            fi
        done
        printf "] %d%%" $(( (progress * 100) / cols ))
        sleep $duration
        let progress++
    done
    echo
}

# Function to list existing folders
list_folders() {
    local count=1
    print_color "36" "\nExisting folders:"
    for folder in *; do
        if [ -d "$folder" ] && [ "$folder" != "lora" ] && [ "$folder" != "lokr" ]; then
            print_color "33" "$count. $folder"
            let count++
        fi
    done
}

# Function to list available datasets
list_datasets() {
    local count=1
    print_color "36" "\nAvailable datasets:"
    pushd /workspace/SimpleTuner/datasets > /dev/null || exit 1
    for folder in */; do
        if [ -d "$folder" ]; then
            folder=${folder%/}
            print_color "33" "$count. $folder"
            let count++
        fi
    done
    popd > /dev/null || return
}

# Function to get dataset selection
get_dataset_choice() {
    list_datasets
    read -p "Enter dataset number: " dataset_num
    DATASET_DIR=$(find /workspace/SimpleTuner/datasets -maxdepth 1 -type d ! -name "datasets" ! -name ".*" -printf "%f\n" | sort | sed -n "${dataset_num}p")
    if [ -z "$DATASET_DIR" ]; then
        print_color "31" "Invalid dataset selection"
        exit 1
    fi
    print_color "32" "Selected dataset: $DATASET_DIR"
}

# Function to parse folder name
parse_folder_name() {
    local folder=$1
    TOKEN_NAME=$(echo $folder | cut -d'-' -f1)
    VERSION_NUMBER=$(echo $folder | cut -d'-' -f2-)
}

# Function to sanitize names for cache directories
sanitize_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | tr -s '-'
}

# Function to extract dataset name from existing config
extract_dataset_name() {
    local config_file=$1
    # Extract just the dataset name without path components and duplicates
    local dataset=$(grep -o '"instance_data_dir":[[:space:]]*"[^"]*"' "$config_file" | 
                   head -1 | 
                   grep -o '[^/"]*"$' | 
                   tr -d '"')
    echo "$dataset"
}

# Main script starts here
clear
print_color "35" "=== Configuration Folder Management Tool ==="
print_color "36" "\nSelect source folder type:"
print_color "33" "1. Use existing folder"
print_color "33" "2. Use 'lora' template"
print_color "33" "3. Use 'lokr' template"

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        list_folders
        read -p "Enter number to select source folder: " folder_num
        SOURCE_DIR=$(find . -maxdepth 1 -type d ! -name "lora" ! -name "lokr" ! -name ".*" -printf "%f\n" | sort | sed -n "${folder_num}p")
        if [ -z "$SOURCE_DIR" ]; then
            print_color "31" "Invalid selection"
            exit 1
        fi
        parse_folder_name "$SOURCE_DIR"
        print_color "32" "Selected folder: $SOURCE_DIR"
        read -p "Enter new version number: " NEW_VERSION
        
        read -n1 -p "Use same dataset? (y/n): " same_dataset
        echo
        if [[ $same_dataset != [yY] ]]; then
            get_dataset_choice
        else
            DATASET_DIR=$(extract_dataset_name "$SOURCE_DIR/multidatabackend.json")
            print_color "32" "Using existing dataset: $DATASET_DIR"
        fi
        ;;
    2)
        SOURCE_DIR="lora"
        read -p "Enter new token name: " TOKEN_NAME
        read -p "Enter version number: " NEW_VERSION
        get_dataset_choice
        ;;
    3)
        SOURCE_DIR="lokr"
        read -p "Enter new token name: " TOKEN_NAME
        read -p "Enter version number: " NEW_VERSION
        get_dataset_choice
        ;;
    *)
        print_color "31" "Invalid choice. Exiting."
        exit 1
        ;;
esac

TOKEN_NAME_VERSION="${TOKEN_NAME}-${NEW_VERSION}"

print_color "36" "\nProcessing with following parameters:"
print_color "33" "Source Directory: $SOURCE_DIR"
print_color "33" "Token Name: $TOKEN_NAME"
print_color "33" "New Version: $NEW_VERSION"
print_color "33" "New Folder Name: $TOKEN_NAME_VERSION"
print_color "33" "Dataset: $DATASET_DIR"

read -n1 -p "Proceed? (y/n): " confirm
echo
[[ $confirm != [yY] ]] && { print_color "31" "\nOperation cancelled."; exit 1; }

print_color "36" "\nCopying files..."
show_progress 0.01

[[ ! -d "$SOURCE_DIR" ]] && { print_color "31" "Error: Source directory '$SOURCE_DIR' does not exist."; exit 1; }

rsync -av --exclude='.ipynb_checkpoints' "$SOURCE_DIR/" "$TOKEN_NAME_VERSION/"

print_color "36" "\nUpdating configuration files..."
show_progress 0.02

# Create sanitized names for cache directories
SANITIZED_TOKEN=$(sanitize_name "$TOKEN_NAME")
SANITIZED_DATASET=$(sanitize_name "$DATASET_DIR")
BASE_CACHE_PATH="${SANITIZED_TOKEN}-${SANITIZED_DATASET}"
VAE_CACHE_DIR="cache/vae/${BASE_CACHE_PATH}"
TEXT_CACHE_DIR="cache/text/${BASE_CACHE_PATH}"

# Update multidatabackend.json
if [ -f "${TOKEN_NAME_VERSION}/multidatabackend.json" ]; then
    if command -v jq >/dev/null 2>&1; then
        # Use jq if available
        tmp_file=$(mktemp)
        jq --arg ds "$DATASET_DIR" \
           --arg cv "$VAE_CACHE_DIR" \
           --arg ct "$TEXT_CACHE_DIR" \
           --arg tn "$TOKEN_NAME" \
           --arg id "1024" '
        walk(
            if type == "object" then
                if .id == "text_embeds" then
                    .cache_dir = $ct |
                    del(.instance_data_dir) |
                    del(.cache_dir_vae)
                elif .id == $id then
                    .instance_data_dir = "datasets/\($ds)" |
                    .cache_dir_vae = "\($cv)/\($id)"
                elif .id == "768" or .id == "512" then
                    .instance_data_dir = "datasets/\($ds)" |
                    .cache_dir_vae = "\($cv)/\(.id)"
                else
                    .
                end
            else
                .
            end
        )' "${TOKEN_NAME_VERSION}/multidatabackend.json" > "$tmp_file"
        mv "$tmp_file" "${TOKEN_NAME_VERSION}/multidatabackend.json"
    else
        # Clean existing paths first
        sed -i \
            -e 's|"datasets/[^"]*"|"datasets/'"$DATASET_DIR"'"|g' \
            -e 's|"cache/vae/[^"]*"|"'"$VAE_CACHE_DIR"'/1024"|g' \
            "${TOKEN_NAME_VERSION}/multidatabackend.json"

        # Update text_embeds section
        sed -i '/"id"[[:space:]]*:[[:space:]]*"text_embeds"/,/^[[:space:]]*}/{
            s|"cache_dir":[[:space:]]*"[^"]*"|"cache_dir": "'"$TEXT_CACHE_DIR"'"|g
            /[[:space:]]*"instance_data_dir":/d
            /[[:space:]]*"cache_dir_vae":/d
        }' "${TOKEN_NAME_VERSION}/multidatabackend.json"
    fi
    print_color "32" "Updated multidatabackend.json"
fi

# Update config.json
if [ -f "${TOKEN_NAME_VERSION}/config.json" ]; then
    sed -i \
        -e 's|__TOKEN_NAME__|'"$TOKEN_NAME"'|g' \
        -e 's|__TOKEN_NAME_VERSION__|'"$TOKEN_NAME_VERSION"'|g' \
        -e 's|__VERSION_NUMBER__|'"$NEW_VERSION"'|g' \
        -e 's|\(--[^"]*\)"|\1 "|g' \
        "${TOKEN_NAME_VERSION}/config.json"
    print_color "32" "Updated config.json"
fi

# Update user_prompt_library.json
if [ -f "${TOKEN_NAME_VERSION}/user_prompt_library.json" ]; then
    sed -i \
        -e 's|"long__'"$TOKEN_NAME"'_"|"long_'"$TOKEN_NAME"'"|g' \
        -e 's|"basictokens__'"$TOKEN_NAME"'_"|"basictokens_'"$TOKEN_NAME"'"|g' \
        -e 's|"token__'"$TOKEN_NAME"'_"|"token_'"$TOKEN_NAME"'"|g' \
        -e 's|__'"$TOKEN_NAME"'_|'"$TOKEN_NAME"'|g' \
        -e 's|_'"$TOKEN_NAME"'_|'"$TOKEN_NAME"'|g' \
        -e 's|_TOKEN_NAME_|'"$TOKEN_NAME"'|g' \
        -e 's|_TOKEN_NAME_VERSION_|'"$TOKEN_NAME_VERSION"'|g' \
        "${TOKEN_NAME_VERSION}/user_prompt_library.json"
    print_color "32" "Updated user_prompt_library.json"
fi

print_color "32" "\nOperation completed successfully!"
print_color "36" "\nCreated new configuration in: $TOKEN_NAME_VERSION"