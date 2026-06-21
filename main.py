from fastapi import FastAPI
import httpx
import asyncio
from typing import List, Optional

app = FastAPI(title="Comparador de Supermercados España")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

async def fetch_price(client, url, supermarket_name, headers=None):
    try:
        resp = await client.get(url, headers=headers or HEADERS, timeout=10.0)
        print(f"[{supermarket_name}] Status: {resp.status_code}") # Log para Render
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"[{supermarket_name}] Error Body: {resp.text[:100]}") # Ver si hay mensaje de bloqueo
            return None
    except Exception as e:
        print(f"[{supermarket_name}] Excepción: {e}")
        return None

# --- Los scrapers se mantienen igual, pero pasando el nombre al fetch_price ---
# Ejemplo de cómo actualizar uno:
async def get_mercadona(ean: str, client: httpx.AsyncClient):
    url = f"https://tienda.mercadona.es/api/search/?query={ean}"
    data = await fetch_price(client, url, "Mercadona")
    if data and data.get("results"):
        prod = data["results"][0]
        price = prod.get("price_instructions", {}).get("unit_price")
        if price:
            return {"supermarket": "Mercadona", "price": float(price), "name": prod.get("display_name")}
    return None

# ... (Repite la estructura de pasar el nombre del súper a fetch_price para los demás) ...
