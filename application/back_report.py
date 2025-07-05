import json
import numpy as np
import nibabel as nb
from scipy.ndimage import label
from scipy.ndimage import center_of_mass, distance_transform_edt
import cv2
import os
from back_irm_analysis import run_analysis_location, run_analysis

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    print("Warning: weasyprint not installed. PDF generation will not be available.")
    print("Install with: pip install weasyprint")
    WEASYPRINT_AVAILABLE = False

MRI_FOLDER = "./front/public/mri"
REPORT_FOLDER = "./front/public/report"

REPORT_TEMPLATE = """<!DOCTYPE html>
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
            <p><span class="label">Patient Name:</span> {patient_name}</p>
            <p><span class="label">Referring MD:</span> {referring_md}</p>
            <p><span class="label">Age:</span> {age}</p>
            <p><span class="label">Patient ID:</span> {patient_id}</p>
        </div>
        <div class="header-card">
            <h3>Report Information</h3>
            <p><span class="label">Current Scan Date:</span> {date_tp1}</p>
            <p><span class="label">Prior Scan Date:</span> {date_tp0}</p>
            <p><span class="label">Baseline Scan Date:</span> {date_previous}</p>
        </div>
        <div class="header-card">
            <h3>Site Information</h3>
            <p><span class="label">Google France Hospital</span></p>
            <p><span class="label">8 rue de Londres</span></p>
            <p><span class="label">Paris, 75009 FRANCE</span></p>
        </div>
    </div>

    <h2>Lesion Visualization</h2>
    <div class="visualization">
        <img src="{img_tp0}" alt="TP0">
        <img src="{img_tp1}" alt="TP1">
        <img src="{difference}" alt="TP1 + Seg">
    </div>
    <div class="visualization-labels">
        <div>{date_tp0}</div>
        <div>{date_tp1}</div>
        <div>Segmentation</div>
    </div>

    <div class="metrics-section">
        <div class="metrics-grid">
            <div class="metric-card">
                <h4>Max Diameter</h4>
                <div class="metric-value">{diameter:.1f} cm</div>
                <div class="metric-change positive">({diameter_change:+.1f})</div>
            </div>
            <div class="metric-card">
                <h4>Total Volume</h4>
                <div class="metric-value">{total_volume:.1f} mL</div>
                <div class="metric-change positive">({total_volume_change:+.1f})</div>
            </div>
            <div class="metric-card">
                <h4>Sites of Involvement</h4>
                <div class="metric-value">{num_lesions_tp1}</div>
                <div class="metric-change positive">({num_lesions_diff:+d})</div>
            </div>
            <div class="metric-card">
                <h4>Radiographic Grading</h4>
                <div class="metric-value" style="font-size: 20px;">{radiographic_grading}</div>
            </div>
        </div>
    </div>

    <div class="chart-section">
        <div class="chart-title">Volumes Evolution</div>
        <div class="chart-container">
            <canvas id="evolutionChart"></canvas>
        </div>
    </div>

    <script>
        const ctx = document.getElementById('evolutionChart').getContext('2d');
        const chart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['{date_previous}', '{date_tp0}', '{date_tp1}'],
                datasets: [{{
                    label: 'Max Diameter (cm)',
                    data: [{previous_diameter:.2f}, {tp0_diameter:.2f}, {tp1_diameter:.2f}],
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

def find_biggest_difference_slice(segmentation_t0, segmentation_t1):
    diff = np.abs(segmentation_t1 - segmentation_t0)
    max_diff_index = np.argmax(np.sum(diff, axis=(1, 2)))
    return max_diff_index

def generate_client_report(client_name):
    info = {
        "client_name": client_name,
        "time0": "2025-03-24",
        "time1": "2025-04-18",
        "rmi_location": run_analysis_location(1),
    }

    seg_t0_slices = nb.load("./front/public/mri/0.seg/mri_file.nii").get_fdata()
    seg_t1_slices = nb.load("./front/public/mri/1.seg/mri_file.nii").get_fdata()

    volume_t0 = float(compute_volume(seg_t0_slices))
    volume_t1 = float(compute_volume(seg_t1_slices))
    volume_change = volume_t1 - volume_t0
    biggest_diff_slice = int(find_biggest_difference_slice(seg_t0_slices, seg_t1_slices))
    info["biggest_diff_slice"] = biggest_diff_slice
    info["volume_t0"] = volume_t0
    info["volume_t1"] = volume_t1
    info["volume_change"] = volume_change
    info["oedemas_t0"] = float(compute_number_of_oedemas(seg_t0_slices))
    info["oedemas_t1"] = float(compute_number_of_oedemas(seg_t1_slices))
    info["max_diameter_t0"] = float(compute_max_diameter(seg_t0_slices))
    info["max_diameter_t1"] = float(compute_max_diameter(seg_t1_slices))

    info["previous_volumes"] = {
        "2025-02-27": float(volume_t0 - (volume_change / 2)),
    }

    info["severity"], info["severity_reason"] = run_analysis(1)

    return info

def generate_html(info_json):
    out = REPORT_TEMPLATE.format(
        patient_name=info_json["client_name"],
        referring_md="Dr. Roger",
        age="65",
        patient_id="123456789",
        date_tp1=info_json["time1"],
        date_tp0=info_json["time0"],
        date_previous=list(info_json["previous_volumes"].keys())[0],
        img_tp0=f"/mri/0.seg/slice_{str(info_json['biggest_diff_slice']).zfill(3)}.jpg",
        img_tp1=f"/mri/1.seg/slice_{str(info_json['biggest_diff_slice']).zfill(3)}.jpg",
        difference=f"/mri/difference/slice_{str(info_json['biggest_diff_slice']).zfill(3)}.jpg",
        diameter=info_json["max_diameter_t1"],
        diameter_change=info_json["max_diameter_t1"] - info_json["max_diameter_t0"],
        total_volume=info_json["volume_t1"],
        total_volume_change=info_json["volume_change"],
        num_lesions_tp1=int(info_json["oedemas_t1"]),
        num_lesions_diff=int(info_json["oedemas_t1"] - info_json["oedemas_t0"]),
        radiographic_grading=info_json["severity"],
        previous_diameter=info_json["max_diameter_t0"],
        tp0_diameter=info_json["max_diameter_t0"],
        tp1_diameter=info_json["max_diameter_t1"]
    )
    return out

# HTML and JSON ##################
def save_html(html):
    save_path = f"{REPORT_FOLDER}/report.html"
    with open(save_path, "w") as f:
        f.write(html)
    return save_path

def save_json(info_json):
    save_path = f"{REPORT_FOLDER}/report.json"
    with open(save_path, "w") as f:
        json.dump(info_json, f, indent=4)
    return save_path

def load_json():
    save_path = f"{REPORT_FOLDER}/report.json"
    with open(save_path, "r") as f:
        try:
            info_json = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            info_json = {}
    return info_json

# PDF GENERATION ##################
def generate_pdf_from_html(html_content, output_path=None):
    """
    Convert HTML content to PDF using weasyprint
    
    Args:
        html_content (str): HTML content to convert to PDF
        output_path (str, optional): Path where to save the PDF. If None, saves to REPORT_FOLDER/report.pdf
        
    Returns:
        str: Path to the generated PDF file
        
    Raises:
        ImportError: If weasyprint is not installed
        Exception: If PDF generation fails
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("weasyprint is not installed. Install with: pip install weasyprint")
    
    try:
        # Set default output path if not provided
        if output_path is None:
            output_path = f"{REPORT_FOLDER}/report.pdf"
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create HTML document from string
        html_doc = HTML(string=html_content)
        
        # Optional: Add custom CSS for better PDF formatting
        pdf_css = CSS(string="""
            @page {
                size: A4;
                margin: 1cm;
            }
            
            /* Ensure images fit on page */
            .visualization img {
                max-width: 100%;
                height: auto;
            }
            
            /* Better chart rendering for PDF */
            .chart-container {
                page-break-inside: avoid;
            }
            
            /* Prevent page breaks inside metric cards */
            .metric-card {
                page-break-inside: avoid;
            }
            
            /* Header cards page break control */
            .header-cards {
                page-break-inside: avoid;
            }
        """)
        
        # Generate PDF
        html_doc.write_pdf(output_path, stylesheets=[pdf_css])
        
        print(f"PDF successfully generated: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise

def save_pdf(html_content, output_path=None):
    """
    Convenience function to save HTML as PDF
    
    Args:
        html_content (str): HTML content to convert
        output_path (str, optional): Output path for PDF
        
    Returns:
        str: Path to generated PDF file
    """
    return generate_pdf_from_html(html_content, output_path)



if __name__ == "__main__":
    client_name = "John Doe"
    info_json = generate_client_report(client_name)
    html_content = generate_html(info_json)
    
    # Save HTML
    save_html(html_content)
    
    # Save JSON
    save_json(info_json)
    
    # Generate PDF
    try:
        pdf_path = save_pdf(html_content)
        print(f"Report generated successfully!")
        print(f"HTML: {REPORT_FOLDER}/report.html")
        print(f"JSON: {REPORT_FOLDER}/report.json")
        print(f"PDF: {pdf_path}")
    except ImportError as e:
        print(f"PDF generation skipped: {e}")
    except Exception as e:
        print(f"PDF generation failed: {e}")


# Generates a Json with the following information:
# - Client Info
# - IRM Analysis
# - Segmentation Analysis
# - Stats
# - MedGemma Analysis

# Much of the information is contained in frontend