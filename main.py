from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import rdflib

app = FastAPI()

g = rdflib.Graph()
g.parse("static/steam.ttl")


@app.get("/api")
async def root():
    return {"message": "Hello World"}


@app.get("/api/{app_id}")
async def read_app(app_id: str):
    query = f"""
        SELECT ?app ?app_name
        WHERE {{
            ?app <http://127.0.0.1:8000/appid> "{app_id}" .
            ?app rdfs:label ?app_name .
        }}
    """

    res = g.query(query)

    for row in res:
        print(row)
    return res
