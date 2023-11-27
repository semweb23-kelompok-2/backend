from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import json
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
    return load_result_into_json(res)


@app.get("/api/games/search")
async def search_games(name: str, skip: int = 0, limit: int = 50):
    query = f"""
        prefix : <http://127.0.0.1:8000/>

            SELECT ?app_id ?app_name ?header_image ?background ?positive_ratings ?negative_ratings (GROUP_CONCAT(distinct(?genre); SEPARATOR=", ") as ?genres)
            WHERE {{
                ?app a :Game ;
                    rdfs:label ?app_name ;
                    :appid ?app_id ;
                    :header_image ?header_image ;
                    :background ?background ;
                    :positive_ratings ?positive_ratings ;
                    :negative_ratings ?negative_ratings ;
                    :genre ?genre .

                FILTER (regex(?app_name, "{name}", "i"))
        }}
        GROUP BY ?app_id ?app_name ?header_image ?background ?positive_ratings ?negative_ratings
        ORDER BY ?app_name 
        LIMIT {limit}
        OFFSET {skip}
    """

    res = g.query(query)
    # return the result in json format without using process_result
    return json.loads(res.serialize(format="json"))


@app.get("/api/games/{app_id}")
async def read_game(app_id: str):
    query = f"""
        SELECT ?app ?app_name
        WHERE {{
            ?app <http://127.0.0.1:8000/appid> "{app_id}" .
            ?app rdfs:label ?app_name .
        }}
    """

    res = g.query(query)
    return load_result_into_json(res)


def load_result_into_json(query_result):
    return json.loads(query_result.serialize(format="json"))
