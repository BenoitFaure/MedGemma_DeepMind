# MedGemma Fine-Tuning for Brain Region Classification

This repository contains code for fine-tuning Google's MedGemma-4B model to classify brain regions where edema spans the most in medical brain scans. The project uses LoRA (Low-Rank Adaptation) for efficient fine-tuning and compares performance against the baseline model.

## 🎯 Task Overview

The model classifies brain regions into four categories:
- **A: frontal** - Frontal lobe
- **B: occipital** - Occipital lobe  
- **C: parietal** - Parietal lobe
- **D: temporal** - Temporal lobe

Given a brain scan image, the model answers: *"What brain region does the edema span the most?"*

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (40GB+ VRAM recommended)
- GPU with bfloat16 support (compute capability >= 8.0)
- Hugging Face account with access to MedGemma model

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medgemma_ft.git
cd medgemma_ft
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Login to Hugging Face:
```bash
huggingface-cli login
```

### Dataset Setup

Organize your dataset in the following structure:
```
packaged_dataset/
├── slices_train/          # Training images (.jpg)
├── slices_test/           # Test images (.jpg)
├── train_labels.txt       # Training labels (one per line)
└── test_label.txt         # Test labels (one per line)
```

**Label format**: Each line should contain one of: `frontal`, `occipital`, `parietal`, `temporal`

## 📊 Usage

### 1. Fine-Tuning

Run the fine-tuning script:
```bash
python main.py
```

**Key parameters:**
- **Epochs**: 3
- **Learning Rate**: 2e-4
- **Batch Size**: 4 per device
- **LoRA Rank**: 16
- **LoRA Alpha**: 16

The fine-tuned model will be saved to `medgemma-4b-it-sft-lora-brain-regions/` and pushed to Hugging Face Hub.

### 2. Evaluation

Compare baseline vs fine-tuned model performance:
```bash
python eval.py
```

This script:
- Loads the baseline MedGemma-4B model
- Loads your fine-tuned model
- Evaluates both on the test set
- Reports accuracy and F1-score metrics

### 3. Dataset Processing

The dataset processing is handled automatically, but you can also run it standalone:
```bash
python dataset_functions.py
```

## 🛠️ Key Components

### `main.py` - Fine-Tuning Pipeline
- Loads MedGemma-4B with 4-bit quantization
- Applies LoRA configuration for efficient training
- Uses custom collate function for image-text pairs
- Implements gradient checkpointing for memory efficiency

### `eval.py` - Model Evaluation
- Compares baseline vs fine-tuned model performance
- Implements intelligent response parsing
- Handles both exact and partial matching
- Provides detailed debugging output

### `dataset_functions.py` - Data Processing
- Converts custom dataset to Hugging Face format
- Handles image loading and label mapping
- Creates proper train/test splits
- Formats data for conversation-style training

## 🔧 Configuration

### Model Parameters
```python
# LoRA Configuration
lora_alpha = 16
lora_dropout = 0.05
r = 16
target_modules = "all-linear"

# Training Configuration
num_train_epochs = 3
per_device_train_batch_size = 4
gradient_accumulation_steps = 4
learning_rate = 2e-4
```

### Generation Settings
```python
# For deterministic results
do_sample = False
max_new_tokens = 40
```

## 📈 Results

The evaluation script provides:
- **Accuracy**: Overall classification accuracy
- **F1-Score**: Weighted F1-score across all classes
- **Comparison**: Baseline vs fine-tuned model performance

Example output:
```
Baseline metrics: {'accuracy': 0.042, 'f1': 0.076}
Fine-tuned metrics: {'accuracy': 0.5, 'f1': 0.474}
```

## 🎛️ Advanced Usage

### Custom Dataset Path
Modify the dataset path in `dataset_functions.py`:
```python
dataset_path = "./your_custom_dataset"
```

### Hyperparameter Tuning
Adjust training parameters in `main.py`:
```python
learning_rate = 1e-4  # Lower learning rate
num_train_epochs = 5  # More epochs
r = 32               # Higher LoRA rank
```

### Memory Optimization
For smaller GPUs, reduce batch size:
```python
per_device_train_batch_size = 2
gradient_accumulation_steps = 8
```

## 🔍 Troubleshooting

### Common Issues

1. **Empty Model Responses**
   - Check padding configuration matches training
   - Verify input format (user messages only during inference)
   - Ensure sufficient `max_new_tokens`

2. **CUDA Out of Memory**
   - Reduce batch size
   - Enable gradient checkpointing
   - Use smaller LoRA rank

3. **Label Mismatch Errors**
   - Verify label format in text files
   - Check for typos (e.g., "parietel" vs "parietal")
   - Ensure consistent label naming

### Debug Mode
Enable detailed logging in `eval.py`:
```python
print(f"Response text: '{response_text}' (length: {len(response_text)})")
```

## 📋 Dependencies

Core dependencies:
- `transformers` - Hugging Face transformers
- `torch` - PyTorch deep learning framework
- `peft` - Parameter-Efficient Fine-Tuning
- `trl` - Transformer Reinforcement Learning
- `datasets` - Hugging Face datasets
- `bitsandbytes` - 4-bit quantization
- `evaluate` - Model evaluation metrics

See `requirements.txt` for complete list with versions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google for the MedGemma model
- Hugging Face for the transformers library
