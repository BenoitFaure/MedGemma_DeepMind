import os
from typing import Any
from datasets import Dataset, DatasetDict, Features, Value, Image, ClassLabel

BRAIN_CLASSES = [
    "A: frontal",
    "B: occipital",
    "C: parietal",
    "D: temporal",
]
options = "\n".join(BRAIN_CLASSES)
PROMPT = f"What brain region does the edema span the most?\n{options}"

def format_data(example: dict[str, Any]) -> dict[str, Any]:
    example["messages"] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                },
                {
                    "type": "text",
                    "text": PROMPT,
                },
            ],
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": BRAIN_CLASSES[example["label"]],
                },
            ],
        },
    ]
    return example

def process_custom_dataset(dataset_path):
    """
    Process custom dataset to make it compatible with Hugging Face load_dataset function.

    Args:
        dataset_path (str): Path to the packaged_dataset directory

    Returns:
        DatasetDict: Processed dataset ready for Hugging Face
    """

    # Define paths
    train_images_path = os.path.join(dataset_path, "slices_train")
    test_images_path = os.path.join(dataset_path, "slices_test")
    train_labels_path = os.path.join(dataset_path, "train_labels.txt")
    test_labels_path = os.path.join(dataset_path, "test_label.txt")

    # Read label files and filter out empty lines
    with open(train_labels_path, 'r') as f:
        train_labels = [line.strip().replace("parietel", "parietal") for line in f.readlines() if line.strip()]

    with open(test_labels_path, 'r') as f:
        test_labels = [line.strip().replace("parietel", "parietal") for line in f.readlines() if line.strip()]

    # Get unique classes and create label mapping (filter out empty strings)
    all_labels = list(set(train_labels + test_labels))
    full_labels = []
    for label in all_labels:
        if label in [elem.split(":")[1].strip() for elem in BRAIN_CLASSES]:
            full_labels.append(label)
        else:
            raise ValueError(f"Label {label} not found in BRAIN_CLASSES")
    label_to_id = {label: idx for idx, label in enumerate(sorted(full_labels))}
    id_to_label = {idx: label for label, idx in label_to_id.items()}

    print(f"Classes found: {sorted(full_labels)}")
    print(f"Label mapping: {label_to_id}")

    # Verify we have the expected number of labels
    if len(train_labels) != len([f for f in os.listdir(train_images_path) if f.lower().endswith('.jpg')]):
        print(f"WARNING: Number of train labels ({len(train_labels)}) doesn't match number of train images")
    if len(test_labels) != len([f for f in os.listdir(test_images_path) if f.lower().endswith('.jpg')]):
        print(f"WARNING: Number of test labels ({len(test_labels)}) doesn't match number of test images")

    # Process training data
    train_image_files = sorted([f for f in os.listdir(train_images_path) if f.lower().endswith('.jpg')])
    train_data = []

    for idx, (image_file, label) in enumerate(zip(train_image_files, train_labels)):
        image_path = os.path.join(train_images_path, image_file)
        train_data.append({
            'image': image_path,
            'label': label_to_id[label],
            'text': label  # Keep original text label as well
        })

    # Process test data
    test_image_files = sorted([f for f in os.listdir(test_images_path) if f.lower().endswith('.jpg')])
    test_data = []

    for idx, (image_file, label) in enumerate(zip(test_image_files, test_labels)):
        image_path = os.path.join(test_images_path, image_file)
        test_data.append({
            'image': image_path,
            'label': label_to_id[label],
            'text': label  # Keep original text label as well
        })

    # Define features
    features = Features({
        'image': Image(),
        'label': ClassLabel(names=sorted(full_labels)),
        'text': Value('string')
    })

    # Create datasets
    train_dataset = Dataset.from_list(train_data, features=features)
    test_dataset = Dataset.from_list(test_data, features=features)

    # Create DatasetDict
    dataset_dict = DatasetDict({
        'train': train_dataset,
        'test': test_dataset
    })

    print(f"Training samples: {len(train_dataset)}")
    print(f"Test samples: {len(test_dataset)}")

    return dataset_dict

def save_dataset_for_huggingface(dataset_dict, output_path):
    """
    Save the processed dataset in a format that can be loaded with load_dataset.

    Args:
        dataset_dict (DatasetDict): Processed dataset
        output_path (str): Path to save the dataset
    """
    # Save the dataset
    dataset_dict.save_to_disk(output_path)

    # Create a simple dataset loading script
    dataset_script = f'''
import os
from datasets import load_from_disk

def load_dataset():
    return load_from_disk("{output_path}")
'''

    with open(os.path.join(output_path, "load_dataset.py"), "w") as f:
        f.write(dataset_script)

    print(f"Dataset saved to {output_path}")
    print(f"To load: from datasets import load_from_disk; dataset = load_from_disk('{output_path}')")

# Usage example for Google Colab
def setup_and_process_dataset():
    """
    Complete setup function for Google Colab usage
    """
    # Install required packages (run this in a cell first)
    # !pip install datasets pillow

    # Set your dataset path
    dataset_path = "./packaged_dataset"  # Adjust this path as needed
    output_path = "./processed_dataset"

    # Process the dataset
    dataset_dict = process_custom_dataset(dataset_path)

    # Save for later use
    save_dataset_for_huggingface(dataset_dict, output_path)

    # Display some examples
    print("\nExample from training set:")
    print(dataset_dict['train'][0])
    print("\nExample from test set:")
    print(dataset_dict['test'][0])

    return dataset_dict



# Simple execution for Colab
if __name__ == "__main__":
    # For Google Colab, uncomment and run:
    data = setup_and_process_dataset()