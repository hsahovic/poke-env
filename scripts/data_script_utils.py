import json
import re

import requests

CURRENT_GEN = 9
MAX_MON_IDX_PER_GEN = {1: 151, 2: 251, 3: 386, 4: 493, 5: 649, 6: 721, 7: 809, 8: 898}
MAX_MOVE_IDX_PER_GEN = {1: 165, 2: 251, 3: 354, 4: 467, 5: 559, 6: 621, 7: 742, 8: 850}
STATIC_DATA_ROOT = "src/poke_env/data/static"


def fetch_and_clean_ps_data(url: str, deserialize: bool = True):
    data = requests.get(url).text

    if data == "404: Not Found":
        return {}

    # Remove start and end of the file
    data = "{" + "= {".join(data.split("= {")[1:])[:-2]

    # Transform tabs into spaces
    data = data.replace("\t", " ")

    # Transform keys into correct json strings
    data = re.sub(r"([\w\d]+): ", r'"\1": ', data)

    # Transform single quoted text into double quoted text
    data = re.sub(r"'([\w\d ]+)'", r'"\1"', data)

    # Remove comments
    data = re.sub(r" +//.+", "", data)

    # Remove empty lines
    for _ in range(3):
        data = re.sub(r"\n\n", "\n", data)

    data = re.sub(r",\n( +)\]", r"\n\1]", data)

    # Correct double-quoted text inside double-quoted text
    data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)

    # Correct isolated "undefined" values
    data = re.sub(r": undefined", r": null", data)

    # Callback and handlers
    for function_title_match in (r"(on\w+)", r"(\w+Callback)"):
        for n_space in range(10):
            spaces = " " * (n_space)
            pattern = (
                r"^"
                + spaces
                + function_title_match
                + r"\((\w+, )*(\w+)?\) \{\n(.+\n)+?"
                + spaces
                + r"\},"
            )
            sub = spaces + r'"\1": "\1",'
            data = re.sub(pattern, sub, data, flags=re.MULTILINE)
        pattern = function_title_match + r"\(\) \{\s*\}"
        sub = r'"\1": "\1"'
        data = re.sub(pattern, sub, data, flags=re.MULTILINE)

    # Remove incorrect commas
    data = re.sub(r",\n( *)\}", r"\n\1}", data)

    # Null arrow functions
    data = re.sub(r"\(\) => null", r"null", data)

    # Remove incorrect commas
    data = re.sub(r",\n( *)\}", r"\n\1}", data)
    data = re.sub(r",\n( +)\]", r"\n\1]", data)
    # Correct double-quoted text inside double-quoted text

    data = re.sub(r': "(.*)"(.*)":(.*)",', r': "\1\2:\3",', data)
    data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)

    # Correct non-quoted number keys
    data = re.sub(r"(\d+):", r'"\1":', data)
    # Correct non-quoted H keys

    data = re.sub(r"H: ", r'"H": ', data)
    data = re.sub(r", moves:", r', "moves":', data)
    data = re.sub(r", nature:", r', "nature":', data)

    try:
        if deserialize:
            return json.loads(data)
        else:
            return data
    except Exception:
        with open("out.json", "w+") as f:
            f.write(data)
        raise Exception
