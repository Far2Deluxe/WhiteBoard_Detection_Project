import os
import shutil
from pathlib import Path
from ultralytics import YOLO

def classify_and_organize_whiteboards(
    photos_folder, 
    model_path, 
    confidence_threshold=0.5,
    create_whiteboard_folder=True
):
    """
    Use a YOLO classification model to detect whiteboards in photos and organize them.
    
    Args:
        photos_folder (str): Path to folder containing photos to test
        model_path (str): Path to trained YOLO classification model (.pt file)
        confidence_threshold (float): Minimum confidence to classify as whiteboard (0.0-1.0)
        create_whiteboard_folder (bool): Whether to create a 'whiteboards' subfolder
    
    Returns:
        dict: Summary statistics of the classification and organization
    """
    # Convert to Path objects
    photos_path = Path(photos_folder)
    
    # Check if photos folder exists
    if not photos_path.exists():
        raise FileNotFoundError(f"Photos folder not found: {photos_folder}")
    
    # Check if model file exists
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    # Load YOLO classification model
    print(f"🔄 Loading YOLO classification model from: {model_path}")
    model = YOLO(model_path)
    
    # Create whiteboards folder if requested
    whiteboards_folder = None
    if create_whiteboard_folder:
        whiteboards_folder = photos_path / "whiteboards"
        whiteboards_folder.mkdir(exist_ok=True)
        print(f"📁 Created whiteboards folder: {whiteboards_folder}")
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    # Find all image files
    image_files = []
    for file_path in photos_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    print(f"🔍 Found {len(image_files)} image files to process")
    print(f"🎯 Confidence threshold: {confidence_threshold}")
    print("-" * 60)
    
    # Statistics
    whiteboard_count = 0
    non_whiteboard_count = 0
    error_count = 0
    whiteboard_files = []
    non_whiteboard_files = []
    error_files = []
    
    # Process each image
    for i, image_file in enumerate(image_files, 1):
        try:
            print(f"[{i}/{len(image_files)}] Processing: {image_file.name}")
            
            # Run classification
            results = model.predict(str(image_file), verbose=False)
            
            # Get prediction results
            probs = results[0].probs.data.cpu().numpy()
            class_names = results[0].names
            predicted_class = class_names[probs.argmax()]
            confidence = probs.max()
            
            print(f"   📊 Prediction: {predicted_class} (confidence: {confidence:.3f})")
            
            # Check if it's classified as whiteboard with sufficient confidence
            is_whiteboard = (predicted_class.lower() in ['whiteboard', 'whiteboards', '0'] and 
                           confidence >= confidence_threshold)
            
            if is_whiteboard:
                whiteboard_count += 1
                whiteboard_files.append(image_file.name)
                
                if create_whiteboard_folder:
                    # Move to whiteboards folder
                    dest_path = whiteboards_folder / image_file.name
                    shutil.move(str(image_file), str(dest_path))
                    print(f"   ✅ WHITEBOARD DETECTED → Moved to whiteboards folder")
                else:
                    print(f"   ✅ WHITEBOARD DETECTED → Keeping in place")
            else:
                non_whiteboard_count += 1
                non_whiteboard_files.append(image_file.name)
                print(f"   ❌ Not a whiteboard → Keeping in place")
                
        except Exception as e:
            error_count += 1
            error_files.append(image_file.name)
            print(f"   ⚠️  ERROR processing {image_file.name}: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 CLASSIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Whiteboards detected: {whiteboard_count}")
    print(f"❌ Non-whiteboards: {non_whiteboard_count}")
    print(f"⚠️  Errors: {error_count}")
    print(f"📁 Total processed: {len(image_files)}")
    
    if create_whiteboard_folder and whiteboard_count > 0:
        print(f"📂 Whiteboards moved to: {whiteboards_folder}")
    
    # Show some examples
    if whiteboard_files:
        print(f"\n🎯 Sample whiteboard files detected:")
        for file in whiteboard_files[:5]:  # Show first 5
            print(f"   • {file}")
        if len(whiteboard_files) > 5:
            print(f"   ... and {len(whiteboard_files) - 5} more")
    
    return {
        "total_images": len(image_files),
        "whiteboard_count": whiteboard_count,
        "non_whiteboard_count": non_whiteboard_count,
        "error_count": error_count,
        "whiteboard_files": whiteboard_files,
        "non_whiteboard_files": non_whiteboard_files,
        "error_files": error_files,
        "whiteboards_folder": str(whiteboards_folder) if create_whiteboard_folder else None
    }

def main():
    """Main function to run the whiteboard classification and organization."""
    
    # Configuration - MODIFY THESE PATHS AS NEEDED
    photos_folder = "test3"  # Folder with photos to test
    model_path = "src/models/Whiteboard Model Classification5/weights/best.pt"  # Path to your trained model
    
    # Optional: You can also try other model paths if the above doesn't exist
    alternative_models = [
        "src/models/Whiteboard Model Classification2/weights/best.pt",
        "src/models/Whiteboard Model Classification3/weights/best.pt",
        "yolov8n-cls.pt"  # Pre-trained model as fallback
    ]
    
    # Check if primary model exists, try alternatives if not
    if not Path(model_path).exists():
        print(f"⚠️  Primary model not found: {model_path}")
        print("🔍 Trying alternative models...")
        
        for alt_model in alternative_models:
            if Path(alt_model).exists():
                model_path = alt_model
                print(f"✅ Using alternative model: {model_path}")
                break
        else:
            print("❌ No suitable model found!")
            return
    
    # Configuration parameters
    confidence_threshold = 0.6  # Adjust this value (0.0-1.0) - higher = more strict
    create_whiteboard_folder = True  # Set to False if you don't want to move files
    
    print("🚀 Starting YOLO Whiteboard Classification and Organization")
    print(f"📁 Photos folder: {photos_folder}")
    print(f"🤖 Model: {model_path}")
    print(f"🎯 Confidence threshold: {confidence_threshold}")
    print(f"📂 Create whiteboard folder: {create_whiteboard_folder}")
    print("=" * 60)
    
    try:
        results = classify_and_organize_whiteboards(
            photos_folder=photos_folder,
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            create_whiteboard_folder=create_whiteboard_folder
        )
        
        # Final success message
        if results["whiteboard_count"] > 0:
            print(f"\n🎉 SUCCESS! Found and organized {results['whiteboard_count']} whiteboard images!")
        else:
            print(f"\n📝 No whiteboards detected with confidence >= {confidence_threshold}")
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
