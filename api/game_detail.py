from .utils import *
from fastapi import APIRouter
import requests
import ast
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

    # ------------ query local ttl ------------------------
    query = prefix + f"""
        SELECT ?app_name ?release_date ?background ?in_english ?nameDeveloper ?namePublisher ?website ?support_email ?support_url 
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
        OPTIONAL {{
                ?app :developer ?developer .
                ?developer rdfs:label ?nameDeveloper .}}
        OPTIONAL {{
            ?app :publisher ?publisher .
            ?publisher rdfs:label ?namePublisher .}}
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
    GROUP BY ?app_name ?release_date ?background ?in_english ?nameDeveloper ?namePublisher ?website ?support_email ?support_url ?minimum_requirements ?recommended_requirements 
        ?req_age ?header_image ?avg_playtime ?median_playtime ?negative_ratings ?positive_ratings ?owners 
        ?movies ?screenshots
    """
    sparql_results = g.query(query)
    json_res = json.loads(sparql_results.serialize(format="json"))

    # ------------------ change string of list into list ------------
    # movies = json_res['results']['bindings'][0]["movies"]
    # lst_movies = ast.literal_eval(movies)
    # json_res['results']['bindings'][0]["movies"] = lst_movies

    # screenshots = json_res['results']['bindings'][0]["screenshots"]
    # lst_screenshots = ast.literal_eval(screenshots)
    # json_res['results']['bindings'][0]["screenshots"] = lst_screenshots

    # ------------ query external detail games -----------------------
    extData_game = external_data_games_detail(app_id)
    dct = dict()
    for key in extData_game.keys():
        if key not in json_res['results']['bindings'][0].keys():
            dct = dict()
            dct["value"] = extData_game[key].value
            json_res['results']['bindings'][0][key] = dct
        else:
            val = json_res['results']['bindings'][0][key]["value"]
            val = val + f", {extData_game[key].value}"
            json_res['results']['bindings'][0][key]["value"] = val

    # ------------ query external developer -----------------------
    # check if not empty
    nameDeveloper = json_res['results']['bindings'][0]["nameDeveloper"]["value"]
    if nameDeveloper != "":
        exData_Developer = developer_detail(nameDeveloper)
        dct = dict()
        for key in exData_Developer.keys():
            if key not in json_res['results']['bindings'][0].keys():
                dct = dict()
                dct["value"] = exData_Developer[key].value
                json_res['results']['bindings'][0][key] = dct
            else:
                val = json_res['results']['bindings'][0][key]["value"]
                val = val + f", {exData_Developer[key].value}"
                json_res['results']['bindings'][0][key]["value"] = val

    # ------------ query external publisher -----------------------
    # check if not empty

    # ------------ query external genre -----------------------
    # check if not empty

    return json_res

@router.get("/external-data/{app_id}")
def external_data_games_detail(app_id):
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

    dbq_query = prefix + f"""
    SELECT ?abstract (GROUP_CONCAT(distinct(?genre); SEPARATOR=", ") as ?genres) where
    {{ ?s owl:sameAs <{url_wikidata}> .
    ?s  dbo:abstract ?abstract ;
        dbo:genre ?genre
    }}
    """
    wrapper = SPARQLWrapper2(dbpedia_endpoint)
    wrapper.setQuery(dbq_query)

    dbq_res = None
    for index, db_result in enumerate(wrapper.query().bindings):
        # abstract (en)
        if db_result["abstract"].lang == "en":
            dbq_res = wrapper.query().bindings[index]
            abstract = db_result["abstract"].value
            genre = db_result["genres"].value
            break

    return dbq_res

@router.get("/developer/{query_name}")
def developer_detail(query_name):
    # Which parameters to use
    params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'search': query_name,
            'language': 'en'
        }
    data = fetch_wikidata(params)
    data = data.json()

    wikidata_id = data['search'][0]['id']
    print(wikidata_id)
    dbpedia_endpoint = "https://dbpedia.org/sparql"

    wiki_uri_base = "http://www.wikidata.org/entity/"
    wiki_uri = wiki_uri_base+wikidata_id

    dbq_query = prefix + f"""
    SELECT ?developerName ?developerAbstract
        ?developerThumbnail ?developerFounderName ?developerFoundDate
        ?developerNumEmployees ?developerHomepage ?developerOwner
        (COALESCE(?developerLocCity, ?developerLoc) AS ?developerLocation) WHERE
    {{
        ?developer owl:sameAs <{wiki_uri}>;
        foaf:name ?developerName ;
        dbo:abstract ?developerAbstract .
        OPTIONAL {{ ?developer foaf:homepage ?developerHomepage }}.
        OPTIONAL {{ ?developer dbo:thumbnail ?developerThumbnail }}.
        OPTIONAL {{?developer dbp:numEmployees ?developerNumEmployees}}.
        OPTIONAL {{?developer dbo:locationCity ?developerLocCity }} .
        OPTIONAL {{?developer dbo:location ?developerLoc}}.
        OPTIONAL {{?developer dbo:foundingDate ?developerFoundDate}}.
        OPTIONAL {{?developer dbp:founders ?developerFounders.
            ?developerFounders rdfs:label ?developerFounderName}}.
        OPTIONAL {{?developer dbp:owner ?developerOwner}}
        }}
        GROUP BY ?developerName ?developerAbstract ?developerThumbnail ?developerFounders ?developerFoundDate
        ?developerNumEmployees ?developerHomepage ?developerLocCity ?developerLoc ?developerOwner
    """

    wrapper = SPARQLWrapper2(dbpedia_endpoint)
    wrapper.setQuery(dbq_query)

    dbq_res = None
    for index, db_result in enumerate(wrapper.query().bindings):
        # abstract (en)
        if db_result["developerAbstract"].lang == "en":
            dbq_res = wrapper.query().bindings[index]
            break
    return dbq_res

def fetch_wikidata(params):
    url = 'https://www.wikidata.org/w/api.php'
    try:
        return requests.get(url, params=params)
    except:
        return 'There was an error'



