import os
import nibabel as nib
import numpy as np
from PIL import Image
import random
import argparse
from pathlib import Path

def normalize_image(image_slice):
    """Normalize image slice to 0-255 range for JPG conversion"""
    p_low, p_high = np.percentile(image_slice, [0.5, 99.5])
    image_slice = np.clip(image_slice, p_low, p_high)

    if image_slice.max() > image_slice.min():
        normalized = (image_slice - image_slice.min()) / (image_slice.max() - image_slice.min())
        normalized = (normalized * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(image_slice, dtype=np.uint8)

    return normalized

def find_valid_slices(seg_data, target_label=1):
    """Find axial slices that contain the target segmentation label"""
    valid_slices = []
    for slice_idx in range(seg_data.shape[0]):
        if target_label in seg_data[slice_idx]:
            valid_slices.append(slice_idx)
    return valid_slices

def extract_random_slice(image_path, seg_path, output_folder):
    """Extract a random slice from image that has segmentation"""
    try:
        img_nib = nib.load(image_path)
        seg_nib = nib.load(seg_path)

        img_data = img_nib.get_fdata()
        seg_data = seg_nib.get_fdata()

        valid_slices = find_valid_slices(seg_data, target_label=1)

        if not valid_slices:
            print(f"Warning: No slices with label 1 found in {seg_path}")
            return False

        selected_slice = random.choice(valid_slices)
        image_slice = img_data[selected_slice, :, :]
        normalized_slice = normalize_image(image_slice)

        pil_image = Image.fromarray(normalized_slice, mode='L')
        base_name = Path(image_path).stem.replace('.nii', '')
        output_path = output_folder / f"{base_name}.jpg"

        pil_image.save(output_path, 'JPEG', quality=95)

        print(f"Extracted slice {selected_slice} from {base_name} -> {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return False

def find_matching_label(img_file, label_files):
    """Match label by prefix, e.g., LUMIERE_001_0000 -> LUMIERE_001"""
    img_prefix = img_file.stem[:11]  # 'LUMIERE_001'
    for label_file in label_files:
        if label_file.stem == img_prefix:
            return label_file
    return None

def process_dataset(root_folder):
    """Process the entire nnU-Net dataset"""
    root_path = Path(root_folder)

    folder_pairs = [
        ('imagesTr', 'labelsTr', 'slices_train'),
        ('imagesTs', 'labelTs', 'slices_test')
    ]

    for img_folder, label_folder, output_folder in folder_pairs:
        img_path = root_path / img_folder
        label_path = root_path / label_folder
        output_path = root_path / output_folder

        if not img_path.exists():
            print(f"Warning: {img_path} does not exist, skipping...")
            continue
        if not label_path.exists():
            print(f"Warning: {label_path} does not exist, skipping...")
            continue

        output_path.mkdir(exist_ok=True)
        print(f"Processing {img_folder} -> {output_folder}")

        img_files = list(img_path.glob("*.nii.gz"))
        label_files = list(label_path.glob("*.nii.gz"))

        successful_extractions = 0

        for img_file in img_files:
            seg_file = find_matching_label(img_file, label_files)

            if not seg_file:
                print(f"Warning: No matching label found for {img_file.name}")
                continue

            if extract_random_slice(img_file, seg_file, output_path):
                successful_extractions += 1

        print(f"Successfully extracted {successful_extractions}/{len(img_files)} slices from {img_folder}")
        print("-" * 50)

def main():
    parser = argparse.ArgumentParser(description='Extract random axial slices from nnU-Net dataset')
    parser.add_argument('root_folder', type=str, help='Root folder containing imagesTr, imagesTs, labelsTr, labelTs')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')

    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    if not os.path.exists(args.root_folder):
        print(f"Error: Root folder {args.root_folder} does not exist")
        return

    print(f"Processing nnU-Net dataset in: {args.root_folder}")
    print(f"Random seed: {args.seed}")
    print("=" * 50)

    process_dataset(args.root_folder)
    print("Processing complete!")

if __name__ == "__main__":
    main()
