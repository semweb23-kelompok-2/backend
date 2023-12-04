from .utils import *
from fastapi import APIRouter

import rdflib

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")

prefix = "prefix : <http://127.0.0.1:8000/>"


@router.get("/games/search")
async def search_games(name: str, skip: int = 0, limit: int = 50, genre: str = None):
    query = f"""
        {prefix}

        SELECT ?app_id ?app_name ?header_image ?background ?positive_ratings ?negative_ratings (GROUP_CONCAT(distinct(?genre_label); SEPARATOR=", ") as ?genres)
        WHERE {{
            ?app a :Game ;
                rdfs:label ?app_name ;
                :appid ?app_id ;
                :header_image ?header_image ;
                :background ?background ;
                :positive_ratings ?positive_ratings ;
                :negative_ratings ?negative_ratings ;
                :genre ?genre .
            ?genre rdfs:label ?genre_label .

            # select query that selects the app that genre matches the genre argument
            {f'''
            {{ 
                SELECT ?selected_app_id
                WHERE {{
                    ?app a :Game ;
                        :appid ?selected_app_id ;
                        :genre ?selected_genre .
                    ?selected_genre rdfs:label ?selected_genre_label .
                    FILTER (regex(?selected_genre_label, "{genre}", "i"))
                }}
            }}
            FILTER (?app_id = ?selected_app_id)
            ''' if genre else ''}

            FILTER (regex(?app_name, "{name}", "i"))
        }}
        GROUP BY ?app_id ?app_name ?header_image ?background ?positive_ratings ?negative_ratings
        ORDER BY ?app_name 
        LIMIT {limit}
        OFFSET {skip}
    """

    res = g.query(query)
    # return the result in json format without using process_result
    return load_result_into_json(res)


@router.get("/games/genres")
async def get_genres():
    query = f"""
        {prefix}

        SELECT ?genre_label
        WHERE {{
            ?genre a :Genre ;
                rdfs:label ?genre_label .
        }}
    """

    res = g.query(query)
    return load_result_into_json(res)
