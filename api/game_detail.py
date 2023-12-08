from .utils import *
from fastapi import APIRouter
import requests
import ast
import random
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


def fetch_wikidata(params):
    url = "https://www.wikidata.org/w/api.php"
    try:
        return requests.get(url, params=params)
    except:
        return "There was an error"


@router.get("/games/{app_id}")
async def game_detail(app_id: str):
    # ------------ query local ttl ------------------------
    query = (
        prefix
        + f"""
    SELECT ?app_name ?release_date ?short_description ?background ?in_english ?developerName ?publisherName ?website ?support_email ?support_url 
                (GROUP_CONCAT(DISTINCT ?category; SEPARATOR=", ") as ?categories)
                (GROUP_CONCAT(DISTINCT ?genre; SEPARATOR=", ") as ?genres)
                (GROUP_CONCAT(DISTINCT ?platform; SEPARATOR=", ") as ?platforms)
                ?minimum_requirements ?recommended_requirements
                ?req_age ?header_image ?avg_playtime ?median_playtime ?negative_ratings ?positive_ratings ?owners 
                ?movies ?screenshots

    WHERE {{
    ?app :appid "{app_id}";
        rdfs:label ?app_name;
        OPTIONAL {{?app :short_description ?short_description.}}
        OPTIONAL {{?app :release_date ?release_date .}}
        OPTIONAL {{?app :background ?background.}}
        OPTIONAL {{?app :in_english ?in_english .}}
        OPTIONAL {{
                ?app :developer ?developer .
                ?developer rdfs:label ?developerName .}}
        OPTIONAL {{
            ?app :publisher ?publisher .
            ?publisher rdfs:label ?publisherName .}}
        OPTIONAL {{
            ?app :category ?categoryIRI . 
            ?categoryIRI rdfs:label ?category .}}
        OPTIONAL {{
            ?app :genre ?genreIRI .
            ?genreIRI rdfs:label ?genre .}}
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
    GROUP BY ?app_name ?release_date ?short_description ?background ?in_english ?developerName ?publisherName ?website ?support_email ?support_url ?minimum_requirements ?recommended_requirements 
        ?req_age ?header_image ?avg_playtime ?median_playtime ?negative_ratings ?positive_ratings ?owners 
        ?movies ?screenshots
    """
    )
    sparql_results = g.query(query)
    json_res = json.loads(sparql_results.serialize(format="json"))

    # ------------------ change string of list into list ------------
    key = "movies"
    if key in json_res["results"]["bindings"][0].keys():
        movies = json_res["results"]["bindings"][0]["movies"]["value"]
        lst_movies = ast.literal_eval(movies)
        rand_index = random.randint(0, len(lst_movies) - 1)
        chosen_movie = lst_movies[rand_index]["webm"]["max"]
        # movie 1 value string link
        json_res["results"]["bindings"][0]["movies"]["value"] = chosen_movie

    key = "screenshots"
    if key in json_res["results"]["bindings"][0].keys():
        screenshots = json_res["results"]["bindings"][0]["screenshots"]["value"]
        lst_screenshots = ast.literal_eval(screenshots)
        cnt_ss = 0
        if len(lst_screenshots) > 10:
            cnt_ss = 10
        else:
            cnt_ss = len(lst_screenshots)
        chosen_ss = []
        for i in range(cnt_ss):
            rand = random.randint(0, len(lst_screenshots) - 1)
            item_rand_ss = lst_screenshots[rand]["path_full"]
            chosen_ss.append(item_rand_ss)
            lst_screenshots.pop(rand)
        json_res["results"]["bindings"][0]["screenshots"]["value"] = chosen_ss
    # ------------ query external detail games -----------------------
    extData_game = external_data_games_detail(app_id)
    if extData_game != None:
        dct = dict()
        for key in extData_game.keys():
            if key not in json_res["results"]["bindings"][0].keys():
                dct = dict()
                dct["value"] = extData_game[key].value
                json_res["results"]["bindings"][0][key] = dct
            else:
                val = json_res["results"]["bindings"][0][key]["value"]
                val = val + f", {extData_game[key].value}"
                json_res["results"]["bindings"][0][key]["value"] = val

    # ------------ query external developer -----------------------
    # check if not empty
    nameDeveloper = json_res["results"]["bindings"][0]["developerName"]["value"]
    if nameDeveloper != "":
        exData_Developer = dev_pub_detail("developer", nameDeveloper)
        if exData_Developer != None:
            dct = dict()
            for key in exData_Developer.keys():
                if key not in json_res["results"]["bindings"][0].keys():
                    dct = dict()
                    dct["value"] = exData_Developer[key].value
                    json_res["results"]["bindings"][0][key] = dct
                else:
                    val = json_res["results"]["bindings"][0][key]["value"]
                    val = val + f", {exData_Developer[key].value}"
                    json_res["results"]["bindings"][0][key]["value"] = val

    # ------------ query external publisher -----------------------
    # check if not empty
    namePublisher = json_res["results"]["bindings"][0]["publisherName"]["value"]
    if namePublisher != "":
        exData_Publisher = dev_pub_detail("publisher", namePublisher)
        if exData_Publisher != None:
            dct = dict()
            for key in exData_Publisher.keys():
                if key not in json_res["results"]["bindings"][0].keys():
                    dct = dict()
                    dct["value"] = exData_Publisher[key].value
                    json_res["results"]["bindings"][0][key] = dct
                else:
                    val = json_res["results"]["bindings"][0][key]["value"]
                    val = val + f", {exData_Publisher[key].value}"
                    json_res["results"]["bindings"][0][key]["value"] = val

    return json_res


@router.get("/extGame/{app_id}")
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

    dbq_query = (
        prefix
        + f"""
    SELECT ?gameAbstract (GROUP_CONCAT(distinct(?genre); SEPARATOR=", ") as ?genres) where
    {{ ?s owl:sameAs <{url_wikidata}> .
    ?s dbo:abstract ?gameAbstract FILTER(LANG(?gameAbstract) = 'en').
        OPTIONAL {{
            ?s dbo:genre ?genreIRI .
            ?genreIRI rdfs:label ?genre FILTER(LANG(?genre) = 'en'). }}
    }}
    """
    )
    wrapper = SPARQLWrapper2(dbpedia_endpoint)
    wrapper.setQuery(dbq_query)
    wrapper.setTimeout(700)

    dbq_res = None
    if len(wrapper.query().bindings) != 0:
        dbq_res = wrapper.query().bindings[0]

    return dbq_res


@router.get("/extDevPub/{types}/{query_name}")
def dev_pub_detail(types, query_name):
    # search in wikidata
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "search": query_name,
        "language": "en",
    }
    data = fetch_wikidata(params)
    data = data.json()
    print(f"type: {types}")
    if len(data["search"]) != 0:
        wikidata_id = data["search"][0]["id"]  # get wikidata id
        print(f"wikidata id: {wikidata_id}")

        # get information from dbpedia
        dbpedia_endpoint = "https://dbpedia.org/sparql"
        wiki_uri_base = "http://www.wikidata.org/entity/"
        wiki_uri = wiki_uri_base + wikidata_id
        dbq_query = (
            prefix
            + f"""
        SELECT (COALESCE(?foafName, ?dbpName) AS ?{types}Name) ?{types}Abstract
            ?{types}Thumbnail ?{types}FounderName ?{types}FoundDate
            ?{types}NumEmployees ?{types}Homepage ?{types}Owner
            (COALESCE(?{types}LocCity, ?{types}Loc) AS ?{types}Location)

        WHERE
        {{
            ?{types} owl:sameAs <{wiki_uri}>;
                    dbo:abstract ?{types}Abstract .
            OPTIONAL {{?{types} foaf:name ?foafName}}.
            OPTIONAL {{?{types} dbp:name ?dbpName}}.
            OPTIONAL {{ ?{types} foaf:homepage ?{types}Homepage }}.
            OPTIONAL {{ ?{types} dbo:thumbnail ?{types}Thumbnail }}.
            OPTIONAL {{?{types} dbp:numEmployees ?{types}NumEmployees}}.
            OPTIONAL {{?{types} dbo:locationCity ?{types}LocCity }} .
            OPTIONAL {{?{types} dbo:location ?{types}Loc}}.
            OPTIONAL {{?{types} dbo:foundingDate ?{types}FoundDate}}.
            OPTIONAL {{?{types} dbp:founders ?{types}Founders.
                ?{types}Founders rdfs:label ?{types}FounderName}}.
            OPTIONAL {{?{types} dbp:owner ?{types}Owner}}
            }}
        """
        )

        wrapper = SPARQLWrapper2(dbpedia_endpoint)
        wrapper.setQuery(dbq_query)
        wrapper.setTimeout(1000000)

        dbq_res = None
        for index, db_result in enumerate(wrapper.query().bindings):
            # abstract (en)
            if db_result[f"{types}Abstract"].lang == "en":
                dbq_res = wrapper.query().bindings[index]
                break
        return dbq_res
    return None
