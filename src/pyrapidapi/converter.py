from parse import parse, search, findall, with_pattern
import parse
import regex as re
from loguru import logger
import ast
from typing import List, Dict, Callable

#This module uses reStructuredText as a format.

def extract_fields(string: str) -> dict:
    """RapidAPI automatically generates code snippets. This takes a code snippet for the requests library and extracts the fields of interest, allowing you to generate a function that can be used to make the request.
    :params string: A string containing the code snippet for the requests library.
    :returns: A dictionary containing the fields of interest.
    """
    request_types = search("response = requests.request(\"{}\",", string)
    if not request_types:
        raise ValueError("Could not find request type – I looked for the pattern: response = requests.request(\"{}\",")
    elif isinstance(request_types, parse.Result) and request_types is not None:
        request_type: str = request_types[0] #type: ignore
    else:
        raise ValueError("Something very weird happened. I couldn't find the request type.")
    patterns = {
        "host_name": "x-rapidapi-host': \"{}\",\n",
        "url": "url = \"{}\"",
        "payload": "payload = \"{}\"\nheaders",
    }
    located_fields = {"request_type": request_type}
    for pattern in patterns:
        try:
            located_fields[pattern] = search(patterns[pattern], string)[0] #type: ignore
        except Exception:
            logger.debug(f"Could not find {pattern} in the string")
            pass
    try:
        querystring = search("querystring = {}\n", string)[0] #type: ignore
        fields = ast.literal_eval(querystring)
        located_fields["query_fields"] = fields
    except Exception as e:
        logger.debug(f"Could not find querystring in the string: {e}")
        pass
    if "payload" in located_fields:
        payload = located_fields["payload"]
        try:
            payload_fields = ast.literal_eval(payload)
            if isinstance(payload_fields, list):
                payload_fields = payload_fields[0]
            located_fields["payload_fields"] = payload_fields
            del located_fields["payload"]
        except Exception:
            try:
                fields = []
                for field in payload.split("&"):
                    field_name = field.split("=")[0]
                    cleaned_field_name = re.sub("[^a-zA-Z0-9]", "", field_name)
                    fields.append(cleaned_field_name)
                located_fields["payload_fields"] = fields #type: ignore
            except Exception:
                pass
    return located_fields

def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = name.replace("-", "_")
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


import json
def dict_to_post_request_function(func_name: str, dic: dict, fields_of_interest: List[str]) -> str:
    """This function takes a dictionary containing the fields of interest and generates a function that can be used to make the request.
    :params func_name: The name of the function to be generated.
    :params dic: A dictionary containing the fields of interest."""
    template = """
@apis.json_decode({fields_of_interest})
@apis.post(
    "{url}",
    "{host_name}",
)
def {func_name}({keyword_args}) -> Tuple[str, dict]:
    return json.dumps([{payload}], {query_string}
    """
    url = dic["url"]
    host_name = dic["host_name"]
    keyword_args = str()
    for field, key in list(dic["payload_fields"].items()) + list(dic["query_fields"].items()):
        key_type = str(type(key)) #will return <class 'str'>, so we need to capture everything between ' and '>
        key_type = key_type.split("'")[1].split("'>")[0]
        keyword_args += f"{camel_to_snake(field)}: {key_type} = {json.dumps(key)}, "
    payload = dict()
    for field, _ in dic["payload_fields"].items():
        payload[field] = f"{camel_to_snake(field)}"
    query = dict()
    for field, _ in dic["query_fields"].items():
        query[field] = f"{camel_to_snake(field)}"
    payload = "{" + ", ".join(["'{}': {}".format(k, v) for k, v in payload.items()]) + "}"
    query_string = "{" + ", ".join(["'{}': {}".format(k, v) for k, v in query.items()]) + "}"
    template = template.format(
        fields_of_interest=json.dumps(fields_of_interest),
        url=url,
        host_name=host_name,
        func_name=func_name,
        keyword_args=keyword_args,
        payload=payload,
        query_string=query_string,
    )
    return template

import inspect
def to_post(name: str, desired_fields: list[str], func_source: str) -> str:
    fields: dict = extract_fields(func_source)
    converted_func: str = dict_to_post_request_function(name, fields, desired_fields)
    return converted_func