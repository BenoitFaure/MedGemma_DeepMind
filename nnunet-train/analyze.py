import os
import nibabel as nib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from collections import defaultdict

def extract_timepoint_number(timepoint_folder):
    """Extract numeric timepoint from folder name (e.g., 'week-000-1' -> 1, 'week-044' -> 44)"""
    # Handle both formats: week-000-1 and week-044
    match = re.search(r'week-(\d+)(?:-(\d+))?', timepoint_folder)
    if match:
        week = int(match.group(1))
        subweek = int(match.group(2)) if match.group(2) else 0
        return week + subweek  # This creates a simple ordering
    return 0

def calculate_label_proportion(seg_mask_path, label_value=3):
    """Calculate the proportion of voxels with the specified label value"""
    try:
        # Load the segmentation mask
        seg_img = nib.load(seg_mask_path)
        seg_data = seg_img.get_fdata()
        
        # Calculate total non-zero voxels (brain volume)
        total_brain_voxels = np.sum(seg_data > 0)
        
        if total_brain_voxels == 0:
            return 0.0
        
        # Calculate voxels with the target label
        label_voxels = np.sum(seg_data == label_value)
        
        # Return proportion
        return label_voxels / total_brain_voxels
        
    except Exception as e:
        print(f"Error processing {seg_mask_path}: {e}")
        return None

def analyze_lumiere_dataset(dataset_path, label_value=3):
    """Analyze the evolution of label proportion across timepoints"""
    
    dataset_path = Path(dataset_path)
    results = []
    
    # Find all patient folders
    patient_folders = [f for f in dataset_path.iterdir() if f.is_dir() and f.name.startswith('Patient-')]
    
    print(f"Found {len(patient_folders)} patients")
    
    for patient_folder in sorted(patient_folders):
        patient_id = patient_folder.name
        print(f"Processing {patient_id}...")
        
        # Find all timepoint folders for this patient
        timepoint_folders = [f for f in patient_folder.iterdir() if f.is_dir() and 'week' in f.name]
        
        for timepoint_folder in timepoint_folders:
            timepoint_name = timepoint_folder.name
            timepoint_num = extract_timepoint_number(timepoint_name)
            
            # Look for seg_mask.nii file
            seg_mask_path = timepoint_folder / 'seg_mask.nii'
            
            if seg_mask_path.exists():
                proportion = calculate_label_proportion(seg_mask_path, label_value)
                
                if proportion is not None:
                    results.append({
                        'patient_id': patient_id,
                        'timepoint_name': timepoint_name,
                        'timepoint_num': timepoint_num,
                        'label_proportion': proportion
                    })
                    print(f"  {timepoint_name}: {proportion:.4f}")
                else:
                    print(f"  {timepoint_name}: Failed to process")
            else:
                print(f"  {timepoint_name}: seg_mask.nii not found")
    
    return pd.DataFrame(results)

def plot_label_evolution(df, label_value=3, save_path=None):
    """Plot the evolution of label proportion across timepoints"""
    
    # Calculate mean and std for each timepoint
    timepoint_stats = df.groupby('timepoint_num')['label_proportion'].agg(['mean', 'std', 'count']).reset_index()
    timepoint_stats['sem'] = timepoint_stats['std'] / np.sqrt(timepoint_stats['count'])  # Standard error of mean
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot individual patient trajectories (thin lines)
    for patient in df['patient_id'].unique():
        patient_data = df[df['patient_id'] == patient].sort_values('timepoint_num')
        plt.plot(patient_data['timepoint_num'], patient_data['label_proportion'], 
                'o-', alpha=0.3, linewidth=1, markersize=3, color='lightblue')
    
    # Plot mean trajectory (thick line)
    plt.errorbar(timepoint_stats['timepoint_num'], timepoint_stats['mean'], 
                yerr=timepoint_stats['sem'], 
                marker='o', linewidth=3, markersize=8, 
                capsize=5, capthick=2, color='red', label='Mean ± SEM')
    
    plt.xlabel('Timepoint', fontsize=12)
    plt.ylabel(f'Label {label_value} Proportion (relative to brain volume)', fontsize=12)
    plt.title(f'Evolution of Label {label_value} (Edema) Proportion Across Timepoints\nAveraged Over All Patients', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Add sample size annotations
    for _, row in timepoint_stats.iterrows():
        plt.annotate(f'n={int(row["count"])}', 
                    (row['timepoint_num'], row['mean']), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {save_path}")
    
    plt.show()
    
    return timepoint_stats

def print_summary_statistics(df, timepoint_stats):
    """Print summary statistics"""
    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    
    print(f"Total patients analyzed: {df['patient_id'].nunique()}")
    print(f"Total timepoints: {len(df)}")
    print(f"Unique timepoint numbers: {sorted(df['timepoint_num'].unique())}")
    
    print("\nTimepoint Statistics:")
    print(timepoint_stats.round(4))
    
    # Find timepoints with highest edema proportion
    best_timepoints = timepoint_stats.nlargest(3, 'mean')[['timepoint_num', 'mean', 'count']]
    print(f"\nTop 3 timepoints with highest mean edema proportion:")
    for _, row in best_timepoints.iterrows():
        print(f"  Timepoint {int(row['timepoint_num'])}: {row['mean']:.4f} (n={int(row['count'])})")

# Main execution
if __name__ == "__main__":
    # Set your dataset path here
    DATASET_PATH = "/home/rohitkumar/gemma/train/train"  # Change this to your actual path
    LABEL_VALUE = 3  # Edema label
    
    print("Starting LUMIERE dataset analysis...")
    print(f"Looking for label {LABEL_VALUE} (edema) evolution")
    
    # Analyze the dataset
    df = analyze_lumiere_dataset(DATASET_PATH, LABEL_VALUE)
    
    if len(df) > 0:
        # Plot the evolution
        timepoint_stats = plot_label_evolution(df, LABEL_VALUE, save_path='edema_evolution.png')
        
        # Print summary
        print_summary_statistics(df, timepoint_stats)
        
        # Save results to CSV
        df.to_csv('lumiere_label3_analysis.csv', index=False)
        timepoint_stats.to_csv('timepoint_statistics.csv', index=False)
        print("\nResults saved to 'lumiere_label3_analysis.csv' and 'timepoint_statistics.csv'")
        
    else:
        print("No data found. Please check your dataset path and file structure.")