import cv2
import numpy as np
import os
import nibabel as nib

TO_SLICE = ["/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/0/", "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/1/"]
SEG = {
    "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/0.seg/": "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/0/",
    "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/1.seg/": "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/1/"
}
DIFFERENCE = "/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/difference/"

def extract_files():
    for slice_path in TO_SLICE:
        # Load the NIfTI file
        img = nib.load(slice_path + "mri_file.nii")
        data = img.get_fdata()

        for i in range(154):
            slice = data[i]
            min_val, max_val = np.min(slice), np.max(slice)
            slice = (slice - min_val) / (max_val - min_val) * 255
            slice = slice.astype(np.uint8)
            name = slice_path + f"/slice_{i:03d}.jpg"
            cv2.imwrite(name, slice)
        
        print(f"Saved slices for {slice_path} to disk.")

    for seg_path, orig_path in SEG.items():
        # Generate jpg of the slice with the segmentation as red on top
        segmentation = nib.load(seg_path + "mri_file.nii").get_fdata()
        segmentation = (segmentation > 0).astype(np.float32)

        orig_data = nib.load(orig_path + "mri_file.nii").get_fdata()
        for i in range(154):
            orig_slice = orig_data[i]
            seg_slice = segmentation[i]

            # Normalize original slice
            min_val, max_val = np.min(orig_slice), np.max(orig_slice)
            orig_slice = (orig_slice - min_val) / (max_val - min_val) * 255
            orig_slice = orig_slice.astype(np.uint8)

            # Create a color image with red segmentation
            color_image = cv2.cvtColor(orig_slice, cv2.COLOR_GRAY2BGR)
            color_image[seg_slice > 0] = [0, 0, 255]
            name = seg_path + f"/slice_{i:03d}.jpg"
            cv2.imwrite(name, color_image)

    os.makedirs(DIFFERENCE, exist_ok=True)
    seg_0 = nib.load(SEG["/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/0.seg/"] + "mri_file.nii").get_fdata()
    seg_1 = nib.load(SEG["/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/1.seg/"] + "mri_file.nii").get_fdata()

    # Calculate the difference
    diff = np.abs(seg_1 - seg_0)

    # Load the original MRI data for 1
    orig_data = nib.load("/home/mohamed/Documents/Mateo_GrinchJr/MedGemma_DeepMind/application/front/public/mri/1/mri_file.nii").get_fdata()

    for i in range(154):
        orig_slice = orig_data[i]
        diff_slice = diff[i]

        # Normalize original slice
        min_val, max_val = np.min(orig_slice), np.max(orig_slice)
        orig_slice = (orig_slice - min_val) / (max_val - min_val) * 255
        orig_slice = orig_slice.astype(np.uint8)

        # Create a color image with red difference
        color_image = cv2.cvtColor(orig_slice, cv2.COLOR_GRAY2BGR)
        color_image[diff_slice > 0] = [0, 0, 255]
        
        name = DIFFERENCE + f"/slice_{i:03d}.jpg"
        cv2.imwrite(name, color_image)

    print("Saved difference slices to disk.")
    return True


if __name__ == "__main__":
    try:
        extract_files()
    except Exception as e:
        print(f"Error during extraction: {e}")
        raise e
    else:
        print("Extraction completed successfully.")
