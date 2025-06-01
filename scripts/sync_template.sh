#!/bin/bash

# Prompta Template Synchronization Script
# Syncs files from ./prompta-app to ./prompta-cli/prompta/templates/api/

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -d "./prompta-app" ]; then
    print_error "Source directory './prompta-app' not found. Please run this script from the project root."
    exit 1
fi

# Define source and target directories
SOURCE_DIR="./prompta-app"
TARGET_DIR="./prompta-cli/prompta/templates/api"

print_status "Starting template synchronization..."
print_status "Source: $SOURCE_DIR"
print_status "Target: $TARGET_DIR"

# Create target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    print_status "Creating target directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

# List of directories to sync
DIRECTORIES=(
    "app"
    "auth"
    "migrations"
    "models"
    "prompts"
    "tests"
)

# List of files to sync
FILES=(
    ".env.example"
    ".gitignore"
    "alembic.ini"
    "README.md"
    "docker-compose.yml"
    "Dockerfile"
)

# List of files to preserve in target directory (don't overwrite)
PRESERVE_FILES=(
    "requirements.txt"
)

# Function to copy directory
copy_directory() {
    local dir_name="$1"
    local source_path="$SOURCE_DIR/$dir_name"
    local target_path="$TARGET_DIR/$dir_name"
    
    if [ -d "$source_path" ]; then
        print_status "Syncing directory: $dir_name"
        
        # Create target directory if it doesn't exist
        mkdir -p "$target_path"
        
        # Backup preserved files if they exist in target
        local backup_dir="/tmp/prompta_backup_$$"
        local has_preserved_files=false
        
        for preserve_file in "${PRESERVE_FILES[@]}"; do
            local preserve_path="$target_path/$preserve_file"
            if [ -f "$preserve_path" ]; then
                if [ "$has_preserved_files" = false ]; then
                    mkdir -p "$backup_dir"
                    has_preserved_files=true
                fi
                print_status "Backing up preserved file: $preserve_file"
                cp "$preserve_path" "$backup_dir/"
            fi
        done
        
        # Remove target directory contents (but not the directory itself)
        if [ -d "$target_path" ]; then
            rm -rf "$target_path"/*
        fi
        
        # Copy directory contents recursively
        cp -r "$source_path"/* "$target_path"/ 2>/dev/null || true
        
        # Restore preserved files if they were backed up
        if [ "$has_preserved_files" = true ]; then
            for preserve_file in "${PRESERVE_FILES[@]}"; do
                local backup_file="$backup_dir/$preserve_file"
                if [ -f "$backup_file" ]; then
                    print_status "Restoring preserved file: $preserve_file"
                    cp "$backup_file" "$target_path/"
                fi
            done
            # Clean up backup directory
            rm -rf "$backup_dir"
        fi
        
        print_success "Directory '$dir_name' synced successfully (preserved files retained)"
    else
        print_warning "Source directory '$dir_name' not found, skipping..."
    fi
}

# Function to copy file
copy_file() {
    local file_name="$1"
    local source_path="$SOURCE_DIR/$file_name"
    local target_path="$TARGET_DIR/$file_name"
    
    if [ -f "$source_path" ]; then
        print_status "Syncing file: $file_name"
        
        # Create target directory if needed
        local target_dir=$(dirname "$target_path")
        mkdir -p "$target_dir"
        
        # Copy the file
        cp "$source_path" "$target_path"
        print_success "File '$file_name' synced successfully"
    else
        print_warning "Source file '$file_name' not found in $SOURCE_DIR, skipping..."
        
        # Check if the file exists in target (might be template-specific)
        if [ -f "$target_path" ]; then
            print_status "File '$file_name' already exists in target, keeping existing version"
        fi
    fi
}

# Sync directories
print_status "Syncing directories..."
for dir in "${DIRECTORIES[@]}"; do
    copy_directory "$dir"
done

echo ""

# Sync files
print_status "Syncing files..."
for file in "${FILES[@]}"; do
    copy_file "$file"
done

echo ""

# Create README.md.template if README.md exists
if [ -f "$SOURCE_DIR/README.md" ]; then
    print_status "Creating README.md.template from README.md"
    cp "$SOURCE_DIR/README.md" "$TARGET_DIR/README.md.template"
    print_success "README.md.template created successfully"
fi

# Set permissions
print_status "Setting proper permissions..."
find "$TARGET_DIR" -type f -name "*.py" -exec chmod 644 {} \;
find "$TARGET_DIR" -type d -exec chmod 755 {} \;

# Summary
print_success "Template synchronization completed successfully!"
print_status "Files have been synced from '$SOURCE_DIR' to '$TARGET_DIR'"

# List what was synced
echo ""
print_status "Synced content:"
if [ -d "$TARGET_DIR" ]; then
    ls -la "$TARGET_DIR"
else
    print_error "Target directory was not created properly"
    exit 1
fi

echo ""
print_success "All done! The template is now ready for use."
