import os
import shutil
from pathlib import Path

def move_matching_text_files(images_folder, labels_folder):
    """
    Find all image files in the images folder, then search for matching text files
    in the labels folder and move them to the images folder.
    
    Supported image formats: .jpg, .jpeg, .png, .bmp, .tiff
    Text files should have the same base name as the image files.
    
    Args:
        images_folder (str): Path to folder containing image files
        labels_folder (str): Path to folder containing text label files
    
    Returns:
        dict: Summary of the operation with counts and file lists
    """
    # Convert to Path objects for easier handling
    images_path = Path(images_folder)
    labels_path = Path(labels_folder)
    
    # Check if folders exist
    if not images_path.exists():
        raise FileNotFoundError(f"Images folder not found: {images_folder}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels folder not found: {labels_folder}")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # Find all image files
    image_files = []
    for file_path in images_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    print(f"🔍 Found {len(image_files)} image files in {images_folder}")
    
    # Statistics
    moved_count = 0
    not_found_count = 0
    already_exists_count = 0
    moved_files = []
    not_found_files = []
    
    # Process each image file
    for image_file in image_files:
        # Get the base name without extension
        base_name = image_file.stem
        
        # Try multiple naming patterns for text files
        text_file = None
        
        # First try: exact match (Images (1234).txt)
        text_file = labels_path / f"{base_name}.txt"
        
        # Second try: convert "Images (1234)" -> "Image (1234)"
        if not text_file.exists() and base_name.startswith("Images ("):
            text_base_name = base_name.replace("Images (", "Image (", 1)
            text_file = labels_path / f"{text_base_name}.txt"
            
        # Third try: convert "Image (1234)" -> "Images (1234)" (reverse)
        if not text_file.exists() and base_name.startswith("Image ("):
            text_base_name = base_name.replace("Image (", "Images (", 1)
            text_file = labels_path / f"{text_base_name}.txt"
        
        if text_file.exists():
            # Check if text file already exists in images folder
            dest_text_file = images_path / f"{base_name}.txt"
            
            if dest_text_file.exists():
                print(f"⚠️  Text file already exists: {base_name}.txt")
                already_exists_count += 1
            else:
                # Move the text file to images folder
                shutil.move(str(text_file), str(dest_text_file))
                moved_count += 1
                moved_files.append(base_name)
                print(f"✅ Moved: {base_name}.txt")
        else:
            print(f"❌ No text file found for: {image_file.name}")
            not_found_count += 1
            not_found_files.append(image_file.name)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   ✅ Moved: {moved_count} text files")
    print(f"   ⚠️  Already existed: {already_exists_count} text files")
    print(f"   ❌ Not found: {not_found_count} text files")
    print(f"   📁 Total images processed: {len(image_files)}")
    
    return {
        "moved_count": moved_count,
        "already_exists_count": already_exists_count,
        "not_found_count": not_found_count,
        "total_images": len(image_files),
        "moved_files": moved_files,
        "not_found_files": not_found_files
    }

def main():
    """Main function to run the text file moving operation."""
    # Define the folders
    images_folder = "data/images/temp vald"
    labels_folder = "data/images/temp vald labels"
    
    print("🚀 Starting text file matching and moving process...")
    print(f"📁 Images folder: {images_folder}")
    print(f"📁 Labels folder: {labels_folder}")
    print("-" * 50)
    
    try:
        results = move_matching_text_files(images_folder, labels_folder)
        
        if results["moved_count"] > 0:
            print(f"\n🎉 Successfully moved {results['moved_count']} text files!")
        else:
            print("\n⚠️  No text files were moved.")
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
