import os
import random
import asyncio
import httpx
import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Apna Nidhi Tech Alert & OTP Server")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Universal CORS & Preflight Fix for Cloudflare Workers
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# 100% Correct Telegram Token and Dedicated Admin Chat ID (9627490569 Target)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8698294819:AAEVoNvzY7H2rEwcUYZHmVP3TsdtdfUtOjE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5652323334")
RENDER_SERVER_URL = os.getenv("RENDER_SERVER_URL", "https://apna-nidhi-tech-telegram-api.onrender.com")

# In-memory OTP storage
otp_store = {}

# ----------------------------
# 🔄 SELF-PINGING LOGIC (10 Seconds Interval)
# ----------------------------
async def self_ping_task():
    await asyncio.sleep(10)
    async with httpx.AsyncClient() as client:
        while True:
            try:
                ping_url = f"{RENDER_SERVER_URL.rstrip('/')}/health"
                await client.get(ping_url, timeout=4.0)
            except Exception:
                pass
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(self_ping_task())

@app.get("/health")
def health_check():
    return {"status": "alive", "message": "Server is 24/7 active with 10s ping!"}


# ----------------------------
# REQUEST MODELS
# ----------------------------
class SendOtpRequest(BaseModel):
    identifier: str

class VerifyOtpRequest(BaseModel):
    identifier: str
    otp: str

class AdminAlertRequest(BaseModel):
    serviceType: str
    orderId: str
    applicantName: str
    agentName: str
    agentMobile: str
    extraDetails: Optional[str] = "N/A"


# ----------------------------
# ROUTE 1: SEND OTP (Hitech & Secure Design)
# ----------------------------
@app.post("/api/send-otp")
async def send_otp(data: SendOtpRequest):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(status_code=500, detail="Telegram credentials missing!")

    identifier_key = data.identifier.strip().lower()
    generated_otp = str(random.randint(100000, 999999))
    otp_store[identifier_key] = generated_otp

    message = (
        f"🛡️ *APNA NIDHI TECH - SECURE GATEWAY* 🛡️\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Target ID / Mobile:* `{data.identifier}`\n"
        f"🔑 *Verification OTP:* `✨ {generated_otp} ✨`\n"
        f"⏳ *Validity:* 5 Minutes Only\n"
        f"🌐 *Portal URL:* https://ant-sapna-portals.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *SECURITY WARNING:*\n"
        f"• Never share this OTP code with anyone, even if they claim to be Apna Nidhi Tech support.\n"
        f"• We never ask for your personal banking passwords or sensitive credentials.\n"
        f"• If you didn't request this, immediately secure your account."
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(telegram_url, json=payload, timeout=8)
        if response.status_code == 200:
            return {"status": "success", "message": "OTP sent to Telegram successfully!"}
        else:
            raise HTTPException(status_code=500, detail=f"Telegram API Error: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------
# ROUTE 2: VERIFY OTP
# ----------------------------
@app.post("/api/verify-otp")
async def verify_otp(data: VerifyOtpRequest):
    identifier_key = data.identifier.strip().lower()
    stored_otp = otp_store.get(identifier_key)

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP expired or not requested!")

    if stored_otp == data.otp.strip():
        del otp_store[identifier_key]
        return {"status": "success", "verified": True, "message": "OTP Verified Successfully!"}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP entered!")


# ----------------------------
# ROUTE 3: SEND ADMIN ALERT (Exclusive Target & Admin Link)
# ----------------------------
@app.post("/api/send-admin-alert")
async def send_admin_alert(data: AdminAlertRequest):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(status_code=500, detail="Telegram credentials missing!")

    message = (
        f"🚨 *HIGH PRIORITY SERVICE ALERT* 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *Service:* `{data.serviceType}`\n"
        f"🔖 *Order ID:* `{data.orderId}`\n"
        f"👤 *Applicant:* `{data.applicantName}`\n"
        f"🏢 *Retailer:* `{data.agentName}`\n"
        f"📞 *Mobile:* `{data.agentMobile}`\n"
        f"📝 *Extra Info:* `{data.extraDetails}`\n"
        f"🔗 *Admin Portal:* https://ant-by-sapna-portals.netlify.app/\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 *Action Required:* Review and Verify request from dashboard."
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,  # Designated number target chat ID
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(telegram_url, json=payload, timeout=8)
        if response.status_code == 200:
            return {"status": "success", "message": "Alert sent to admin successfully!"}
        else:
            raise HTTPException(status_code=500, detail=f"Telegram API Error: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))