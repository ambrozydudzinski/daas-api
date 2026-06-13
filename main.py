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
    
    # Budujemy czysty, zakodowany adres URL pod publiczny strumień danych OLX
    encoded_item = httpx.utils.quote(item)
    url = f"https://www.olx.pl/motoryzacja/czesci-samochodowe/q-{encoded_item}/?search%5Bfilter_float_price%3Ato%5D={max_price}&search%5Border%5D=created_at%3Adesc"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=15.0)
            
            if response.status_code != 200:
                return {"status": "error", "message": f"OLX zwrocil status: {response.status_code}"}
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Szukamy kontenerów z ogłoszeniami (wykorzystujemy selektor kart ogłoszeń na OLX)
            offers = soup.find_all("div", {"data-cy": "l-card"})
            
            if not offers:
                return {"status": "success", "message": f"Brak nowych ogłoszeń dla '{item}' poniżej {max_price} PLN w tej sekundzie."}
            
            # Pobieramy najnowsze ogłoszenie z góry listy
            latest_offer = offers[0]
            
            # Wyciągamy tytuł, cenę i link
            title_elem = latest_offer.find("h6")
            price_elem = latest_offer.find("p", {"data-xy": "price-text"}) or latest_offer.find("p")
            link_elem = latest_offer.find("a")
            
            title = title_elem.text.strip() if title_elem else "Specjalistyczna część motoryzacyjna"
            price = price_elem.text.strip() if price_elem else "Do negocjacji"
            
            raw_link = link_elem["href"] if link_elem else ""
            full_link = f"https://www.olx.pl{raw_link}" if raw_link.startswith("/") else raw_link
            
            # Budowanie przejrzystego raportu biznesowego dla klienta B2B
            msg_text = (
                f"🎯 *NOWA OFERTA W MONITOROWANEJ NISZY*\n"
                f"───────────────────\n"
                f"📦 *Część:* {title}\n"
                f"💰 *Cena w ogłoszeniu:* {price}\n"
                f"🔍 *Słowo kluczowe:* {item}\n"
                f"───────────────────\n"
                f"🔗 [OTWÓRZ OGŁOSZENIE NA OLX]({full_link})\n"
                f"⏱ _System przetworzył dane natychmiast po publikacji._"
            )
            
            # Wymuszamy poprawne kodowanie znaków do formatu UTF-8, aby uniknąć błędów
            url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": msg_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            telegram_res = await client.post(url_send, json=payload)
            
            return {
                "status": "scan_completed",
                "item_scanned": item,
                "found_title": title,
                "found_price": price,
                "telegram_response": telegram_res.json()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
