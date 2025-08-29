from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import List
import random

app = FastAPI(title="Domino Test API", version="1.0.0")

# Configure CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Item(BaseModel):
    name: str
    price: float

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float

# In-memory storage (for demo purposes)
items_db = []
item_counter = 1

@app.get("/")
async def root():
    return {"message": "FastAPI backend is running on Domino!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fastapi-backend"}

@app.get("/api/items", response_model=List[ItemResponse])
async def get_items():
    return items_db

@app.post("/api/items", response_model=ItemResponse)
async def create_item(item: Item):
    global item_counter
    new_item = ItemResponse(id=item_counter, name=item.name, price=item.price)
    items_db.append(new_item)
    item_counter += 1
    return new_item

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: int):
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": f"Item {item_id} deleted"}

@app.get("/api/random-quote")
async def get_random_quote():
    quotes = [
        "The best way to predict the future is to invent it.",
        "Life is what happens when you're busy making other plans.",
        "The future belongs to those who believe in the beauty of their dreams.",
        "It is during our darkest moments that we must focus to see the light.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts."
    ]
    return {"quote": random.choice(quotes), "author": "Various"}

if __name__ == "__main__":
    # Run on port 8000 for the backend
    uvicorn.run(app, host="0.0.0.0", port=8000)