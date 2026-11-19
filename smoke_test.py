import time, torch
from transformers import AutoTokenizer
from capability_check import MODEL, DEVICE, load_model, mem_gb

tok = AutoTokenizer.from_pretrained(MODEL)
t0 = time.time()
model = load_model()
print(f"{type(model).__name__} on {DEVICE}, dtype {model.dtype}, load {time.time() - t0:.1f}s, mem {mem_gb():.2f} GB")

msgs = [{"role": "user", "content": "What is 12 times 8?"}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False,
                              return_tensors="pt", return_dict=True)["input_ids"].to(DEVICE)
t0 = time.time()
with torch.no_grad():
    out = model.generate(input_ids=ids, max_new_tokens=40, do_sample=False)
n = out.shape[1] - ids.shape[1]
print(f"answer: {tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)!r}")
print(f"{n} tokens in {time.time() - t0:.1f}s")
