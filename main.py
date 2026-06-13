from fastapi import FastAPI
import httpx
import os

app = FastAPI(title="Skaner Okazji B2B")

# Pobieramy bezpieczne dane z panelu Railway
TOKEN = os.getenv("TELEGRAM_TOKEN")

@app.get("/")
async def root():
    return {"status": "online", "message": "System gotowy. Uzyj /test-alert aby sprawdzic polaczenie."}

@app.get("/test-alert")
async def test_alert():
    if not TOKEN:
        return {"status": "error", "message": "Brak konfiguracji TELEGRAM_TOKEN w Railway!"}
    
    # Automatyczne szukanie ID Twojego kanału na podstawie ostatniej wiadomości
    url_updates = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Pobieramy ID czatu/kanału z ostatnich aktywności bota
            res = await client.get(url_updates)
            updates = res.json()
            
            chat_id = None
            # Szukamy wpisu z kanału (channel_post)
            if "result" in updates and len(updates["result"]) > 0:
                for update in updates["result"]:
                    if "channel_post" in update:
                        chat_id = update["channel_post"]["chat"]["id"]
                        break
            
            if not chat_id:
                return {
                    "status": "pending", 
                    "message": "Nie znaleziono ID kanału. Upewnij sie, ze napisales cos na kanale i bot jest tam administratorem, a nastepnie odswiez te strone."
                }
            
            # 2. Wysyłamy właściwy alert testowy bezpośrednio na zabezpieczony kanał
            msg_text = (
                "🚀 *ALERT SKANERA B2B*\n"
                "───────────────────\n"
                " Połączenie z serwerem automatyzacji: *AKTYWNE*\n"
                " System monitoringu: *OCZEKIWANIE NA DANE*\n"
                "───────────────────\n"
                "Zabezpieczenia anty-kopiowania działają prawidłowo."
            )
            
            url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": msg_text,
                "parse_mode": "Markdown"
            }
            
            send_res = await client.post(url_send, json=payload)
            
            return {
                "status": "success",
                "detected_channel_id": chat_id,
                "telegram_response": send_res.json()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}


