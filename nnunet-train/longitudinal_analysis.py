def compare_lesion_metrics(tp0_metrics, tp1_metrics):
    """
    Compare lesion metrics between two timepoints.
    
    Args:
        tp0_metrics (dict): Metrics at timepoint 0, with keys:
            - 'max_diameter_cm' (float)
            - 'num_lesions' (int)
            - 'total_volume_ml' (float)
            - 'max_lesion_slice' (int)
        tp1_metrics (dict): Metrics at timepoint 1, same keys as above.
        
    Returns:
        dict: Dictionary with comparison metrics:
            - 'max_diameter_tp1' (float)
            - 'diameter_diff' (float) (tp1 - tp0)
            - 'num_lesions_tp1' (int)
            - 'num_lesions_diff' (int) (tp1 - tp0)
            - 'total_volume_tp1' (float)
            - 'total_volume_diff' (float) (tp1 - tp0)
            - 'max_lesion_slice_tp1' (int)x
    """
    max_diameter_tp1 = tp1_metrics.get('max_diameter_cm', 0)
    max_diameter_tp0 = tp0_metrics.get('max_diameter_cm', 0)
    
    num_lesions_tp1 = tp1_metrics.get('num_lesions', 0)
    num_lesions_tp0 = tp0_metrics.get('num_lesions', 0)
    
    total_volume_tp1 = tp1_metrics.get('total_volume_ml', 0)
    total_volume_tp0 = tp0_metrics.get('total_volume_ml', 0)
    
    max_lesion_slice_tp1 = tp1_metrics.get('max_lesion_slice', None)
    
    return {
        'max_diameter_tp1': max_diameter_tp1,
        'diameter_diff': max_diameter_tp1 - max_diameter_tp0,
        'num_lesions_tp1': num_lesions_tp1,
        'num_lesions_diff': num_lesions_tp1 - num_lesions_tp0,
        'total_volume_tp1': total_volume_tp1,
        'total_volume_diff': total_volume_tp1 - total_volume_tp0,
        'max_lesion_slice_tp1': max_lesion_slice_tp1,
    }



tp0 = {
    'max_diameter_cm': 1.2,
    'num_lesions': 3,
    'total_volume_ml': 5.0,
    'max_lesion_slice': 25
}

tp1 = {
    'max_diameter_cm': 1.5,
    'num_lesions': 4,
    'total_volume_ml': 6.3,
    'max_lesion_slice': 28
}

comparison = compare_lesion_metrics(tp0, tp1)
print(comparison)