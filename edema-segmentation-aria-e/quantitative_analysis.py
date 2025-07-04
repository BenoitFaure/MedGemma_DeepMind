import numpy as np
import nibabel as nib
from scipy.ndimage import label
from skimage.measure import regionprops
import argparse


def analyze_lesions(mask_path, timepoint, slice_number=None):
    """
    Fast lesion analysis from segmentation mask (optimized for hackathon demo).
    
    Args:
        mask_path (str): Path to the segmentation mask (.nii.gz)
        timepoint (int): Timepoint order (0 or 1)
        slice_number (int, optional): Axial slice number. If provided, will be returned directly.
    
    Returns:
        dict: Dictionary containing lesion analysis results
    """
    
    # Load the segmentation mask
    mask_img = nib.load(mask_path)
    mask_data = mask_img.get_fdata().astype(np.uint8)  # Convert to uint8 for speed
    
    # Get voxel dimensions for volume calculation
    voxel_dims = mask_img.header.get_zooms()
    voxel_volume = np.prod(voxel_dims)  # mm³
    
    # Find connected components (distinct lesions) - this is the bottleneck
    print("Finding connected components...")
    labeled_array, num_lesions = label(mask_data == 1)
    
    if num_lesions == 0:
        return {
            'max_diameter_mm': 0.0,
            'total_volume_mm3': 0.0,
            'num_lesions': 0,
            'timepoint': timepoint,
            'max_lesion_slice': slice_number if slice_number is not None else 0
        }
    
    print(f"Found {num_lesions} lesions. Analyzing properties...")
    
    # Calculate total volume (fast)
    total_lesion_voxels = np.sum(mask_data == 1)
    total_volume = total_lesion_voxels * voxel_volume
    
    # Use regionprops for fast property calculation
    regions = regionprops(labeled_array)
    
    # Find largest lesion by area
    largest_region = max(regions, key=lambda r: r.area)
    
    # Fast approximate diameter using equivalent diameter
    max_diameter = largest_region.equivalent_diameter * min(voxel_dims)  # Approximate scaling
    
    # Find slice with biggest lesion (if not provided)
    if slice_number is None:
        max_lesion_slice = find_slice_with_largest_lesion_fast(labeled_array, largest_region.label)
    else:
        max_lesion_slice = slice_number
    
    return {
        'max_diameter_cm': float(max_diameter)/10,
        'total_volume_mL': float(total_volume)* 1e-3,
        'num_lesions': int(num_lesions),
        'timepoint': int(timepoint),
        'max_lesion_slice': int(max_lesion_slice)
    }


def find_slice_with_largest_lesion_fast(labeled_array, largest_lesion_label):
    lesion_mask = (labeled_array == largest_lesion_label)
    
    # Sum lesion voxels in each axial slice: sum over axes 1 (rows) and 2 (columns)
    slice_areas = np.sum(lesion_mask, axis=(1, 2))
    
    max_slice = np.argmax(slice_areas)
    return int(max_slice)



def analyze_lesions_downsampled(mask_path, timepoint, slice_number=None, downsample_factor=2):
    """
    Ultra-fast lesion analysis with downsampling for very large masks.
    
    Args:
        mask_path (str): Path to the segmentation mask (.nii.gz)
        timepoint (int): Timepoint order (0 or 1)
        slice_number (int, optional): Axial slice number. If provided, will be returned directly.
        downsample_factor (int): Factor to downsample the mask (2 = half resolution)
    
    Returns:
        dict: Dictionary containing lesion analysis results
    """
    
    # Load the segmentation mask
    mask_img = nib.load(mask_path)
    mask_data = mask_img.get_fdata().astype(np.uint8)
    
    # Downsample for speed
    if downsample_factor > 1:
        print(f"Downsampling by factor {downsample_factor} for speed...")
        mask_data = mask_data[::downsample_factor, ::downsample_factor, ::downsample_factor]
    
    # Get voxel dimensions (adjust for downsampling)
    voxel_dims = mask_img.header.get_zooms()
    if downsample_factor > 1:
        voxel_dims = tuple(d * downsample_factor for d in voxel_dims)
    voxel_volume = np.prod(voxel_dims)
    
    # Find connected components
    print("Finding connected components...")
    labeled_array, num_lesions = label(mask_data == 1)
    
    if num_lesions == 0:
        return {
            'max_diameter_mm': 0.0,
            'total_volume_mm3': 0.0,
            'num_lesions': 0,
            'timepoint': timepoint,
            'max_lesion_slice': slice_number if slice_number is not None else 0
        }
    
    print(f"Found {num_lesions} lesions. Analyzing properties...")
    
    # Calculate total volume
    total_lesion_voxels = np.sum(mask_data == 1)
    total_volume = total_lesion_voxels * voxel_volume
    
    # Use regionprops for fast property calculation
    regions = regionprops(labeled_array)
    largest_region = max(regions, key=lambda r: r.area)
    
    # Fast approximate diameter
    max_diameter = largest_region.equivalent_diameter * min(voxel_dims)
    
    # Find slice with biggest lesion (adjust for downsampling)
    if slice_number is None:
        max_lesion_slice = find_slice_with_largest_lesion_fast(labeled_array, largest_region.label)
        if downsample_factor > 1:
            max_lesion_slice *= downsample_factor  # Scale back up
    else:
        max_lesion_slice = slice_number
    
    return {
        'max_diameter_mm': float(max_diameter),
        'total_volume_mm3': float(total_volume),
        'num_lesions': int(num_lesions),
        'timepoint': int(timepoint),
        'max_lesion_slice': int(max_lesion_slice)
    }


def main():
    """Command line interface for the lesion analysis script."""
    parser = argparse.ArgumentParser(description='Fast lesion analysis from segmentation mask')
    parser.add_argument('mask_path', help='Path to segmentation mask (.nii.gz)')
    parser.add_argument('timepoint', type=int, choices=[0, 1], help='Timepoint order (0 or 1)')
    parser.add_argument('--slice_number', type=int, help='Axial slice number (optional)')
    parser.add_argument('--fast', action='store_true', help='Use ultra-fast mode with downsampling')
    parser.add_argument('--downsample', type=int, default=2, help='Downsampling factor for fast mode (default: 2)')
    
    args = parser.parse_args()
    
    # Analyze lesions
    if args.fast:
        print("Using ultra-fast mode with downsampling...")
        results = analyze_lesions_downsampled(args.mask_path, args.timepoint, args.slice_number, args.downsample)
    else:
        results = analyze_lesions(args.mask_path, args.timepoint, args.slice_number)
    
    # Print results
    print("\nLesion Analysis Results:")
    print("=" * 30)
    for key, value in results.items():
        print(f"{key}: {value}")
    return results


if __name__ == "__main__":
    main()