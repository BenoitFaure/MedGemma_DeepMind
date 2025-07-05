'''
Script to handle analysis of patient IRM and seg
'''
# Dependencies
import base64
import nibabel as nib
import numpy as np
import cv2
import io
from PIL import Image
from google.cloud import aiplatform

from back_environment import PROJECT_ID, REGION, MEDGEMMA_FT_ENDPOINT_ID, MEDGEMMA_FT_ENDPOINT_REGION, MEDGEMMA_ENDPOINT_ID, MEDGEMMA_ENDPOINT_REGION

def run_analysis_location(id):

    '''
    Give the id of the IRM and run the analysis to determine the location of the edema using the MedGemma FineTuned model.
    Args:
        id (str): The MRI ID (e.g., "0" or "1")
    Returns:
        str: The predicted brain region where the edema is located (e.g., "frontal", "occipital", "parietal", "temporal")
    '''

    # MOCK FOR DEMO
    return "frontal"

    # Run MedGemma FineTuned on all images
    #          Images in seg are supposed to be pre-processed to already have the segmentations applied

    # INIT PLATFORM AND ENDPOINT
    aiplatform.init(project=PROJECT_ID, location=REGION)

    endpoint = aiplatform.Endpoint(
        endpoint_name=MEDGEMMA_FT_ENDPOINT_ID,
        project=PROJECT_ID,
        location=MEDGEMMA_FT_ENDPOINT_REGION,
    )

    # Load MRI data using nibabel and process each slice
    mri_file_path = f"./front/public/mri/{id}.seg/mri_file.nii"
    
    # Load the NIfTI file
    img = nib.load(mri_file_path)
    data = img.get_fdata()

    # Prompt 
    BRAIN_CLASSES = [
        "A: frontal",
        "B: occipital",
        "C: parietal",
        "D: temporal",
    ]
    options = "\n".join(BRAIN_CLASSES)
    PROMPT = f"What brain region does the edema span the most?\n{options}\nOutput the answer as a single letter (A, B, C, or D)."
    formatted_prompt = f"{PROMPT} <start_of_image>"
    
    # Process each slice and encode to base64
    slice_predictions = []
    
    for slice_idx in range(data.shape[0]):
        # Extract the slice
        slice_data = data[slice_idx]

        # Encode to png
        success, encoded_image = cv2.imencode('.png', slice_data)
        # Encode the bytes to base64
        img_b64 = base64.b64encode(encoded_image).decode('utf-8')

        # Instance and Message
        instances = [
            {
                "prompt": formatted_prompt,
                "multi_modal_data": {"image": f'data:image/png;base64,{img_b64}' },
                "max_tokens": 500,
                "temperature": 0,
                "raw_response": False,
            },
        ]

        # Run Inference
        response = endpoint.predict(
            instances=instances, use_dedicated_endpoint=True
        )

        # EXTRACT PREDICTION
        for label in ["A", "B", "C", "D"]:
            if label in response.predictions[0]:
                slice_predictions.append(label)
                break

    # Get the most common prediction across all slices
    if slice_predictions == []:
        return "frontal"
    most_common_prediction = max(set(slice_predictions), key=slice_predictions.count)
    return {"A": "frontal", "B": "occipital", "C": "parietal", "D": "temporal"}[most_common_prediction]




def run_analysis(json_data):
    '''
    Run the MedGemma model to analyze the severity of ARIA-E lesions based on the provided JSON data.
    Args:
        json_data (str): JSON string containing the radiology report data.
    Returns:
        str: The severity of ARIA-E lesions (MILD, MODERATE, or SEVERE).
    '''

    # MOCK FOR DEMO
    decision = "MILD"
    return decision, f"The report indicates 6 sites of involvement and a maximum lesion diameter of 1.1 cm. According to the grading criteria, more than 1 site of involvement where each lesion is less than 10 cm classifies the severity as {decision}."

    # Run MedGemma on json_data

    # INIT PLATFORM AND ENDPOINT
    aiplatform.init(project=PROJECT_ID, location=REGION)

    endpoint = aiplatform.Endpoint(
        endpoint_name=MEDGEMMA_ENDPOINT_ID,
        project=PROJECT_ID,
        location=MEDGEMMA_ENDPOINT_REGION,
    )

    # Prompt
    PROMPT = f'''
    You are a clinical radiology assistant specialized in grading the severity of ARIA-E (Amyloid-Related Imaging Abnormalities – Edema) in patients undergoing anti-amyloid treatment.
    ARIA-E severity is classified by radiologists based on the number and size of sites of involvement showing vasogenic edema and/or sulcal effusion on FLAIR imaging.
    Use the following grading criteria:

    MILD
    • Exactly 1 site of involvement
    • Lesion size < 5 cm

    MODERATE
    • 1 site of involvement measuring 5–10 cm
    OR
    • More than 1 site of involvement, each < 10 cm

    SEVERE
    • At least 1 site of involvement measuring > 10 cm

    You may extract information about lesion size or number of sites of involvement from the attached JSON radiology report.
    
    Source: Adapted from Cogswell et al. (2022)
    
    <start_of_json>
    {json_data}
    <end_of_json>

    
    Always respond with one of the following severity labels, based strictly on the criteria above:
    MILD, MODERATE, or SEVERE.

    ALWAYS SAY MILD IF THE REPORT DOES NOT MENTION ANY ARIA-E LESIONS.

    Your response should be of the form:
    DIAGNOSIS  |  REASON
    '''

    # Instance and Message
    instances = [
        {
            "prompt": PROMPT,
            "max_tokens": 500,
            "temperature": 0,
            "raw_response": False,
        },
    ]

    # Run Inference
    response = endpoint.predict(
        instances=instances, use_dedicated_endpoint=True
    )

    return response.predictions[0]