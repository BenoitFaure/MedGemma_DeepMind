import os
import nibabel as nib
import numpy as np
import json
import gzip
import shutil
from pathlib import Path
from sklearn.model_selection import train_test_split
import re
from collections import defaultdict

def extract_timepoint_number(timepoint_folder):
    """Extract numeric timepoint from folder name for sorting"""
    match = re.search(r'week-(\d+)(?:-(\d+))?', timepoint_folder)
    if match:
        week = int(match.group(1))
        subweek = int(match.group(2)) if match.group(2) else 0
        return week + subweek * 0.1  # To handle subweeks properly
    return 999  # Put unmatched at end

def normalize_volume(volume_data, percentile_low=1, percentile_high=99):
    """
    Normalize volume to 0-1 range after clipping outliers
    Args:
        volume_data: 3D numpy array
        percentile_low: Lower percentile for clipping (default 1%)
        percentile_high: Upper percentile for clipping (default 99%)
    """
    # Only consider non-zero voxels for percentile calculation (brain tissue)
    brain_mask = volume_data > 0
    if not np.any(brain_mask):
        return volume_data
    
    brain_voxels = volume_data[brain_mask]
    
    # Calculate percentiles only on brain voxels
    p_low = np.percentile(brain_voxels, percentile_low)
    p_high = np.percentile(brain_voxels, percentile_high)
    
    # Clip the entire volume
    clipped_volume = np.clip(volume_data, p_low, p_high)
    
    # Normalize to 0-1, but preserve background (0 values)
    if p_high > p_low:
        normalized_volume = np.where(brain_mask, 
                                   (clipped_volume - p_low) / (p_high - p_low), 
                                   0)  # Keep background as 0
    else:
        normalized_volume = clipped_volume
    
    return normalized_volume.astype(np.float32)

def process_segmentation_mask(seg_data):
    """
    Process segmentation mask to keep only background (0) and edema (3->1)
    """
    # Create new mask: background=0, edema=1, everything else=0
    new_seg = np.zeros_like(seg_data, dtype=np.uint8)
    new_seg[seg_data == 3] = 1  # Edema becomes label 1
    # Background (seg_data == 0) remains 0
    return new_seg

def save_as_nii_gz(data, affine, header, output_path):
    """Save data as .nii.gz file"""
    # Create new nifti image
    new_img = nib.Nifti1Image(data, affine, header)
    
    # Save as .nii.gz
    nib.save(new_img, output_path)
    print(f"Saved: {output_path}")

def get_first_two_timepoints(patient_folder):
    """Get the first two timepoints for a patient, sorted chronologically"""
    timepoint_folders = [f for f in patient_folder.iterdir() 
                        if f.is_dir() and 'week' in f.name]
    
    # Sort by timepoint number
    timepoint_folders.sort(key=lambda x: extract_timepoint_number(x.name))
    
    # Return first two
    return timepoint_folders[:2]

def get_nnunet_raw_folder():
    """Get the nnUNet_raw folder path from environment variables or default"""
    # Check for nnUNet_raw environment variable
    nnunet_raw = os.environ.get('nnUNet_raw')
    if nnunet_raw:
        return Path(nnunet_raw)
    
    # Check for nnUNet_raw_data_base (legacy)
    nnunet_raw_base = os.environ.get('nnUNet_raw_data_base')
    if nnunet_raw_base:
        return Path(nnunet_raw_base) / 'nnUNet_raw_data'
    
    return None

def convert_lumiere_to_nnunet(input_path, output_path=None, dataset_id=100, dataset_name="LUMIERE", use_nnunet_env=True):
    """
    Convert LUMIERE dataset to nnU-Net format
    Args:
        input_path: Path to LUMIERE dataset
        output_path: Custom output path (optional, overrides nnU-Net environment)
        dataset_id: Dataset ID (3-digit integer)
        dataset_name: Dataset name
        use_nnunet_env: If True, tries to use nnUNet_raw environment variable
    """
    input_path = Path(input_path)
    
    # Determine output directory
    if use_nnunet_env and output_path is None:
        nnunet_raw_folder = get_nnunet_raw_folder()
        if nnunet_raw_folder:
            output_path = nnunet_raw_folder
            print(f"✅ Using nnUNet_raw folder: {output_path}")
        else:
            print("⚠️  nnUNet_raw environment variable not set!")
            print("   Using fallback output path. You may need to:")
            print("   1. Set nnUNet_raw environment variable, OR")
            print("   2. Move the dataset to your nnUNet_raw folder manually")
            output_path = Path("/home/rohitkumar/gemma/dataset")
    else:
        output_path = Path(output_path) if output_path else Path("/home/rohitkumar/gemma/dataset")
    
    # Create output directory structure  
    dataset_folder = output_path / f"Dataset{dataset_id:03d}_{dataset_name}"
    images_tr_folder = dataset_folder / "imagesTr"
    images_ts_folder = dataset_folder / "imagesTs"
    labels_tr_folder = dataset_folder / "labelsTr"
    labels_ts_folder = dataset_folder / "labelsTs"
    
    # Create directories
    for folder in [dataset_folder, images_tr_folder, images_ts_folder, 
                   labels_tr_folder, labels_ts_folder]:
        folder.mkdir(parents=True, exist_ok=True)
    
    # Find all patient folders
    patient_folders = [f for f in input_path.iterdir() 
                      if f.is_dir() and f.name.startswith('Patient-')]
    
    print(f"Found {len(patient_folders)} patients")
    
    # Collect all valid cases
    all_cases = []
    failed_cases = []
    
    case_counter = 1
    
    for patient_folder in sorted(patient_folders):
        patient_id = patient_folder.name
        print(f"\nProcessing {patient_id}...")
        
        # Get first two timepoints
        timepoints = get_first_two_timepoints(patient_folder)
        
        if len(timepoints) < 2:
            print(f"  Warning: {patient_id} has less than 2 timepoints, skipping...")
            continue
        
        for i, timepoint_folder in enumerate(timepoints):
            timepoint_name = timepoint_folder.name
            print(f"  Processing {timepoint_name}...")
            
            # Check if required files exist
            flair_path = timepoint_folder / "flair_skull_strip.nii"
            seg_path = timepoint_folder / "seg_mask.nii"
            
            if not flair_path.exists() or not seg_path.exists():
                print(f"    Missing files in {timepoint_name}, skipping...")
                failed_cases.append(f"{patient_id}_{timepoint_name}")
                continue
            
            try:
                # Load FLAIR image
                flair_img = nib.load(flair_path)
                flair_data = flair_img.get_fdata()
                
                # Load segmentation mask
                seg_img = nib.load(seg_path)
                seg_data = seg_img.get_fdata().astype(np.uint8)
                
                # Check if shapes match
                if flair_data.shape != seg_data.shape:
                    print(f"    Shape mismatch in {timepoint_name}: FLAIR {flair_data.shape} vs SEG {seg_data.shape}")
                    failed_cases.append(f"{patient_id}_{timepoint_name}")
                    continue
                
                # Normalize FLAIR data
                flair_normalized = normalize_volume(flair_data)
                
                # Process segmentation mask (keep only background and edema)
                seg_processed = process_segmentation_mask(seg_data)
                
                # Create case identifier
                case_id = f"LUMIERE_{case_counter:03d}"
                
                # Store case info
                all_cases.append({
                    'case_id': case_id,
                    'patient_id': patient_id,
                    'timepoint': timepoint_name,
                    'flair_data': flair_normalized,
                    'seg_data': seg_processed,
                    'affine': flair_img.affine,
                    'header': flair_img.header
                })
                
                print(f"    Successfully processed: {case_id}")
                case_counter += 1
                
            except Exception as e:
                print(f"    Error processing {timepoint_name}: {e}")
                failed_cases.append(f"{patient_id}_{timepoint_name}")
                continue
    
    print(f"\nSuccessfully processed {len(all_cases)} cases")
    if failed_cases:
        print(f"Failed to process {len(failed_cases)} cases:")
        for case in failed_cases:
            print(f"  - {case}")
    
    if len(all_cases) == 0:
        print("No valid cases found. Exiting.")
        return
    
    # Split into train/test (80/20)
    case_ids = [case['case_id'] for case in all_cases]
    train_ids, test_ids = train_test_split(case_ids, test_size=0.2, random_state=42)
    
    print(f"\nDataset split:")
    print(f"  Training: {len(train_ids)} cases")
    print(f"  Testing: {len(test_ids)} cases")
    
    # Save training cases
    print("\nSaving training cases...")
    for case in all_cases:
        if case['case_id'] in train_ids:
            # Save FLAIR image
            flair_output = images_tr_folder / f"{case['case_id']}_0000.nii.gz"
            save_as_nii_gz(case['flair_data'], case['affine'], case['header'], flair_output)
            
            # Save segmentation
            seg_output = labels_tr_folder / f"{case['case_id']}.nii.gz"
            save_as_nii_gz(case['seg_data'], case['affine'], case['header'], seg_output)
    
    # Save test cases
    print("\nSaving test cases...")
    for case in all_cases:
        if case['case_id'] in test_ids:
            # Save FLAIR image
            flair_output = images_ts_folder / f"{case['case_id']}_0000.nii.gz"
            save_as_nii_gz(case['flair_data'], case['affine'], case['header'], flair_output)
            
            # Save segmentation
            seg_output = labels_ts_folder / f"{case['case_id']}.nii.gz"
            save_as_nii_gz(case['seg_data'], case['affine'], case['header'], seg_output)
    
    # Create dataset.json
    dataset_json = {
        "channel_names": {
            "0": "FLAIR"
        },
        "labels": {
            "background": 0,
            "edema": 1
        },
        "numTraining": len(train_ids),
        "file_ending": ".nii.gz"
    }
    
    # Save dataset.json
    json_path = dataset_folder / "dataset.json"
    with open(json_path, 'w') as f:
        json.dump(dataset_json, f, indent=2)
    
    print(f"\nDataset conversion completed!")
    print(f"Output directory: {dataset_folder}")
    print(f"Dataset configuration saved to: {json_path}")
    
    # Print summary
    print(f"\nSummary:")
    print(f"- Total cases processed: {len(all_cases)}")
    print(f"- Training cases: {len(train_ids)}")
    print(f"- Test cases: {len(test_ids)}")
    print(f"- Failed cases: {len(failed_cases)}")
    print(f"- Input modality: FLAIR (normalized 0-1)")
    print(f"- Labels: 0=background, 1=edema")
    
    return dataset_folder

def verify_dataset(dataset_folder):
    """Verify the created dataset"""
    print(f"\nVerifying dataset at {dataset_folder}...")
    
    dataset_folder = Path(dataset_folder)
    
    # Check folder structure
    required_folders = ["imagesTr", "imagesTs", "labelsTr", "labelsTs"]
    for folder in required_folders:
        folder_path = dataset_folder / folder
        if not folder_path.exists():
            print(f"❌ Missing folder: {folder}")
        else:
            file_count = len(list(folder_path.glob("*.nii.gz")))
            print(f"✅ {folder}: {file_count} files")
    
    # Check dataset.json
    json_path = dataset_folder / "dataset.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            dataset_info = json.load(f)
        print(f"✅ dataset.json exists")
        print(f"   - Channels: {dataset_info['channel_names']}")
        print(f"   - Labels: {dataset_info['labels']}")
        print(f"   - Training cases: {dataset_info['numTraining']}")
    else:
        print(f"❌ Missing dataset.json")
    
    # Verify a few random files
    images_tr = list((dataset_folder / "imagesTr").glob("*.nii.gz"))
    labels_tr = list((dataset_folder / "labelsTr").glob("*.nii.gz"))
    
    if len(images_tr) > 0 and len(labels_tr) > 0:
        # Check first training case
        img_path = images_tr[0]
        case_id = img_path.stem.replace("_0000", "")
        seg_path = dataset_folder / "labelsTr" / f"{case_id}.nii.gz"
        
        if seg_path.exists():
            img = nib.load(img_path)
            seg = nib.load(seg_path)
            
            print(f"✅ Sample verification ({case_id}):")
            print(f"   - Image shape: {img.shape}")
            print(f"   - Image data range: [{img.get_fdata().min():.3f}, {img.get_fdata().max():.3f}]")
            print(f"   - Segmentation shape: {seg.shape}")
            print(f"   - Segmentation labels: {np.unique(seg.get_fdata())}")
        else:
            print(f"❌ Missing corresponding segmentation for {case_id}")

if __name__ == "__main__":
    # Configuration
    INPUT_PATH = "/home/rohitkumar/gemma/train/train"
    DATASET_ID = 100
    DATASET_NAME = "LUMIERE"
    
    print("Starting LUMIERE to nnU-Net conversion...")
    print(f"Input: {INPUT_PATH}")
    
    # Option 1: Let the script auto-detect nnUNet_raw folder
    print("\n🔍 Checking nnU-Net environment setup...")
    nnunet_raw = get_nnunet_raw_folder()
    
    if nnunet_raw:
        print(f"✅ Found nnUNet_raw: {nnunet_raw}")
        use_env = True
        output_path = None  # Will use nnUNet_raw automatically
    else:
        print("⚠️  nnUNet_raw not configured. Using fallback path.")
        print("   After conversion, you may need to move the dataset or set nnUNet_raw")
        use_env = False
        output_path = "/home/rohitkumar/gemma/dataset"
    
    print(f"Output will be: {output_path if output_path else nnunet_raw}")
    
    # Convert dataset
    dataset_folder = convert_lumiere_to_nnunet(
        input_path=INPUT_PATH,
        output_path=output_path,
        dataset_id=DATASET_ID,
        dataset_name=DATASET_NAME,
        use_nnunet_env=use_env
    )
    
    # Verify the created dataset
    if dataset_folder:
        verify_dataset(dataset_folder)
        
        print(f"\n🎉 Conversion completed successfully!")
        print(f"Your nnU-Net dataset is ready at: {dataset_folder}")
        
        # Check if dataset is in correct nnUNet_raw location
        nnunet_raw = get_nnunet_raw_folder()
        if nnunet_raw and str(dataset_folder).startswith(str(nnunet_raw)):
            print(f"✅ Dataset is correctly placed in nnUNet_raw folder")
            print(f"\nNext steps:")
            print(f"1. Run: nnUNetv2_plan_and_preprocess -d {DATASET_ID}")
            print(f"2. Run: nnUNetv2_train {DATASET_ID} 3d_fullres 0")
        else:
            print(f"⚠️  Dataset location setup:")
            if nnunet_raw:
                print(f"   Your nnUNet_raw: {nnunet_raw}")
                print(f"   Dataset location: {dataset_folder}")
                print(f"   Consider moving dataset to nnUNet_raw folder or updating nnUNet_raw variable")
            else:
                print(f"   Please set nnUNet_raw environment variable to: {dataset_folder.parent}")
                print(f"   Or move {dataset_folder} to your nnUNet_raw folder")
            
            print(f"\nNext steps:")
            print(f"1. Set nnUNet_raw environment variable appropriately")
            print(f"2. Run: nnUNetv2_plan_and_preprocess -d {DATASET_ID}")
            print(f"3. Run: nnUNetv2_train {DATASET_ID} 3d_fullres 0")