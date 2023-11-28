from .utils import *
from fastapi import APIRouter

import rdflib

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")


@router.get("/games/{app_id}")
async def game_detail(app_id: str):
    query = f"""
        SELECT ?app ?app_name
        WHERE {{
            ?app <http://127.0.0.1:8000/appid> "{app_id}" .
            ?app rdfs:label ?app_name .
        }}
    """

    res = g.query(query)
    return load_result_into_json(res)
