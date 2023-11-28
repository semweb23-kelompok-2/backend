from .utils import *
from fastapi import APIRouter

import rdflib

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")


@router.get("/games")
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
