import numpy as np
import nibabel as nb
from scipy.ndimage import label
from scipy.ndimage import center_of_mass, distance_transform_edt
from back_irm_analysis import run_analysis_location

MRI_FOLDER = "../front/public/mri"
REPORT_FOLDER = "../front/public/report"

REPORT_TEMPLATE = """<html>
"""

PIXEL_AREA_ON_MRI = 0.004 # in cm^2
DISTANCE_BETWEEN_SLICES = 0.1 # in cm

def compute_volume(segmentation):
    num_voxels = np.sum(segmentation > 0)
    voxel_volume = PIXEL_AREA_ON_MRI * DISTANCE_BETWEEN_SLICES
    return num_voxels * voxel_volume

def compute_number_of_oedemas(segmentation):
    _, num_features = label(segmentation > 0)
    return num_features

def compute_max_diameter(segmentation):
    coords = np.argwhere(segmentation > 0)
    if coords.size == 0:
        return 0.0 

    com = center_of_mass(segmentation)

    dist_transform = distance_transform_edt(segmentation > 0)

    max_distance = np.max(dist_transform[tuple(coords.T)])
    
    return max_distance * 2 * PIXEL_AREA_ON_MRI**0.5


def generate_client_report(client_name):
    info = {
        "client_name": client_name,
        "time0": "2025-03-24",
        "time1": "2025-04-18",
        "rmi_location": run_analysis_location(1),
    }

    rmi_t0_slices = nb.load("./front/public/mri/0/mri_file.nii").get_fdata()
    rmi_t1_slices = nb.load("./front/public/mri/1/mri_file.nii").get_fdata()
    seg_t0_slices = nb.load("./front/public/seg/0.seg/mri_file.nii").get_fdata()
    seg_t1_slices = nb.load("./front/public/seg/1.seg/mri_file.nii").get_fdata()

    volume_t0 = compute_volume(seg_t0_slices)
    volume_t1 = compute_volume(seg_t1_slices)
    volume_change = volume_t1 - volume_t0

    info["volume_t0"] = volume_t0
    info["volume_t1"] = volume_t1
    info["volume_change"] = volume_change
    info["oedemas_t0"] = compute_number_of_oedemas(seg_t0_slices)
    info["oedemas_t1"] = compute_number_of_oedemas(seg_t1_slices)
    info["max_diameter_t0"] = compute_max_diameter(seg_t0_slices)
    info["max_diameter_t1"] = compute_max_diameter(seg_t1_slices)

    info["previous_volumes"] = {
        "2025-02-27": 3,
    }

    # TODO: Add MedGemma analysis

    return info


# Generates a Json with the following information:
# - Client Info
# - IRM Analysis
# - Segmentation Analysis
# - Stats
# - MedGemma Analysis

# Much of the information is contained in frontend