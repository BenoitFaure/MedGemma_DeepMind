# 🧠GemmARIA: AI-Powered Neurological Support for Anti-Amyloid Therapies

![Project Banner](https://placehold.co/1200x300?text=GemmARIA)

## 🌟 Overview

This project aims to support neurologists in monitoring patients undergoing anti-amyloid therapy for Alzheimer's disease — treatments that, while promising, can cause side effects such as **Amyloid-Related Imaging Abnormalities with edema (ARIA-E)**, which leads to brain edema visible on FLAIR MRI scans. 

Our solution provides physicians with **automated, longitudinal reports** that compare a patient's MRIs over time, highlighting the evolution of these edemas using state-of-the-art **nnU-Net** segmentation outputs. The generated report, which helps assess whether treatment should continue, is refined by **MedGemma** for enhanced clarity and clinical relevance. 

Additionally, a chatbot with access to the latest ARIA-E research through a **Retrieval-Augmented Generation (RAG)** system offers up-to-date scientific context, empowering neurologists to make informed, evidence-based decisions on this cutting-edge therapy.IA: Agentic AI Copilot for Safer Alzheimer Treatment Monitoring

## 🚀 Key Contributions

- 🎯 **Automated Edema Segmentation**: Leverages a custom-trained nnU-Net model to accurately identify and segment ARIA-E regions in FLAIR MRI scans.
- 📊 **Patient Reports**: Generates reports comparing a patient's current and previous MRI scans to track edema evolution.
- 🤖 **Fine-tuned MedGemma**: Adapted to MRI sequences of both healthy and affected brains to interpret scans and identify the most damaged regions. This enhances the quality and precision of the generated report. Available on [🤗 Hugging Face](https://huggingface.co/axel-darmouni/medgemma-4b-it-sft-lora-brain-regions)
- 📝 **LLM-Refined Reports**: Uses a MedGemma-4b model to produce clear, clinically relevant, and easy-to-understand narrative reports.
- 🔍 **Up-to-Date RAG Knowledge Base**: Integrates a RAG system with MedGemma, providing access to the latest research papers on anti-amyloid therapies and ARIA.
- 🔄 **Automated Knowledge Updates**: A cloud-based pipeline continuously ingests and processes new scientific literature into the RAG database.
- 💬 **Interactive Chatbot**: Allows clinicians to ask complex questions and receive evidence-based answers from the RAG-powered MedGemma-27b.
- 🏥 **Integrated Clinical Workflow**: A user-friendly frontend application that brings all functionalities together to support clinical decision-making.

## ☁️ Google Cloud Tools Used

- 🗄️ **Google Cloud Storage (GCS)** to store and retrieve MRI volumes and host the RAG database.
- 📦 **Artifact Registry** to store the Docker image containing the API and the weights of the nnU-NET.
- 🚀 **Vertex AI** to deploy the models (nnU-Net + API, fine-tuned MedGemma-4b, MedGemma-27b + RAG) as endpoints for inference.


## 🏗️ Technical Architecture

The project is organized into several core components, each with its own detailed documentation. Below is a high-level summary of each part.

### 🎯 1. nnU-Net for ARIA-E Segmentation

We trained a `nnU-Net` model on a private dataset of FLAIR MRI scans to perform robust and accurate segmentation of brain edemas. This model serves as the first step in our pipeline, providing the precise location and volume of ARIA-E.

> 📚 For a detailed explanation of the data preprocessing, training, and inference process, please see the **`nnunet_segmentation/README.md`**.

### 🤖 2. Fine-Tuned MedGemma for MRI Interpretation

We fine-tuned Google's MedGemma model to understand the context of ARIA-E and interpret the segmentation masks from our nnU-Net model. This specialized model is capable of describing the location and changes in edema over time in a structured manner. This model is available on [🤗 Hugging Face](https://huggingface.co/axel-darmouni/medgemma-4b-it-sft-lora-brain-regions)

> 📚 To learn more about the fine-tuning dataset, methodology, and evaluation, refer to the **`medgemma_finetuning/README.md`**.

### 🔍 3. Retrieval-Augmented Generation (RAG) System

To ground MedGemma's responses in the latest scientific evidence, we implemented a RAG system. The knowledge base is built from recent academic papers on ARIA, which are chunked semantically using the Gemini API and stored as embeddings in a vector database on Google Cloud Storage.

> 📚 For details on the RAG architecture, vector database schema, and retrieval strategies, please consult the **`rag_medgemma/README.md`**.

### 🔄 4. Automated Knowledge Base Updates

A crucial part of our RAG system is ensuring the knowledge base remains current. We developed a serverless function on Google Cloud that runs weekly to scrape, download, and process the latest publications on ARIA, automatically updating our vector database.

> 📚 The implementation details of this data ingestion pipeline are available in **`rag_medgemma/README.md`**.

### 📊 5. Report Generation and Refinement

This component integrates the outputs from the nnU-Net and fine-tuned MedGemma models. It takes the segmentation data from two MRIs, generates a preliminary comparative report, and then uses the base MedGemma model to refine the language for clinical clarity and coherence.

### 🖥️ 6. Frontend Application & Chatbot

The entire system is accessible through a web-based frontend. It provides an intuitive interface for uploading MRIs, generating comparative reports, and interacting with the RAG-powered chatbot. This allows neurologists to seamlessly integrate our tool into their workflow.


## 🚀 Getting Started

### 📥 1. Clone the Repository

To set up the project locally, please refer to the `README.md` file within each component's directory, starting with the frontend application.

```bash
# Clone the repository
git clone https://github.com/BenoitFaure/MedGemma_DeepMind.git
cd MedGemma_DeepMind
# Follow instructions in each sub-directory's README
```

### 🐍 2. Backend Setup (Python/FastAPI)

#### Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
```

#### ⚙️ Configure Environment

Create or update `back_environment.py` with your GCP settings:

```python
# GCP Configuration
PROJECT_ID = "your-gcp-project-id"
REGION = "us-central1"
MEDGEMMA_ENDPOINT_ID = "your-medgemma-endpoint-id"
MEDGEMMA_FT_ENDPOINT_ID = "your-finetuned-endpoint-id"
# ... other configuration
```

#### 🔐 Set up Google Cloud Authentication

```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
gcloud config set project your-gcp-project-id
```

#### 🏃‍♂️ Run the Backend Server

```bash
# Start FastAPI server
python back.py
```

The backend will be available at: `http://localhost:8000`

### 🌐 3. Frontend Setup (Next.js)

#### Navigate to Frontend Directory

```bash
cd front
```

#### 📦 Install Node.js Dependencies

```bash
# Install packages
npm install

# Or using yarn
yarn install
```

#### 🏃‍♂️ Run the Development Server

```bash
# Start Next.js development server
npm run dev

# Or using yarn
yarn dev
```

The frontend will be available at: `http://localhost:3000`

## 📄 License

MedGemma is governed by the [Health AI Developer Foundations terms of use](https://developers.google.com/health-ai-developer-foundations/terms).

This integration is licensed under the Apache 2.0 License.

### 📋 Gemmaria Presentation

<embed src="PRESENTATION_GEMMARIA.pdf" type="application/pdf" width="100%" height="600px" />

**Note:** If the PDF doesn't display in your browser, you can [download it directly](./PRESENTATION_GEMMARIA.pdf) or [view it in GitHub](https://github.com/BenoitFaure/MedGemma_DeepMind/blob/main/PRESENTATION_GEMMARIA.pdf).

🤗 IRM Finetuned Model on [HuggingFace](https://huggingface.co/axel-darmouni/medgemma-4b-it-sft-lora-brain-regions)

---

**🧠 Empowering neurologists with AI-driven insights for safer Alzheimer's treatment! ✨**
