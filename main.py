from fastapi import FastAPI
from typing import List

app = FastAPI(title="Comparador de Precios API")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API de Comparación de Supermercados funcionando"}

@app.get("/search/{ean}")
async def search_product(ean: str):
    # Por ahora devolvemos datos de prueba. 
    # Aquí es donde más adelante añadiremos el scraping real.
    return {
        "ean": ean,
        "results": [
            {
                "supermarket": "Mercadona",
                "price": 1.25,
                "name": "Producto Ejemplo",
            },
            {
                "supermarket": "Carrefour",
                "price": 1.18,
                "name": "Producto Ejemplo",
            }
        ]
    }
