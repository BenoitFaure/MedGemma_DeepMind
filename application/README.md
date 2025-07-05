# MedGemma Application

A comprehensive medical imaging analysis platform that combines AI-powered MRI segmentation, report generation, and intelligent chat assistance for ARIA-E monitoring in Alzheimer's disease treatment.

## 🧠 Overview

This application provides:
- **MRI Segmentation**: Automated brain lesion segmentation using nnU-Net
- **Report Generation**: Comprehensive medical reports with HTML, JSON, and PDF outputs
- **AI Chat Assistant**: MedGemma-powered clinical radiology assistant with RAG capabilities
- **Interactive Frontend**: Next.js-based web interface for visualization and interaction

## 🏗️ Architecture

```
application/
├── back.py                 # FastAPI backend server
├── back_segmentation.py    # MRI segmentation pipeline
├── back_report.py          # Report generation (HTML/JSON/PDF)
├── back_chat.py           # Citation parsing and chat utilities
├── back_irm_analysis.py   # MRI analysis with MedGemma
├── back_environment.py    # Environment configuration
├── front/                 # Next.js frontend application
│   ├── app/              # Next.js app directory
│   ├── public/           # Static assets and MRI data
│   └── package.json      # Node.js dependencies
└── requirements.txt       # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 18+** and npm
- **Google Cloud Platform** account with Vertex AI enabled
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/BenoitFaure/MedGemma_DeepMind.git
cd MedGemma_DeepMind/application
```

### 2. Backend Setup (Python/FastAPI)

#### Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment

Create or update `back_environment.py` with your GCP settings:

```python
# GCP Configuration
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"
MEDGEMMA_ENDPOINT_ID = "your-medgemma-endpoint-id"
MEDGEMMA_FT_ENDPOINT_ID = "your-finetuned-endpoint-id"
# ... other configuration
```

#### Set up Google Cloud Authentication

```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
gcloud config set project your-gcp-project-id
```

#### Run the Backend Server

```bash
# Start FastAPI server
python back.py
```

<!-- # Or using uvicorn directly
uvicorn back:app --host 0.0.0.0 --port 8000 --reload -->

The backend will be available at: `http://localhost:8000`

### 3. Frontend Setup (Next.js)

#### Navigate to Frontend Directory

```bash
cd front
```

#### Install Node.js Dependencies

```bash
# Install packages
npm install

# Or using yarn
yarn install
```

#### Run the Development Server

```bash
# Start Next.js development server
npm run dev

# Or using yarn
yarn dev
```

The frontend will be available at: `http://localhost:3000`

## 📡 API Endpoints

### Backend API (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and health check |
| `/seg` | POST | Run MRI segmentation pipeline |
| `/report` | POST | Generate medical reports (HTML/JSON/PDF) |
| `/chat/start` | POST | Initialize chat session with patient data |
| `/chat/send` | POST | Send message to AI assistant |

### Example API Usage

```bash
# Health check
curl http://localhost:8000/

# Run segmentation
curl -X POST http://localhost:8000/seg

# Generate report
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{"client_name": "John Doe"}'

# Start chat session
curl -X POST http://localhost:8000/chat/start \
  -H "Content-Type: application/json" \
  -d '{"client_name": "John Doe"}'
```

## 🔧 Configuration

### Environment Variables

Key configuration files:
- `back_environment.py` - GCP and AI model configuration
- `front/next.config.ts` - Next.js configuration
- `requirements.txt` - Python dependencies
- `front/package.json` - Node.js dependencies

### MRI Data Structure

```
front/public/mri/
├── 0/                     # Patient scan 1
│   └── mri_file.nii      # Original MRI file
├── 1/                     # Patient scan 2
│   └── mri_file.nii      # Original MRI file
├── 0.seg/                # Segmentation results for scan 1
│   └── mri_file.nii      # Segmented MRI file
└── 1.seg/                # Segmentation results for scan 2
    └── mri_file.nii      # Segmented MRI file
```

## 🏥 Usage Workflow

### 1. Upload MRI Data
Place MRI files in the appropriate directories under `front/public/mri/`

### 2. Run Segmentation
```bash
# Via API
curl -X POST http://localhost:8000/seg

# Or through the web interface at http://localhost:3000
```

### 3. Generate Reports
```bash
# Generate comprehensive report
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Patient Name"}'
```

Reports will be saved in `front/public/report/`:
- `report.html` - Interactive HTML report
- `report.json` - Raw data in JSON format
- `report.pdf` - Professional PDF report

### 4. Chat with AI Assistant
- Start a chat session through the web interface
- Ask questions about patient data and analysis
- Get AI-powered insights with scientific citations

## 🛠️ Development

### Backend Development

```bash
# Run with auto-reload
uvicorn back:app --reload

# Run tests (if available)
python -m pytest

# Format code
black *.py
```

### Frontend Development

```bash
cd front

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 📊 Features

### Medical Image Analysis
- Automated brain lesion segmentation
- Volume and diameter measurements
- Longitudinal comparison analysis
- ARIA-E severity grading

### Report Generation
- Professional medical reports
- Multiple output formats (HTML, JSON, PDF)
- Interactive visualizations
- Chart.js integration for data visualization

### AI Chat Assistant
- MedGemma-powered clinical insights
- RAG (Retrieval-Augmented Generation) capabilities
- Scientific literature citations
- Context-aware medical conversations

## 🔍 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check Python environment and dependencies
   - Verify GCP authentication
   - Ensure ports 8000 is available

2. **Frontend connection issues**
   - Verify backend is running on port 8000
   - Check CORS configuration in `back.py`
   - Ensure frontend is on port 3000

3. **Segmentation failures**
   - Verify MRI files are in correct format (.nii)
   - Check nnU-Net endpoint configuration
   - Review GCP quota and permissions

4. **PDF generation issues**
   - Install weasyprint: `pip install weasyprint`
   - Check system dependencies for weasyprint

### Logs and Debugging

```bash
# Backend logs
python back.py  # Check console output

# Frontend logs
cd front && npm run dev  # Check browser console
```

## 📚 Dependencies

### Python (Backend)
- FastAPI - Web framework
- nibabel - NIfTI file handling
- numpy, scipy - Scientific computing
- cv2 - Image processing
- google-cloud-aiplatform - Vertex AI integration

### Node.js (Frontend)
- Next.js - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Chart.js - Data visualization