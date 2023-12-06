from .utils import *
from fastapi import APIRouter

import rdflib

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")

prefix = """
    prefix v: <http://example.org/vocab#>
    prefix owl: <http://www.w3.org/2002/07/owl#>
    prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix xml: <http://www.w3.org/XML/1998/namespace>
    prefix xsd: <http://www.w3.org/2001/XMLSchema#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    prefix vcard: <http://www.w3.org/2006/vcard/ns#>
    prefix dbo: <http://dbpedia.org/ontology/>
    prefix dbp: <http://dbpedia.org/property/>
    prefix dbr: <http://dbpedia.org/resource/>
    prefix foaf: <http://xmlns.com/foaf/0.1/>
    prefix : <http://127.0.0.1:8000/>
    """


@router.get("/games/search")
async def search_games(
    name: str = "",
    skip: int = 0,
    limit: int = 50,
    genre: str = None,
    category: str = None,
):
    query = (
        prefix
        + f"""
        SELECT ?app_id ?app_name ?header_image ?background ?positive_ratings 
            ?negative_ratings ?in_english ?release_date 
            (GROUP_CONCAT(distinct(?category); SEPARATOR=", ") as ?categories)
            (GROUP_CONCAT(distinct(?genre_label); SEPARATOR=", ") as ?genres)
        WHERE {{
            ?app a :Game ;
                rdfs:label ?app_name ;
                :appid ?app_id ;
                :header_image ?header_image ;
                :background ?background ;
                :positive_ratings ?positive_ratings ;
                :negative_ratings ?negative_ratings ;
                :in_english ?in_english ;
                :release_date ?release_date ;
                :category ?category ;
                :genre ?genre .
            ?genre rdfs:label ?genre_label .

            {f'''
            {{ 
                SELECT ?genre_select_app_id
                WHERE {{
                    ?app a :Game ;
                        :appid ?genre_select_app_id ;
                        :genre ?genre_select_genre .
                    ?genre_select_genre rdfs:label ?genre_select_genre_label .
                    FILTER (regex(?genre_select_genre_label, "{genre}", "i"))
                }}
            }}
            FILTER (?app_id = ?genre_select_app_id)
            ''' if genre else ''}

            # filter by category same way as genre
            {f'''
            {{
                SELECT ?category_select_app_id
                WHERE {{
                    ?app a :Game ;
                        :appid ?category_select_app_id ;
                        :category ?category_select_category .
                    FILTER (regex(?category_select_category, "{category}", "i"))
                }}
            }}
            FILTER (?app_id = ?category_select_app_id)
            ''' if category else ''}

            FILTER (regex(?app_name, "{name}", "i"))
        }}
        GROUP BY ?app_id ?app_name ?header_image ?background ?positive_ratings 
            ?negative_ratings ?in_english ?release_date 
        ORDER BY ?app_name 
        LIMIT {limit}
        OFFSET {skip}
    """
    )

    res = g.query(query)
    # return the result in json format without using process_result
    return load_result_into_json(res)


@router.get("/games/genres")
async def get_genres():
    query = (
        prefix
        + f"""
        SELECT ?genre_label
        WHERE {{
            ?genre a :Genre ;
                rdfs:label ?genre_label .
        }}
    """
    )

    res = g.query(query)
    return load_result_into_json(res)


@router.get("/games/categories")
async def get_categories():
    query = (
        prefix
        + f"""
        SELECT DISTINCT ?category
        WHERE {{
            ?game :category ?category .
        }}
    """
    )

    res = g.query(query)
    return load_result_into_json(res)
