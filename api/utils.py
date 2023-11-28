import json


def load_result_into_json(query_result):
    return json.loads(query_result.serialize(format="json"))
