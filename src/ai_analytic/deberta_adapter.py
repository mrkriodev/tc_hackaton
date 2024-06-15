from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import torch
import pickle
import numpy as np
import os

if os.path.exists(os.path.join(os.getcwd(), "./src/ai_analytic/LGBMClassifier.pkl")):
    boosting = pickle.load(open(os.path.join(os.getcwd(), "./src/ai_analytic/LGBMClassifier.pkl"), 'rb'))
else:
    boosting = pickle.load(open(os.path.join(os.getcwd(), "./ai_analytic/LGBMClassifier.pkl"), 'rb'))
    
if os.path.exists(os.path.join(os.getcwd(), "./src/ai_analytic/best-src-pt-checkpoint")):
    model = AutoModelForSequenceClassification.from_pretrained("./src/ai_analytic/best-src-pt-checkpoint")
    model_src_emb = AutoModelForSequenceClassification.from_pretrained("./src/ai_analytic/best-src-pt-checkpoint")
    model_opt_emb = AutoModelForSequenceClassification.from_pretrained("./src/ai_analytic/best-opt-pt-checkpoint")
    tokenizer = AutoTokenizer.from_pretrained("./src/ai_analytic/tokenizer")
else:
    model = AutoModelForSequenceClassification.from_pretrained("./ai_analytic/best-src-pt-checkpoint")
    model_src_emb = AutoModelForSequenceClassification.from_pretrained("./ai_analytic/best-src-pt-checkpoint")
    tokenizer = AutoTokenizer.from_pretrained("./ai_analytic/tokenizer")

model_src_emb.classifier = torch.nn.Identity()
model_opt_emb.classifier = torch.nn.Identity()

test_str = "function transferFrom(address from, address to, uint tokens) public returns (bool success) { balances[from] = safeSub(balances[from], tokens); allowed[from][msg.sender] = safeSub(allowed[from][msg.sender], tokens); balances[to] = safeAdd(balances[to], tokens); Transfer(from, to, tokens); return true; }function transfer(address to, uint tokens) public returns (bool success) { balances[msg.sender] = safeSub(balances[msg.sender], tokens); balances[to] = safeAdd(balances[to], tokens); Transfer(msg.sender, to, tokens); return true; } "


def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))


async def source_code_deberta_analyze(src_code_in: str):
    print(f"src_code_in = {src_code_in}")
    result = None
    
    with torch.no_grad():
        in_str = tokenizer(test_str, truncation=True, padding=True, max_length=512, return_tensors="pt")
        emb = model_src_emb(**in_str).logits[0].numpy()
        ans = emb
        
        result = boosting.predict_proba(ans.reshape(1,-1))[:,1]
    
    print(result)
    return result


async def opcodes_deberta_analyze_one(opcodes_in: str):
    print(f"opcodes_in = {opcodes_in}")
    result = None
        
    with torch.no_grad():
        in_str = tokenizer(opcodes_in[:512], truncation=True, padding=True, max_length=512, return_tensors="pt")
        emb = model_opt_emb(**in_str).logits[0].numpy()
        ans = emb
    
    result = boosting.predict_proba(ans.reshape(1,-1))[:,1]
    print(result)
    return result


async def opcodes_deberta_analyze(opcodes_in: str):
    print(f"opcodes_in = {opcodes_in}")
    result = None
    
    chunks = list(chunkstring(opcodes_in, 512))
    ans = []
        
    with torch.no_grad():    
        for chunk in chunks:
            in_str = tokenizer(chunk, truncation=True, padding=True, max_length=512, return_tensors="pt")
            res = model_opt_emb(**in_str)
            probs = torch.sigmoid(res.logits[0])
            pos = torch.argmax(probs)
            ans.append(probs[pos].item())
    
    result = np.sum(ans)/len(ans)
    print(result)
    return result