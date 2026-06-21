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
        if resp.status_code == 200:
            return resp.json()
        print(f"[{supermarket_name}] Status: {resp.status_code}")
    except Exception as e:
        print(f"[{supermarket_name}] Error: {e}")
    return None

async def get_mercadona(ean: str, client: httpx.AsyncClient):
    url = f"https://tienda.mercadona.es/api/search/?query={ean}"
    data = await fetch_price(client, url, "Mercadona")
    if data and data.get("results"):
        prod = data["results"][0]
        price = prod.get("price_instructions", {}).get("unit_price")
        if price:
            return {"supermarket": "Mercadona", "price": float(price), "name": prod.get("display_name")}
    return None

async def get_dia(ean: str, client: httpx.AsyncClient):
    url = f"https://www.dia.es/api/v1/search-back/search/products?q={ean}"
    data = await fetch_price(client, url, "DIA")
    if data and data.get("search_items"):
        prod = data["search_items"][0].get("product", {})
        price = prod.get("price_per_unit", {}).get("amount")
        if price:
            return {"supermarket": "DIA", "price": float(price), "name": prod.get("name")}
    return None

async def get_carrefour(ean: str, client: httpx.AsyncClient):
    url = f"https://www.carrefour.es/cloud-api/proxy/v1/search/search?query={ean}"
    data = await fetch_price(client, url, "Carrefour")
    if data and data.get("content") and data["content"].get("docs"):
        prod = data["content"]["docs"][0]
        price = prod.get("active_price")
        if price:
            return {"supermarket": "Carrefour", "price": float(price), "name": prod.get("display_name")}
    return None

@app.get("/")
def home():
    return {"status": "online", "message": "API de Comparación Arsys activa"}

@app.get("/search/{ean}")
async def search_product(ean: str):
    async with httpx.AsyncClient() as client:
        # Buscamos en los 3 principales para probar
        tasks = [
            get_mercadona(ean, client),
            get_dia(ean, client),
            get_carrefour(ean, client)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Filtramos los que no han devuelto nada
        final_results = [r for r in responses if r is not None]
        
        return {
            "ean": ean,
            "results": final_results
        }
