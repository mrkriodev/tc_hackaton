from langchain_community.embeddings.gigachat import GigaChatEmbeddings
import numpy as np

import os
import pickle

from typing import List

if os.path.exists(os.path.join(os.getcwd(), "./src/ai_analytic/LGBMClassifier.pkl")):
    boosting = pickle.load(open(os.path.join(os.getcwd(), "./src/ai_analytic/LGBMClassifier.pkl"), 'rb'))
else:
    boosting = pickle.load(open(os.path.join(os.getcwd(), "./ai_analytic/LGBMClassifier.pkl"), 'rb'))

embeddings = GigaChatEmbeddings(credentials="ZDRmM2MzOGUtMDBkOS00YzIzLTliOTEtZTQ1MmJlYmY3MjI2OjI4MDM5Mjg3LTJjOWUtNGQ0MC05OTcxLTYzMmI3NDQwOTNiOA==", verify_ssl_certs=False)

def l2_norm(x : np.ndarray) -> float:
   return np.sqrt(np.sum(x**2))

def div_norm(x: np.ndarray) -> np.ndarray:
   norm_value = l2_norm(x)
   if norm_value > 0:
       return x * ( 1.0 / norm_value)
   else:
       return x

def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

def get_giga_emb(text_array_in):
    return np.array(embeddings.embed_documents(texts=text_array_in)[0])

async def ya_source_code_gigachain_analyze(src_code_in: str):
    print(f"src_code_in = {src_code_in}")
    src_code_splitted_text_array = list(chunkstring(src_code_in, 512))
    sent_vec = np.zeros(1024)  # sentence vector
    
    for chunk in src_code_splitted_text_array:  # already 512 symbols spliited every chunk
        vec = np.array(embeddings.embed_documents(texts=[chunk])[0])
        sent_vec += div_norm(vec)
    
    sent_vec = sent_vec / len(src_code_splitted_text_array)
    emb = np.array(sent_vec)  # embedding sentense
    
    result = boosting.predict_proba(emb.reshape(1,-1))[:,1]
    
    print(result)
    return result
    

async def source_code_gigachain_analyze_by_funcs(funcs_array_in: List):
    print(f"funcs_array_in = {funcs_array_in}")
    probs = []
    for chunk in funcs_array_in:
        if len(chunk) < 1:
            continue
        #print(chunk[:512])
        if len(chunk[:512]) > 512:
            emb = get_giga_emb(chunk[:512])
        else:
            emb = get_giga_emb(chunk)
        result = boosting.predict_proba(emb.reshape(1,-1))[:,1]
        probs.append(result[0])
    result = np.sum(probs)/len(probs)
    print(result)
    return result


async def source_code_gigachain_analyze(src_code_in: str):
    print(f"src_code_in = {src_code_in}")
    probs = []
    src_code_splitted_text_array = list(chunkstring(src_code_in, 512))
    for chunk in src_code_splitted_text_array:
        print(chunk)
        emb = get_giga_emb(chunk)
        result = boosting.predict_proba(emb.reshape(1,-1))[:,1]
        probs.append(result[0])
    result = np.sum(probs)/len(probs)
    print(result)
    return result