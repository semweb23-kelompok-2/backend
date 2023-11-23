from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import rdflib

app = FastAPI()

g = rdflib.Graph()
g.parse("static/steam.ttl")


@app.get("/api")
async def root():
    return {"message": "Hello World"}


@app.get("/api/games")
async def get_all_games(skip: int = 0, limit: int = 50):
    query = f"""
        prefix : <http://127.0.0.1:8000/>

        SELECT ?app_id ?app_name
        WHERE {{
            ?app a :Game .
            ?app rdfs:label ?app_name .
            ?app :appid ?app_id .
        }}
        ORDER BY ?app_name
        LIMIT {limit}
        OFFSET {skip}
    """

    res = g.query(query)
    return process_result(res)


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


def process_result(query_result):
    res = []
    print(len(query_result))
    for row in query_result:
        res.append(row)

    return res
