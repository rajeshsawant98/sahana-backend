"""
Dump all Firestore collections to JSON for schema inspection.
Run from project root: python scripts/dump_firestore.py
"""
import json
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('firebase_cred.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


def serialize(obj):
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


def dump_collection(name, limit=3):
    docs = list(db.collection(name).limit(limit).stream())
    all_docs = [{"_id": d.id, **serialize(d.to_dict())} for d in docs]
    total = db.collection(name).count().get()[0][0].value
    return total, all_docs


for col in ["users", "events", "friend_requests"]:
    total, samples = dump_collection(col, limit=3)
    print(f"\n{'='*60}")
    print(f"COLLECTION: {col}  (total docs: {total})")
    print('='*60)
    for doc in samples:
        print(json.dumps(doc, indent=2, default=str))
        print("-" * 40)
