from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- CONFIGURAÇÃO DO FIREBASE ---
# (Só faça isso se ainda não tiver configurado no seu código)
if not firebase_admin._apps:
    # Atenção: No Render, você geralmente usa variáveis de ambiente para a chave
    cred = credentials.Certificate("caminho/para/sua/chave-firebase.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = FastAPI()

# --- MODELO DE DADOS ---
class VagaExcel(BaseModel):
    vaga: str
    setor: str
    responsavel: str
    data_abertura: str 

# --- A ROTA QUE O EXCEL ESTÁ PROCURANDO ---
@app.post("/api/vagas")
async def receber_vagas(vagas: List[VagaExcel]):
    print(f"📥 Recebendo {len(vagas)} vagas...")

    try:
        # Opcional: Limpar coleção antiga para não duplicar (snapshot)
        # Se quiser manter histórico, pode pular essa parte
        docs = db.collection("vagas_kpi").stream()
        for doc in docs:
            doc.reference.delete()
        
        # Salvar as novas vagas
        batch = db.batch()
        for item in vagas:
            # Cria um ID único ou usa automático
            doc_ref = db.collection("vagas_kpi").document()
            
            # Prepara os dados
            dados_salvar = {
                "titulo": item.vaga,
                "setor": item.setor,
                "recrutador": item.responsavel,
                "data_abertura": item.data_abertura,
                "sincronizado_em": datetime.now() # Bom para saber quando atualizou
            }
            batch.set(doc_ref, dados_salvar)
            
        # Executa a gravação em lote (muito mais rápido)
        batch.commit()
        
        return {"status": "sucesso", "msg": f"{len(vagas)} vagas sincronizadas!"}

    except Exception as e:
        print(f"Erro no Firebase: {e}")
        raise HTTPException(status_code=500, detail=str(e))
