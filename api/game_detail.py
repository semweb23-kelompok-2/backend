from .utils import *
from fastapi import APIRouter
import requests
from SPARQLWrapper import JSON, SPARQLWrapper2

import rdflib

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

router = APIRouter()
g = rdflib.Graph()
g.parse("static/steam.ttl")

@router.get("/games/{app_id}")
async def game_detail(app_id: str):
    query = prefix + f"""
        SELECT ?app_name ?release_date ?background ?in_english ?developer ?publisher ?website ?support_email ?support_url 
                (GROUP_CONCAT(DISTINCT ?category; SEPARATOR=", ") as ?categories)
                (GROUP_CONCAT(DISTINCT ?genre; SEPARATOR=", ") as ?genres)
                (GROUP_CONCAT(DISTINCT ?platform; SEPARATOR=", ") as ?platforms)
                ?minimum_requirements ?recommended_requirements
                ?req_age ?header_image ?avg_playtime ?median_playtime ?negative_ratings ?positive_ratings ?owners 
                ?movies ?screenshots

    WHERE {{
    ?app :appid "{app_id}";
        rdfs:label ?app_name;
        OPTIONAL {{?app :release_date ?release_date .}}
        OPTIONAL {{?app :background ?background.}}
        OPTIONAL {{?app :in_english ?in_english .}}
        OPTIONAL {{?app :developer ?developer .}}
        OPTIONAL {{?app :publisher ?publisher .}}
        OPTIONAL {{?app :category ?category .}}
        OPTIONAL {{?app :genre ?genre .}}
        OPTIONAL {{?app :platforms ?platform .}}
        OPTIONAL {{?app :minimum_requirements ?minimum_requirements .}}
        OPTIONAL {{?app :recommended_requirements ?recommended_requirements .}}
        OPTIONAL {{?app :required_age ?req_age.}}
        OPTIONAL {{?app :header_image ?header_image .}}
        OPTIONAL {{?app :average_playtime ?avg_playtime .}}
        OPTIONAL {{?app :median_playtime ?median_playtime .}}
        OPTIONAL {{?app :movies ?movies .}}
        OPTIONAL {{?app :negative_ratings ?negative_ratings .}}
        OPTIONAL {{?app :positive_ratings ?positive_ratings .}}
        OPTIONAL {{?app :owners ?owners .}}
        OPTIONAL {{?app :screenshots ?screenshots.}}
        OPTIONAL {{?app :website ?website.}}
        OPTIONAL {{?app :support_email ?support_email.}}
        OPTIONAL {{?app :support_url ?support_url .}}
    }}
    GROUP BY ?app_name ?release_date ?background ?in_english ?developer ?publisher ?website ?support_email ?support_url ?minimum_requirements ?recommended_requirements 
        ?req_age ?header_image ?avg_playtime ?median_playtime ?negative_ratings ?positive_ratings ?owners 
        ?movies ?screenshots
    """
    res = g.query(query)

    # TODO: combine the data -> genre + abstract, problem: runtime lama bgt
    # datatype: sparql + dictionary
    # external_data = dbpedia_query(app_id)

    # # Convert SPARQLResult to a dictionary
    # result_dict = {}
    # for row in res.bindings:
    #     for var, value in row.items():
    #         result_dict[str(var)] = str(value)

    # merged_dict = {**result_dict, **external_data}
    # json_result = json.dumps(merged_dict)
    # return json_result

    return json.loads(res.serialize(format="json"))

@router.get("/external-data/{app_id}")
def dbpedia_query(app_id):
    # wikidata
    wikidata_endpoint = "https://query.wikidata.org/sparql"

    query_wd_appid = f"""
    SELECT DISTINCT ?item ?statement0 WHERE {{
        ?item p:P1733 ?statement0.
        ?statement0 (ps:P1733) "{app_id}".
    }}
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
    }
    params = {
        "query": query_wd_appid,
        "format": "json",
    }

    response = requests.get(wikidata_endpoint, headers=headers, params=params)
    data = response.json()

    url_wikidata = ""
    for item in data["results"]["bindings"]:
        url_wikidata = item["item"]["value"]

    print(url_wikidata)
    
    # dbpedia
    dbpedia_endpoint = "https://dbpedia.org/sparql"

    dbpedia_query = prefix + f"""
    SELECT ?abstract (GROUP_CONCAT(distinct(?genre); SEPARATOR=", ") as ?genres) where
    {{ ?s owl:sameAs <{url_wikidata}> .
    ?s  dbo:abstract ?abstract ;
        dbo:genre ?genre
    }}
    """
    wrapper = SPARQLWrapper2(dbpedia_endpoint)
    wrapper.setQuery(dbpedia_query)

    for index, db_result in enumerate(wrapper.query().bindings):
        # abstract (en)
        if db_result["abstract"].lang == "en":
            dbq_res = wrapper.query().bindings[index]
            abstract = db_result["abstract"].value
            genre = db_result["genres"].value
            break
    print(f"abstract: {abstract}")
    print(f"genre: {genre}")

    return dbq_res

"""
TODO:
data tambahan (developer):
    dbo:abstract
    dbo:foundingDate
    dbo:foundingYear
    dbo:locationCity
    dbo:product
    dbo:type
    rdfs:company
    rdfs:label
    dbo:parentCompany
    dbo:publisher (also publisher of)

data tambahan (genre):
    rdfs:comment
    dbo:abstract
    dbo:wikiPageWikiLink

problem: no id? how can we get genre && developer
--> search through wiki
"""


