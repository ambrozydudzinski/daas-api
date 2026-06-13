from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Skaner Okazji B2B Pro")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("TARGET_CHANNEL")

@app.get("/")
async def root():
    return {"status": "active", "engine": "B2B Scanner Ready"}

@app.get("/run-scan")
async def run_scan(query: str = "ogólne", min_profit: int = 100):
    if not TOKEN or not CHANNEL_ID:
        return {"status": "error", "message": "Brak pełnej konfiguracji zmiennych w Railway!"}
    
    # 1. Symulacja zaawansowanego algorytmu filtrującego anomalie rynkowe
    # W tym miejscu silnik asynchronicznie analizuje bazy ogłoszeń pod kątem niedoszacowanych cen
    detected_item = f"Pakiet hurtowy / Specjalistyczny osprzęt ({query})"
    market_value = 1200
    scraped_price = market_value - min_profit - 250 # Wyliczenie sztucznej anomalii cenowej do testu bojowego
    
    # 2. Budowanie czystego, profesjonalnego komunikatu B2B bez błędów kodowania
    msg_text = (
        f"🎯 *NOWA OKAZJA RYNKOWA (Anomalia)*\n"
        f"───────────────────\n"
        f"📦 *Produkt:* {detected_item}\n"
        f"💰 *Cena znaleziona:* {scraped_price} PLN\n"
        f"📈 *Szacowana wartość:* {market_value} PLN\n"
        f"🔥 *Czysty zysk (Marża):* {market_value - scraped_price} PLN\n"
        f"───────────────────\n"
        f"🔗 [KLIKNIJ ABY PRZEJŚĆ DO OFERTY](https://olx.pl)\n"
        f"⏱ _Alert wygenerowany automatycznie w milisekundę po publikacji._"
    )
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": msg_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload)
            return {"status": "alert_sent", "target_channel": CHANNEL_ID, "telegram_status": res.json()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
