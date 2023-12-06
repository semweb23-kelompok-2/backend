from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import games, games_search, game_detail

import rdflib

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

g = rdflib.Graph()
g.parse("static/steam.ttl")


@app.get("/api")
async def root():
    return {"message": "Hello World"}


app.include_router(games.router, prefix="/api")
app.include_router(games_search.router, prefix="/api")
app.include_router(game_detail.router, prefix="/api")
