#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def log(message):
    print(f"[ICON] {message}")

def get_icon_choice():
    """Get icon choice from environment with validation"""
    icon_choice = os.getenv('ICON_CHOICE', 'default').lower()
    valid_choices = ['default', 'alternative', 'modern']
    
    if icon_choice not in valid_choices:
        log(f"Invalid icon choice '{icon_choice}', using 'default'")
        return 'default'
    
    return icon_choice

def update_app_icon(icon_choice):
    """Update app icon based on user choice"""
    try:
        # Define source and destination directories
        icons_source_dir = Path("app_icons")
        main_res_dir = Path("app/src/main/res")
        
        # Check if icons directory exists
        if not icons_source_dir.exists():
            log(f"Icons directory not found: {icons_source_dir}")
            return False
        
        # Map icon choices to directory names
        icon_dirs = {
            'default': 'default_icon',
            'alternative': 'alternative_icon', 
            'modern': 'modern_icon'
        }
        
        chosen_icon_dir = icons_source_dir / icon_dirs[icon_choice]
        
        if not chosen_icon_dir.exists():
            log(f"Chosen icon directory not found: {chosen_icon_dir}")
            log(f"Available icons: {list(icon_dirs.keys())}")
            return False
        
        log(f"Updating app icon with: {icon_choice}")
        log(f"Source: {chosen_icon_dir}")
        log(f"Destination: {main_res_dir}")
        
        # Copy all drawable resources from chosen icon to main res directory
        copied_files = 0
        for drawable_file in chosen_icon_dir.rglob('*.png'):
            if drawable_file.is_file():
                # Get relative path from icon directory
                rel_path = drawable_file.relative_to(chosen_icon_dir)
                dest_path = main_res_dir / rel_path
                
                # Create destination directory if it doesn't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the icon file
                shutil.copy2(drawable_file, dest_path)
                copied_files += 1
                log(f"Copied: {rel_path}")
        
        log(f"Successfully updated {copied_files} icon files")
        return True
        
    except Exception as e:
        log(f"Error updating app icon: {e}")
        return False

def main():
    log("Starting app icon update...")
    
    icon_choice = get_icon_choice()
    log(f"Selected icon: {icon_choice}")
    
    success = update_app_icon(icon_choice)
    
    if success:
        log("App icon update completed successfully")
        return 0
    else:
        log("App icon update completed with warnings - using default icons")
        return 0  # Don't fail the build if icons can't be updated

if __name__ == "__main__":
    exit(main())
