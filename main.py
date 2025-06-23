from fastapi import FastAPI, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
from datetime import datetime
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pyaarkepatr.com",
        "https://www.pyaarkepatr.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT"],
    allow_headers=["*"],
)

conn = sqlite3.connect("subscribers.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name VARCHAR(255) NULL,
    timestamp DATETIME NOT NULL
)
''')
conn.commit()

class EmailData(BaseModel):
    email: str
    name: Optional[str] = None


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

@app.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(data: EmailData):
    try:
        timestamp = datetime.now()
        cursor.execute(
            "INSERT INTO subscribers (email, name, timestamp) VALUES (?, ?, ?)",
            (data.email, data.name, timestamp)
        )
        conn.commit()
        logging.info(f"[+] New subscriber: {data.email}")
        return {"message": "Thanks for subscribing!"}
    except Exception as e:
        logging.error(f"[-] Error subscribing: {str(e)}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal Server Error"})


@app.get("/subscribers", status_code=status.HTTP_200_OK)
async def get_subscribers(x_api_key: str = Header(...)):
    expected_key = os.environ.get("X_API_KEY")
    if x_api_key != expected_key:
        logging.warning("Unauthorized access attempt to /subscribers")
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Unauthorized"})

    try:
        cursor.execute("SELECT id, email, name, timestamp FROM subscribers")
        rows = cursor.fetchall()
        subscribers = [
            {
                "id": row[0],
                "email": row[1],
                "name": row[2],
                "timestamp": row[3],
            }
            for row in rows
        ]
        return {"subscribers": subscribers}
    except Exception as e:
        logging.error(f"[-] Error fetching subscribers: {str(e)}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Internal Server Error"})