'''
Code to handle segmentation tasks
'''

import subprocess
import os
import nibabel as nib
import numpy as np
import glob
import shutil

def run_segmentation(id):
    """
    Run segmentation using the remote nnU-Net endpoint
    
    Args:
        id (str): The MRI ID (e.g., "0" or "1")
    """
    # Define input and output file paths
    input_file = f"./front/public/mri/{id}/mri_file.nii"
    output_file = f"./front/public/mri/{id}_seg/mri_file.nii"
    
    # Path to the test_remote_endpoint script
    script_path = "../nnunet-inference/test_remote_endpoint.py"
    
    # Construct the command
    command = [
        "python", 
        script_path,
        "--input_file", input_file,
        "--output_file", output_file
    ]
    
    try:
        print(f"Running segmentation for ID {id}...")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
        # Run the command
        result = subprocess.run(command, 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        print("Segmentation completed successfully!")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running segmentation: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False