import json
import re

import requests

CURRENT_GEN = 9
MAX_MON_IDX_PER_GEN = {1: 151, 2: 251, 3: 386, 4: 493, 5: 649, 6: 721, 7: 809, 8: 898}
MAX_MOVE_IDX_PER_GEN = {1: 165, 2: 251, 3: 354, 4: 467, 5: 559, 6: 621, 7: 742, 8: 850}
STATIC_DATA_ROOT = "src/poke_env/data/static"


def _replace_ps_callbacks(data: str) -> str:
    for function_title_pattern in (r"on\w+", r"\w+Callback"):
        pattern = (
            r"^([ ]*)("
            + function_title_pattern
            + r")\([^)]*\)(?:: [^{]+)? \{\n(?:.*\n)+?\1\},"
        )
        sub = r'\1"\2": "\2",'
        data = re.sub(pattern, sub, data, flags=re.MULTILINE)

        pattern = r"(" + function_title_pattern + r")\([^)]*\)(?:: [^{]+)? \{\s*\}"
        sub = r'"\1": "\1"'
        data = re.sub(pattern, sub, data, flags=re.MULTILINE)

    return data


def clean_ps_data_text(data: str, deserialize: bool = True):
    if data == "404: Not Found":
        return {}

    # Remove start and end of the file
    data = "{" + "= {".join(data.split("= {")[1:])[:-2]

    # Transform tabs into spaces
    data = data.replace("\t", " ")

    # Callback and handlers must be normalized before key quoting so typed
    # arguments such as `target: Pokemon` do not get rewritten as JSON keys.
    data = _replace_ps_callbacks(data)

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

    # Remove incorrect commas
    data = re.sub(r",\n( *)\}", r"\n\1}", data)

    # Null arrow functions
    data = re.sub(r"\(\) => null", r"null", data)

    # Remove incorrect commas
    data = re.sub(r",\n( *)\}", r"\n\1}", data)
    data = re.sub(r",\n( +)\]", r"\n\1]", data)
    # Correct malformed values that start with an accidental extra quote.
    # The broader historical fixer was greedy enough to strip quotes from
    # later inline object keys such as `"pokeball"` in learnset eventData.
    data = re.sub(r': ""([^"\n]+)":([^"\n]+)",', r': "\1:\2",', data)

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
        raise


def fetch_and_clean_ps_data(url: str, deserialize: bool = True):
    data = requests.get(url, timeout=10.0).text
    return clean_ps_data_text(data, deserialize=deserialize)
