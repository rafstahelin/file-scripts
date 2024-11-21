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
   # List directories matching the pattern but exclude lora and lokr
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
   # Change to datasets directory
   pushd /workspace/SimpleTuner/datasets > /dev/null || exit 1
   for folder in */; do
       if [ -d "$folder" ]; then
           folder=${folder%/}  # Remove trailing slash
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
   # Get sorted list of datasets and select the chosen one
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

# Main script
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
       
       # Ask about dataset
       read -n1 -p "Use same dataset? (y/n): " same_dataset
       echo
       if [[ $same_dataset != [yY] ]]; then
           get_dataset_choice
       else
           # Extract current dataset from source config
           DATASET_DIR=$(grep -o '"instance_data_dir": "[^"]*"' "$SOURCE_DIR/multidatabackend.json" | grep -o 'datasets/[^"]*' | sed 's|datasets/||')
           print_color "32" "Using existing dataset: $DATASET_DIR"
       fi
       
       # Make sure we have a token name and version
       if [ -z "$TOKEN_NAME" ] || [ -z "$NEW_VERSION" ]; then
           print_color "31" "Error: Could not determine token name or version"
           exit 1
       fi
       TOKEN_NAME_VERSION="${TOKEN_NAME}-${NEW_VERSION}"
       print_color "36" "Creating new folder: $TOKEN_NAME_VERSION"
       ;;
   2)
       SOURCE_DIR="lora"
       read -p "Enter new token name: " TOKEN_NAME
       read -p "Enter version number: " NEW_VERSION
       TOKEN_NAME_VERSION="${TOKEN_NAME}-${NEW_VERSION}"
       get_dataset_choice
       ;;
   3)
       SOURCE_DIR="lokr"
       read -p "Enter new token name: " TOKEN_NAME
       read -p "Enter version number: " NEW_VERSION
       TOKEN_NAME_VERSION="${TOKEN_NAME}-${NEW_VERSION}"
       get_dataset_choice
       ;;
   *)
       print_color "31" "Invalid choice. Exiting."
       exit 1
       ;;
esac

print_color "36" "\nProcessing with following parameters:"
print_color "33" "Source Directory: $SOURCE_DIR"
print_color "33" "Token Name: $TOKEN_NAME"
print_color "33" "New Version: $NEW_VERSION"
print_color "33" "New Folder Name: $TOKEN_NAME_VERSION"
print_color "33" "Dataset: $DATASET_DIR"

# Modified confirmation prompt for immediate response
read -n1 -p "Proceed? (y/n): " confirm
echo    # add a newline after response
case $confirm in
   [yY]) 
       ;;
   *)
       print_color "31" "\nOperation cancelled."
       exit 1
       ;;
esac

# Show progress bar while copying
print_color "36" "\nCopying files..."
show_progress 0.01

# Copy directory
if [ ! -d "$SOURCE_DIR" ]; then
   print_color "31" "Error: Source directory '$SOURCE_DIR' does not exist."
   exit 1
fi

# Copy the source directory to the new directory
rsync -av --exclude='.ipynb_checkpoints' "$SOURCE_DIR/" "$TOKEN_NAME_VERSION/"

# Change to the new directory
cd "$TOKEN_NAME_VERSION" || exit 1

print_color "36" "\nUpdating configuration files..."
show_progress 0.02

# Replace placeholders in config.json
if [ -f "config.json" ]; then
   # First update paths with current folder structure
   sed -i \
   -e 's|config/[^/"]*/|config/'"$TOKEN_NAME_VERSION"'/|g' \
   -e 's|"output/[^/"]*/[^"]*"|"output/'"$TOKEN_NAME"'/'"$NEW_VERSION"'"|g' config.json
   
   # Then handle any remaining token replacements
   sed -i \
   -e 's|__TOKEN_NAME__|'"$TOKEN_NAME"'|g' \
   -e 's|__TOKEN_NAME_VERSION__|'"$TOKEN_NAME_VERSION"'|g' \
   -e 's|__VERSION_NUMBER__|'"$NEW_VERSION"'|g' config.json

   print_color "32" "Updated config.json"
else
   print_color "33" "Warning: config.json not found in $TOKEN_NAME_VERSION"
fi

# Replace placeholders in multidatabackend.json
if [ -f "multidatabackend.json" ]; then
   # Update dataset path with precise pattern matching
   sed -i \
   -e 's|\("instance_data_dir":[[:space:]]*"\)[^"]*\(".*\)|\1datasets/'"$DATASET_DIR"'\2|g' multidatabackend.json
   print_color "32" "Updated multidatabackend.json with dataset: $DATASET_DIR"
else
   print_color "33" "Warning: multidatabackend.json not found in $TOKEN_NAME_VERSION"
fi

# Replace placeholders in user_prompt_library.json
if [ -f "user_prompt_library.json" ]; then
   sed -i 's/__TOKEN_NAME__/'"$TOKEN_NAME"'/g' user_prompt_library.json
   print_color "32" "Updated user_prompt_library.json"
else
   print_color "33" "Warning: user_prompt_library.json not found in $TOKEN_NAME_VERSION"
fi

cd ..

print_color "32" "\nOperation completed successfully!"
print_color "36" "\nCreated new configuration in: $TOKEN_NAME_VERSION"