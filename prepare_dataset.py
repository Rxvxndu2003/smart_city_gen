#!/usr/bin/env python3
"""
Dataset Preparation Script for ML Training
Helps convert 3D house images into training data

Usage:
    python prepare_dataset.py --input-dir ./house_images --output-dir ./prepared_dataset
"""

import os
import sys
from pathlib import Path
import argparse
from PIL import Image
import json

def create_simple_floor_plan(house_image_path: Path, output_path: Path):
    """
    Create a simplified floor plan representation from a 3D house image.
    This is a placeholder - you should provide actual floor plans.
    """
    print(f"Processing: {house_image_path.name}")
    
    # Load the 3D house image
    img = Image.open(house_image_path)
    
    # Convert to grayscale and apply edge detection (simple floor plan approximation)
    # NOTE: This is just a placeholder. Ideally, you should have actual floor plans!
    img_gray = img.convert('L')
    
    # Save as floor plan
    img_gray.save(output_path)
    print(f"  → Created floor plan: {output_path.name}")
    
    return True

def organize_dataset(input_dir: str, output_dir: str):
    """
    Organize house images into dataset structure.
    
    Expected input structure:
        input_dir/
            house1.jpg (or .png)
            house2.jpg
            house3.jpg
            ...
    
    Creates output structure:
        output_dir/
            sample_001/
                floor_plan.png (you need to provide this)
                house_3d.jpg (original 3D image)
                metadata.json
            sample_002/
                ...
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    house_images = []
    
    for ext in image_extensions:
        house_images.extend(input_path.glob(f'*{ext}'))
    
    if not house_images:
        print(f"❌ No images found in {input_dir}")
        print(f"   Please add house images (.jpg, .png) to this directory")
        return False
    
    print(f"📂 Found {len(house_images)} house images")
    print()
    
    # Process each image
    for idx, house_img in enumerate(house_images, 1):
        sample_id = f"sample_{idx:03d}"
        sample_dir = output_path / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Processing {idx}/{len(house_images)}: {house_img.name}")
        
        # Copy 3D house image
        house_3d_path = sample_dir / f"house_3d{house_img.suffix}"
        img = Image.open(house_img)
        img.save(house_3d_path)
        print(f"  ✓ Saved 3D image")
        
        # Create placeholder floor plan (you should replace with actual floor plans!)
        floor_plan_path = sample_dir / "floor_plan.png"
        create_simple_floor_plan(house_img, floor_plan_path)
        print(f"  ⚠️  Created placeholder floor plan (REPLACE WITH ACTUAL FLOOR PLAN!)")
        
        # Create metadata template
        metadata = {
            "sample_id": sample_id,
            "original_file": house_img.name,
            "rooms": 0,  # TODO: Fill in actual values
            "bedrooms": 0,
            "bathrooms": 0,
            "floor_area": 0.0,
            "style": "Modern",  # TODO: Adjust based on your design
            "description": f"House from {house_img.name}",
            "notes": "PLEASE UPDATE metadata.json with actual house details!"
        }
        
        with open(sample_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ Created metadata.json (NEEDS TO BE UPDATED!)")
        print()
    
    # Create summary
    print("=" * 60)
    print(f"✅ Dataset prepared: {len(house_images)} samples")
    print(f"📁 Output directory: {output_path}")
    print()
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("=" * 60)
    print("1. For EACH sample folder, you need to:")
    print("   - Replace 'floor_plan.png' with the ACTUAL 2D floor plan")
    print("   - Update 'metadata.json' with real house details")
    print()
    print("2. If you don't have floor plans:")
    print("   Option A: Create them in CAD software (AutoCAD, SketchUp)")
    print("   Option B: Draw them by hand and scan")
    print("   Option C: Use floor plan extraction tools")
    print()
    print("3. Once ready, upload to Smart City ML Training:")
    print("   - Go to Dashboard → ML Training → Dataset Management")
    print("   - For each sample, upload:")
    print("     • floor_plan.png (2D)")
    print("     • house_3d.jpg (3D)")
    print("     • Fill metadata from metadata.json")
    print()
    return True

def create_glb_placeholder(house_image_path: Path, output_path: Path):
    """
    Create a simple 3D model placeholder.
    For actual 3D models, you need modeling software.
    """
    # This would require actual 3D modeling - just document the process
    pass

def main():
    parser = argparse.ArgumentParser(
        description='Prepare dataset for ML training from house images'
    )
    parser.add_argument(
        '--input-dir',
        type=str,
        default='./house_images',
        help='Directory containing house images (default: ./house_images)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./prepared_dataset',
        help='Output directory for organized dataset (default: ./prepared_dataset)'
    )
    
    args = parser.parse_args()
    
    print("🏠 Smart City ML Dataset Preparation Tool")
    print("=" * 60)
    print()
    
    # Check if input directory exists
    if not os.path.exists(args.input_dir):
        print(f"❌ Input directory not found: {args.input_dir}")
        print()
        print("Creating it for you...")
        os.makedirs(args.input_dir, exist_ok=True)
        print(f"✅ Created: {args.input_dir}")
        print()
        print("📝 Next step: Add your house images to this directory")
        print(f"   Example: cp /path/to/your/houses/*.jpg {args.input_dir}/")
        return
    
    # Organize dataset
    success = organize_dataset(args.input_dir, args.output_dir)
    
    if success:
        print("=" * 60)
        print("🎉 Dataset preparation complete!")
        print()
        print(f"Next: Review files in {args.output_dir}")
        print("      Then upload to Smart City platform")

if __name__ == '__main__':
    main()
