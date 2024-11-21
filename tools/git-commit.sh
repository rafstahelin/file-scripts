#!/bin/bash
# Save as git-commit-workflow.sh

# Function to check git status and show changes
check_status() {
    echo "Current git status:"
    git status
    
    echo -e "\nChanges to be committed:"
    git diff --cached --name-status
    
    echo -e "\nUntracked/modified files:"
    git diff --name-status
}

# Function to commit and push
commit_and_push() {
    local message="$1"
    local branch="$2"
    
    # Stage all changes
    git add .
    
    # Show what will be committed
    check_status
    
    # Confirm commit
    read -p "Proceed with commit? (y/n): " confirm
    if [[ $confirm != "y" ]]; then
        echo "Aborting commit."
        return 1
    fi
    
    # Commit with message
    git commit -m "$message"
    
    # Push to remote
    echo "Pushing to origin/$branch..."
    git push origin "$branch"
}

# Main execution
echo "=== Git Commit and Push Workflow ==="

# Get current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Show status
check_status

# Get commit message
read -p "Enter commit message: " message

# Execute commit and push
commit_and_push "$message" "$current_branch"