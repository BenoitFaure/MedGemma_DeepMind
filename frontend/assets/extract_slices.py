#!/usr/bin/env python3
"""
NIfTI to JPG Converter Script
Converts .nii.gz files to JPG images, extracting axial slices from the first dimension.
Handles both MRI scans and binary segmentation files.
"""

import argparse
import os
import numpy as np
import nibabel as nib
from PIL import Image
import sys

def is_segmentation_file(data):
    """
    Determine if the file is a segmentation file based on its values.
    Returns True if the data contains only 0s and 1s (binary segmentation).
    """
    unique_values = np.unique(data)
    return len(unique_values) <= 2 and np.all(np.isin(unique_values, [0, 1]))

def normalize_image(slice_data, is_segmentation=False):
    """
    Normalize image data to 0-255 range for JPG output.
    """
    if is_segmentation:
        # For segmentation: 0 stays 0, 1 becomes 255
        return (slice_data * 255).astype(np.uint8)
    else:
        # For MRI: normalize to full 0-255 range
        slice_min = np.min(slice_data)
        slice_max = np.max(slice_data)
        
        if slice_max == slice_min:
            # Handle case where all values are the same
            return np.zeros_like(slice_data, dtype=np.uint8)
        
        normalized = (slice_data - slice_min) / (slice_max - slice_min)
        return (normalized * 255).astype(np.uint8)

def convert_nii_to_jpg(input_file, output_dir=None):
    """
    Convert a NIfTI file to JPG images, one per axial slice.
    
    Args:
        input_file (str): Path to the input .nii.gz file
        output_dir (str): Output directory. If None, uses input file directory.
    """
    # Load the NIfTI file
    try:
        nii_img = nib.load(input_file)
        data = nii_img.get_fdata()
        print(f"Loaded {input_file}")
        print(f"Data shape: {data.shape}")
        print(f"Data type: {data.dtype}")
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return False
    
    # Determine output directory
    if output_dir is None:
        output_dir = os.path.dirname(input_file)
    
    # Create output directory if it doesn't exist
    base_name = os.path.splitext(os.path.splitext(os.path.basename(input_file))[0])[0]  # Remove .nii.gz
    output_subdir = os.path.join(output_dir, f"{base_name}_slices")
    os.makedirs(output_subdir, exist_ok=True)
    
    # Check if this is a segmentation file
    is_seg = is_segmentation_file(data)
    print(f"Detected as: {'Segmentation' if is_seg else 'MRI'} file")
    
    # Get number of slices in the first dimension
    num_slices = data.shape[0]
    print(f"Processing {num_slices} axial slices...")
    
    # Process each axial slice
    successful_slices = 0
    for i in range(num_slices):
        try:
            # Extract the i-th slice from the first dimension
            slice_data = data[i, :, :]
            
            # Skip empty slices (all zeros)
            if np.all(slice_data == 0):
                print(f"Skipping empty slice {i}")
                continue
            
            # Normalize the slice
            normalized_slice = normalize_image(slice_data, is_seg)
            
            # Convert to PIL Image
            # Note: PIL expects (height, width) but our data is (width, height)
            # So we need to transpose
            img = Image.fromarray(normalized_slice.T, mode='L')
            
            # Save as JPG
            output_filename = f"{base_name}_slice_{i:03d}.jpg"
            output_path = os.path.join(output_subdir, output_filename)
            img.save(output_path, 'JPEG', quality=95)
            
            successful_slices += 1
            
        except Exception as e:
            print(f"Error processing slice {i}: {e}")
            continue
    
    print(f"Successfully converted {successful_slices} slices to JPG")
    print(f"Output saved to: {output_subdir}")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Convert NIfTI (.nii.gz) files to JPG images (axial slices)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nii_to_jpg.py brain_scan.nii.gz
  python nii_to_jpg.py segmentation.nii.gz -o /path/to/output/
  python nii_to_jpg.py scan.nii.gz --output-dir ./results/
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input .nii.gz file'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='Output directory for JPG files (default: same as input file directory)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Check if input file has correct extension
    if not args.input_file.lower().endswith('.nii.gz'):
        print(f"Warning: Input file '{args.input_file}' doesn't have .nii.gz extension.")
        print("Proceeding anyway...")
    
    # Convert the file
    success = convert_nii_to_jpg(args.input_file, args.output_dir)
    
    if success:
        print("Conversion completed successfully!")
    else:
        print("Conversion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()