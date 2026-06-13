from fastapi import FastAPI
import httpx
from bs4 import BeautifulSoup
import os

app = FastAPI(title="Skaner Motoryzacyjny B2B Pro")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("TARGET_CHANNEL")

@app.get("/")
async def root():
    return {"status": "active", "engine": "Automotive Scanner Live"}

@app.get("/run-scan")
async def run_scan(item: str = "wtryskiwacze", max_price: int = 600):
    if not TOKEN or not CHANNEL_ID:
        return {"status": "error", "message": "Brak konfiguracji zmiennych w Railway!"}
    
    encoded_item = httpx.utils.quote(item)
    url = f"https://www.olx.pl/motoryzacja/q-{encoded_item}/?search%5Bfilter_float_price%3Ato%5D={max_price}&search%5Border%5D=created_at%3Adesc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                return {"status": "anti_bot_trigger", "message": f"Serwer zwrocil kod {response.status_code}. Portal wymaga uzycia proxy lub naglowkow sesyjnych."}
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Bezpieczne szukanie linków i tytułów – jeśli struktura się zmieniła, skrypt nie wywali błędu 500
            links = [a for a in soup.find_all("a", href=True) if "oferta" in a["href"]]
            
            if not links:
                return {"status": "structure_changed", "message": "Strona pobrana pomyślnie, ale format danych uległ zmianie. Przechodzę na tryb awaryjny."}
            
            # Pobieramy pierwszy napotkany link do oferty
            target_link = links[0]["href"]
            full_link = f"https://www.olx.pl{target_link}" if target_link.startswith("/") else target_link
            
            msg_text = (
                f"🎯 *NOWY WPIS W BAZIE DANYCH*\n"
                f"───────────────────\n"
                f"🔍 *Wykryto ruch dla słowa:* {item}\n"
                f"💰 *Próg maksymalny:* {max_price} PLN\n"
                f"───────────────────\n"
                f"🔗 [KLIKNIJ ABY SPRAWDZIĆ OFERTĘ]({full_link})\n"
                f"⏱ _Raport przesłany w trybie natychmiastowym._"
            )
            
            url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": msg_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            await client.post(url_send, json=payload)
            return {"status": "success", "extracted_link": full_link}
            
        except Exception as e:
            return {"status": "runtime_exception", "details": str(e)}
