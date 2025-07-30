# firebase_reader.py
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

def init_firestore():
    # Firebase'i sadece bir kez başlat
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_lambda_f_data():
    db = init_firestore()
    docs = db.collection("lambdaF").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(30).stream()

    data = []
    for doc in docs:
        entry = doc.to_dict()
        entry["timestamp"] = entry["timestamp"].isoformat() if entry.get("timestamp") else None
        data.append(entry)

    return pd.DataFrame(data)