import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

def nii_axial_rotated_base64(nii_img, slice_idx, seg_mask=None):
    """
    Generate rotated base64 PNG from axial slice with optional segmentation overlay.
    """
    data = nii_img.get_fdata()
    slice_img = data[slice_idx, :, :]
    
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.axis('off')
    # Rotate images by 270 degrees (90 degrees clockwise)
    rotated_img = np.rot90(slice_img.T, k=3)
    ax.imshow(rotated_img, cmap='gray', origin='upper')
    
    if seg_mask is not None:
        overlay = seg_mask[slice_idx, :, :]
        # Rotate segmentation mask by 270 degrees (90 degrees clockwise) to match
        rotated_overlay = np.rot90(overlay.T, k=3)
        # Create a custom red colormap for better visibility
        from matplotlib.colors import ListedColormap
        red_cmap = ListedColormap(['red'])
        ax.imshow(np.ma.masked_where(rotated_overlay == 0, rotated_overlay), cmap=red_cmap, alpha=0.6, origin='upper')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

def generate_ariae_html_report(comparison_dict, tp0_nii_path, tp1_nii_path, tp1_seg_path):
    tp0_nii = nib.load(tp0_nii_path)
    tp1_nii = nib.load(tp1_nii_path)
    tp1_seg = nib.load(tp1_seg_path).get_fdata()
    tp1_seg_bin = (tp1_seg > 0).astype(np.float32)
    
    slice_idx = comparison_dict.get('max_lesion_slice_tp1', 0)

    # Image generation
    img_tp0 = nii_axial_rotated_base64(tp0_nii, slice_idx)
    img_tp1 = nii_axial_rotated_base64(tp1_nii, slice_idx)
    img_tp1_overlay = nii_axial_rotated_base64(tp1_nii, slice_idx, seg_mask=tp1_seg_bin)

    # Scan dates - adding a third timepoint
    date_baseline = "2024-06-01"
    date_tp0 = "2024-10-01" 
    date_tp1 = "2025-03-01"

    # Create dummy baseline value
    baseline_diameter = comparison_dict['max_diameter_tp1'] - comparison_dict['diameter_diff'] - 0.2
    tp0_diameter = comparison_dict['max_diameter_tp1'] - comparison_dict['diameter_diff']
    tp1_diameter = comparison_dict['max_diameter_tp1']

    # HTML with improved styling
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ARIA-E Monitoring Report</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 40px; 
            background: #f8f9fa; 
            color: #333; 
            line-height: 1.5;
            font-size: 16px;
        }}
        
        h1 {{ 
            font-size: 36px; 
            margin-bottom: 8px; 
            color: #2c3e50;
            font-weight: 600;
        }}
        
        .subtitle {{ 
            font-size: 18px; 
            color: #7f8c8d; 
            margin-bottom: 30px; 
            font-weight: 300;
        }}

        /* Header cards - matching first screenshot */
        .header-cards {{ 
            display: flex; 
            gap: 20px; 
            margin-bottom: 40px; 
        }}
        
        .header-card {{ 
            background: white; 
            border-radius: 12px; 
            padding: 20px 25px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
            flex: 1;
            border-left: 4px solid #3498db;
        }}
        
        .header-card h3 {{ 
            margin: 0 0 15px 0; 
            font-size: 18px; 
            color: #2c3e50; 
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .header-card p {{ 
            margin: 8px 0; 
            font-size: 16px; 
            color: #555;
        }}
        
        .header-card .label {{ 
            font-weight: 500; 
            color: #34495e;
        }}

        /* Metrics boxes - PDF-friendly professional styling */
        .metrics-section {{ 
            margin: 40px 0; 
        }}
        
        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }}
        
        .metric-card {{ 
            background: #f8f9fa;
            border: 2px solid #3498db;
            border-radius: 12px; 
            padding: 25px 20px; 
            text-align: center; 
            color: #2c3e50; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .metric-card h4 {{ 
            margin: 0 0 12px 0; 
            font-size: 16px; 
            color: #34495e;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{ 
            font-size: 36px; 
            font-weight: 700; 
            margin: 12px 0; 
            color: #2c3e50;
        }}
        
        .metric-change {{ 
            font-size: 18px; 
            font-weight: 600;
        }}
        
        .metric-change.positive {{ 
            color: #c0392b; 
        }}
        
        .metric-change.negative {{ 
            color: #27ae60; 
        }}
        
        /* Print-specific styles */
        @media print {{
            .metric-card {{
                background: white !important;
                border: 2px solid #3498db !important;
                color: black !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .metric-card h4 {{
                color: black !important;
            }}
            .metric-value {{
                color: black !important;
            }}
            .metric-change.positive {{
                color: #c0392b !important;
            }}
        }}

        /* Chart section */
        .chart-section {{ 
            background: white; 
            border-radius: 12px; 
            padding: 40px 40px 50px 40px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
            margin: 40px 0;
        }}
        
        .chart-title {{ 
            font-size: 24px; 
            margin-bottom: 30px; 
            color: #2c3e50; 
            font-weight: 600;
        }}
        
        .chart-container {{
            position: relative;
            height: 420px;
            width: 100%;
            padding: 0;
            box-sizing: border-box;
        }}

        /* Visualization section */
        .visualization {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 10px; 
        }}
        
        .visualization img {{ 
            width: 32%; 
            border-radius: 8px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .visualization-labels {{ 
            display: flex; 
            justify-content: space-between; 
            margin-bottom: 30px; 
            font-size: 15px; 
            color: #666; 
            font-weight: 500;
        }}
        
        .visualization-labels > div {{
            width: 32%;
            text-align: center;
        }}

        h2 {{ 
            font-size: 24px; 
            margin: 40px 0 20px 0; 
            color: #2c3e50; 
            font-weight: 600;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
</head>
<body>
    <h1>ARIA-E Monitoring</h1>
    <div class="subtitle">Longitudinal Screening Report</div>

    <div class="header-cards">
        <div class="header-card">
            <h3>Patient Information</h3>
            <p><span class="label">Patient Name:</span> ARIA-E</p>
            <p><span class="label">Referring MD:</span> Physician ABC</p>
            <p><span class="label">Age:</span> 61</p>
            <p><span class="label">Patient ID:</span> E0123456</p>
        </div>
        <div class="header-card">
            <h3>Report Information</h3>
            <p><span class="label">Current Scan Date:</span> {date_tp1}</p>
            <p><span class="label">Prior Scan Date:</span> {date_tp0}</p>
            <p><span class="label">Baseline Scan Date:</span> {date_baseline}</p>
        </div>
        <div class="header-card">
            <h3>Site Information</h3>
            <p><span class="label">Academic Imaging Center</span></p>
            <p><span class="label">5555 Radiology Drive</span></p>
            <p><span class="label">San Diego, CA 92122</span></p>
        </div>
    </div>

    <h2>Lesion Visualization</h2>
    <div class="visualization">
        <img src="{img_tp0}" alt="TP0">
        <img src="{img_tp1}" alt="TP1">
        <img src="{img_tp1_overlay}" alt="TP1 + Seg">
    </div>
    <div class="visualization-labels">
        <div>{date_tp0}</div>
        <div>{date_tp1}</div>
        <div>{date_tp1} + Segmentation</div>
    </div>

    <div class="metrics-section">
        <div class="metrics-grid">
            <div class="metric-card">
                <h4>Max Diameter</h4>
                <div class="metric-value">{comparison_dict['max_diameter_tp1']:.1f} cm</div>
                <div class="metric-change positive">({comparison_dict['diameter_diff']:+.1f})</div>
            </div>
            <div class="metric-card">
                <h4>Total Lesion Volume</h4>
                <div class="metric-value">{comparison_dict['total_volume_tp1']:.1f} mL</div>
                <div class="metric-change positive">({comparison_dict['total_volume_diff']:+.1f})</div>
            </div>
            <div class="metric-card">
                <h4>Sites of Involvement</h4>
                <div class="metric-value">{comparison_dict['num_lesions_tp1']}</div>
                <div class="metric-change positive">({comparison_dict['num_lesions_diff']:+d})</div>
            </div>
            <div class="metric-card">
                <h4>Radiographic Grading</h4>
                <div class="metric-value" style="font-size: 20px;">Mild</div>
            </div>
        </div>
    </div>

    <div class="chart-section">
        <div class="chart-title">Lesion Size Evolution</div>
        <div class="chart-container">
            <canvas id="evolutionChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('evolutionChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['{date_baseline}', '{date_tp0}', '{date_tp1}'],
                datasets: [{{
                    label: 'Max Diameter (cm)',
                    data: [{baseline_diameter:.2f}, {tp0_diameter:.2f}, {tp1_diameter:.2f}],
                    borderColor: '#3498db',
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    pointBackgroundColor: '#3498db',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    fill: false,
                    tension: 0.3
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
                layout: {{
                    padding: 0
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        title: {{
                            display: true,
                            text: 'Diameter (cm)',
                            font: {{
                                weight: 'bold'
                            }}
                        }},
                        grid: {{
                            color: 'rgba(0,0,0,0.05)'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Scan Date',
                            font: {{
                                weight: 'bold'
                            }}
                        }},
                        grid: {{
                            color: 'rgba(0,0,0,0.05)'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """
    return html

# Example usage
comparison = {
    'max_diameter_tp1': 1.5, 
    'diameter_diff': 0.3, 
    'num_lesions_tp1': 4, 
    'num_lesions_diff': 1, 
    'total_volume_tp1': 6.3, 
    'total_volume_diff': 1.3, 
    'max_lesion_slice_tp1': 28
}

html_report = generate_ariae_html_report(comparison, 'LUMIERE_001_0000.nii.gz', 'LUMIERE_001_0000.nii.gz', 'LUMIERE_001.nii.gz')
with open("lesion_report_improved.html", "w") as f:
    f.write(html_report)

