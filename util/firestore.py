import json
import os
from base64 import b64decode

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


def get_firestore_db():
    if not firebase_admin._apps:
        firebase_config = os.getenv("FIREBASE")
        firebase_dict = json.loads(b64decode(firebase_config))

        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)

    return firestore.client()
