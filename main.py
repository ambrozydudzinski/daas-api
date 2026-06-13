from fastapi import FastAPI
import asyncio

app = FastAPI(title="Agregator Danych API")

@app.get("/")
async def root():
    return {"status": "online", "message": "API dziala w chmurze. Gotowe do przyjmowania polecen."}

@app.get("/scan")
async def run_scanner():
    # Tutaj wdrożymy asynchroniczny skrypt skanujący rynek (np. w poszukiwaniu ofert)
    await asyncio.sleep(0.5) 
    return {"status": "success", "data": "Brak nowych, zyskownych ofert w tej sekundzie."}
