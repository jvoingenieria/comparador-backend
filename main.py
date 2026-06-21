from fastapi import FastAPI
import httpx
import asyncio
from typing import List, Optional
import json

app = FastAPI(title="Comparador de Supermercados España")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

async def fetch_price(client, url, headers=None):
    try:
        resp = await client.get(url, headers=headers or HEADERS, timeout=8.0)
        if resp.status_code == 200:
            return resp.json()
    except:
        return None

# --- SCRAPERS ESPECÍFICOS ---

async def get_mercadona(ean: str, client: httpx.AsyncClient):
    # Mercadona requiere a veces un código postal en las cookies para dar precios exactos
    url = f"https://tienda.mercadona.es/api/search/?query={ean}"
    data = await fetch_price(client, url)
    if data and data.get("results"):
        prod = data["results"][0]
        price = prod.get("price_instructions", {}).get("unit_price")
        if price:
            return {"supermarket": "Mercadona", "price": float(price), "name": prod.get("display_name")}
    return None

async def get_carrefour(ean: str, client: httpx.AsyncClient):
    # Carrefour tiene una API interna que responde bien al EAN
    url = f"https://www.carrefour.es/cloud-api/proxy/v1/search/search?query={ean}"
    data = await fetch_price(client, url)
    if data and data.get("content") and data["content"].get("docs"):
        prod = data["content"]["docs"][0]
        price = prod.get("active_price")
        if price:
            return {"supermarket": "Carrefour", "price": float(price), "name": prod.get("display_name")}
    return None

async def get_dia(ean: str, client: httpx.AsyncClient):
    url = f"https://www.dia.es/api/v1/search-back/search/products?q={ean}"
    data = await fetch_price(client, url)
    if data and data.get("search_items"):
        prod = data["search_items"][0].get("product", {})
        price = prod.get("price_per_unit", {}).get("amount")
        if price:
            return {"supermarket": "DIA", "price": float(price), "name": prod.get("name")}
    return None

async def get_consum(ean: str, client: httpx.AsyncClient):
    # Consum requiere una API específica de búsqueda
    url = f"https://tienda.consum.es/api/rest/V1.0/catalog/product/search?q={ean}"
    data = await fetch_price(client, url)
    if data and data.get("products"):
        prod = data["products"][0]
        price = prod.get("priceData", {}).get("prices", [{}])[0].get("amount")
        if price:
            return {"supermarket": "Consum", "price": float(price), "name": prod.get("productData", {}).get("name")}
    return None

async def get_alcampo(ean: str, client: httpx.AsyncClient):
    # Alcampo usa una API basada en el buscador de su web
    url = f"https://www.alcampo.es/compra-online/api/v3/search?term={ean}"
    data = await fetch_price(client, url)
    if data and data.get("entities") and data["entities"].get("product"):
        # Alcampo devuelve un mapa de IDs, cogemos el primero
        prod_id = list(data["entities"]["product"].keys())[0]
        prod = data["entities"]["product"][prod_id]
        price = prod.get("price", {}).get("current", {}).get("amount")
        if price:
            return {"supermarket": "Alcampo", "price": float(price), "name": prod.get("name")}
    return None

async def get_lidl(ean: str, client: httpx.AsyncClient):
    # Lidl es más restrictivo, usamos su API de búsqueda de productos
    url = f"https://www.lidl.es/es/search/api/v1/products?q={ean}"
    data = await fetch_price(client, url)
    if data and data.get("products"):
        prod = data["products"][0]
        price = prod.get("price", {}).get("value")
        if price:
            return {"supermarket": "Lidl", "price": float(price), "name": prod.get("fullTitle")}
    return None

# --- ENDPOINT PRINCIPAL ---

@app.get("/search/{ean}")
async def search_product(ean: str):
    async with httpx.AsyncClient() as client:
        # Lanzamos todas las peticiones en paralelo
        tasks = [
            get_mercadona(ean, client),
            get_carrefour(ean, client),
            get_dia(ean, client),
            get_consum(ean, client),
            get_alcampo(ean, client),
            get_lidl(ean, client)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Filtramos resultados encontrados
        final_results = [r for r in responses if r is not None]
        
        return {
            "ean": ean,
            "results": final_results
        }
