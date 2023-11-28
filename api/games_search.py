from .utils import *
from fastapi import APIRouter

import rdflib

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")


@router.get("/api/games/search")
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
