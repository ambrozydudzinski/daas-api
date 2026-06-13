from fastapi import FastAPI
import httpx
from bs4 import BeautifulSoup
import urllib.parse
import os

app = FastAPI(title="Skaner Motoryzacyjny B2B Pro")

@app.get("/")
async def root():
    return {"status": "active", "engine": "Automotive Scanner Live"}

@app.get("/run-scan")
async def run_scan(item: str = "wtryskiwacze", max_price: int = 600):
    token = os.getenv("TELEGRAM_TOKEN")
    channel_id = os.getenv("TARGET_CHANNEL")
    
    if not token or not channel_id:
        return {"status": "configuration_error", "message": "Sprawdź zmienne TELEGRAM_TOKEN i TARGET_CHANNEL w Railway!"}
    
    try:
        # Poprawne i bezpieczne kodowanie znaków dla polskich słów na OLX
        encoded_item = urllib.parse.quote(item)
        url = f"https://www.olx.pl/motoryzacja/q-{encoded_item}/?search%5Bfilter_float_price%3Ato%5D={max_price}&search%5Border%5D=created_at%3Adesc"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code != 200:
                return {"status": "site_blocked", "code": response.status_code}
                
            soup = BeautifulSoup(response.text, "html.parser")
            links = [a["href"] for a in soup.find_all("a", href=True) if "oferta" in a["href"]]
            
            if not links:
                return {"status": "no_links_found", "message": "Brak ofert spełniających kryteria na pierwszej stronie."}
                
            target_link = links[0]
            full_link = f"https://www.olx.pl{target_link}" if target_link.startswith("/") else target_link
            
            msg_text = (
                f"🎯 *NOWY WPIS W BAZIE DANYCH*\n"
                f"───────────────────\n"
                f"🔍 *Słowo:* {item}\n"
                f"💰 *Cena max:* {max_price} PLN\n"
                f"───────────────────\n"
                f"🔗 [KLIKNIJ ABY SPRAWDZIĆ OFERTĘ]({full_link})"
            )
            
            payload = {
                "chat_id": str(channel_id).strip(),
                "text": msg_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
            return {"status": "success", "link": full_link}
            
    except Exception as e:
        return {"status": "fatal_code_error", "error_details": str(e)}
