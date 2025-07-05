import os
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText, BitsAndBytesConfig
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer
from huggingface_hub import login
from dataset_functions import setup_and_process_dataset, format_data

if __name__ == "__main__":
    login()
    data = setup_and_process_dataset()
    data["validation"] = data.pop("test")
    formatted_data = data.map(format_data)
    model_id = "google/medgemma-4b-it"
    if torch.cuda.get_device_capability()[0] < 8:
        raise ValueError("GPU does not support bfloat16, please use a GPU that supports bfloat16.")

    model_kwargs = dict(
        attn_implementation="eager",
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    #model_kwargs["quantization_config"] = BitsAndBytesConfig(
    #    load_in_8bit=True,
    #    # 8-bit quantization does not use the 4-bit specific arguments
    #)

    model = AutoModelForImageTextToText.from_pretrained(model_id, **model_kwargs)
    processor = AutoProcessor.from_pretrained(model_id)

    # Use right padding to avoid issues during training
    processor.tokenizer.padding_side = "right"

    peft_config = LoraConfig(
        lora_alpha=32,
        lora_dropout=0.1,
        r=32,
        bias="none",
        target_modules="all-linear",
        task_type="CAUSAL_LM",
        modules_to_save=[
            "lm_head",
            "embed_tokens",
        ],
    )

    def collate_fn(examples: list[dict[str, any]]):
        texts = []
        images = []
        for example in examples:
            images.append([example["image"].convert("RGB")])
            texts.append(
                processor.apply_chat_template(
                    example["messages"], add_generation_prompt=False, tokenize=False
                ).strip()
            )

        # Tokenize the texts and process the images
        batch = processor(text=texts, images=images, return_tensors="pt", padding=True)

        # The labels are the input_ids, with the padding and image tokens masked in
        # the loss computation
        labels = batch["input_ids"].clone()

        # Mask image tokens
        image_token_id = [
            processor.tokenizer.convert_tokens_to_ids(
                processor.tokenizer.special_tokens_map["boi_token"]
            )
        ]
        # Mask tokens that are not used in the loss computation
        labels[labels == processor.tokenizer.pad_token_id] = -100
        labels[labels == image_token_id] = -100
        labels[labels == 262144] = -100

        batch["labels"] = labels
        return batch

    num_train_epochs = 200  # @param {type: "number"}
    learning_rate = 2e-4  # @param {type: "number"}

    args = SFTConfig(
        output_dir="medgemma-4b-it-sft-brain-regions",            # Directory and Hub repository id to save the model to
        num_train_epochs=num_train_epochs,                       # Number of training epochs
        per_device_train_batch_size=4,                           # Batch size per device during training
        per_device_eval_batch_size=8,                            # Batch size per device during evaluation
        gradient_accumulation_steps=4,                           # Number of steps before performing a backward/update pass
        gradient_checkpointing=True,                             # Enable gradient checkpointing to reduce memory usage
        optim="adamw_torch_fused",                               # Use fused AdamW optimizer for better performance
        logging_steps=50,                                        # Number of steps between logs
        save_strategy="epoch", 
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,            # Save checkpoint every epoch
        eval_strategy="epoch",                                   # Evaluate every `eval_steps`
        eval_steps=3,                                           # Number of steps between evaluations
        learning_rate=learning_rate,                             # Learning rate based on QLoRA paper
        bf16=True,                                               # Use bfloat16 precision
        max_grad_norm=0.3,                                       # Max gradient norm based on QLoRA paper
        warmup_ratio=0.03,                                       # Warmup ratio based on QLoRA paper
        lr_scheduler_type="linear",                              # Use linear learning rate scheduler
        push_to_hub=True,                                        # Push model to Hub
        report_to="tensorboard",                                 # Report metrics to tensorboard
        gradient_checkpointing_kwargs={"use_reentrant": False},  # Set gradient checkpointing to non-reentrant to avoid issues
        dataset_kwargs={"skip_prepare_dataset": True},           # Skip default dataset preparation to preprocess manually
        remove_unused_columns = False,                           # Columns are unused for training but needed for data collator
        label_names=["labels"],                                  # Input keys that correspond to the labels
        save_safetensors=False,                                  # Disable safetensors to avoid shared memory issues with tied weights
    )

    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=formatted_data["train"],
        eval_dataset=formatted_data["validation"],  # Use subset of validation set for faster run
        #peft_config=peft_config,
        processing_class=processor,
        data_collator=collate_fn,
    )
    trainer.train()
