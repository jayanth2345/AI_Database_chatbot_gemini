from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import os

# ====== CONFIG ======
model_id = "meta-llama/Llama-3.2-1B-Instruct"
base_save_dir = "./models"
fp16_dir = os.path.join(base_save_dir, "llama-3.2-3b-instruct-fp16")
quant_dir = os.path.join(base_save_dir, "llama-3.2-3b-instruct-4bit")
os.makedirs(base_save_dir, exist_ok=True)

# ====== STEP 1: LOAD TOKENIZER ======
print("🔹 Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)

# ====== STEP 2: LOAD FP16 MODEL AND SAVE SNAPSHOT ======
print("🔹 Loading FP16 model...")
model_fp16 = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)

print(f"💾 Saving FP16 snapshot to {fp16_dir}")
model_fp16.save_pretrained(fp16_dir)
tokenizer.save_pretrained(fp16_dir)

# ====== STEP 3: CONFIGURE 4-BIT QUANTIZATION ======
print("🔹 Setting up 4-bit quantization config...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",         # Normalized float4
    bnb_4bit_use_double_quant=True,    # Improves accuracy
    bnb_4bit_compute_dtype=torch.bfloat16
)

# ====== STEP 4: LOAD QUANTIZED MODEL ======
print("🔹 Loading quantized model...")
model_4bit = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto"
)

# ====== STEP 5: SAVE QUANTIZED SNAPSHOT ======
print(f"💾 Saving quantized 4-bit snapshot to {quant_dir}")
model_4bit.save_pretrained(quant_dir)
tokenizer.save_pretrained(quant_dir)

print("\n✅ Done! Two versions are now saved locally:")
print(f" - FP16 model: {fp16_dir}")
print(f" - 4-bit quantized model: {quant_dir}")
