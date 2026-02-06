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

    # Trim the JS wrapper to the main object
    data = "{" + "= {".join(data.split("= {")[1:])[:-2]

    # Normalize whitespace early
    data = data.replace("\t", " ")

    # Strip comments (// and /* */)
    data = re.sub(r" +//.*", "", data)
    data = re.sub(r"/\*.*?\*/", "", data, flags=re.DOTALL)

    # Helper: replace method shorthands like: name(params) { ... },
    for n_space in range(14):
        spaces = " " * n_space

        # Multiline method shorthand
        pattern_method = (
            r"^" + spaces +
            r"(\w+)\s*\(\s*[\s\S]*?\)\s*\{\n" +     # tolerate anything in (...)
            r"(?:.*\n)*?" +                          # lazy body
            spaces + r"\},"
        )
        sub = spaces + r'"\1": "\1",'
        data = re.sub(pattern_method, sub, data, flags=re.MULTILINE)

        # Empty/one-liners: name() {},
        pattern_method_empty = r"^" + spaces + r"(\w+)\s*\(\s*[\s\S]*?\)\s*\{\s*\},"
        data = re.sub(pattern_method_empty, sub, data, flags=re.MULTILINE)

        # Property with function keyword: name: function (...) { ... },
        pattern_fnkw = (
            r"^" + spaces +
            r'"?(\w+)"?\s*:\s*function\s*\(\s*[\s\S]*?\)\s*\{\n' +
            r"(?:.*\n)*?" +
            spaces + r"\},"
        )
        data = re.sub(pattern_fnkw, sub, data, flags=re.MULTILINE)

        # Arrow function with block body: name: (...) => { ... },
        pattern_arrow_block = (
            r"^" + spaces +
            r'"?(\w+)"?\s*:\s*\(\s*[\s\S]*?\)\s*=>\s*\{\n' +
            r"(?:.*\n)*?" +
            spaces + r"\},"
        )
        data = re.sub(pattern_arrow_block, sub, data, flags=re.MULTILINE)

        # Arrow function concise body: name: (...) => expr,
        pattern_arrow_expr = (
            r"^" + spaces +
            r'"?(\w+)"?\s*:\s*\(\s*[\s\S]*?\)\s*=>\s*(?:[^,\n]|\n(?!' + spaces + r'\S))*?,'
        )
        data = re.sub(pattern_arrow_expr, sub, data, flags=re.MULTILINE)

    # Empty callbacks like onX() {}
    data = re.sub(r"(\bon\w+\b|\b\w+Callback\b)\(\s*\)\s*\{\s*\}", r'"\1": "\1"', data)

    #Normalize the literal: () => null
    data = re.sub(r"\(\s*\)\s*=>\s*null", r"null", data)

    # Key/quote cleanup
    data = re.sub(r"([\w\d]+): ", r'"\1": ', data)              # quote bare keys
    data = re.sub(r"'([^'\n]+)'", r'"\1"', data)                # single → double

    # Remove extra blank lines / trailing commas
    for _ in range(3):
        data = re.sub(r"\n\n", "\n", data)
    data = re.sub(r",\n( +)\]", r"\n\1]", data)
    data = re.sub(r",\n( *)\}", r"\n\1}", data)

    # Fix tricky embedded quotes
    data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)
    data = re.sub(r': "(.*)"(.*)":(.*)",', r': "\1\2:\3",', data)
    data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)

    # Misc normalizations
    data = re.sub(r": undefined", r": null", data)
    data = re.sub(r"(\d+):", r'"\1":', data)
    data = re.sub(r"\bH: ", r'"H": ', data)
    data = re.sub(r", moves:", r', "moves":', data)
    data = re.sub(r", nature:", r', "nature":', data)

    # Final trailing-comma cleanup
    data = re.sub(r",\n( *)\}", r"\n\1}", data)
    data = re.sub(r",\n( +)\]", r"\n\1]", data)

    try:
        return json.loads(data) if deserialize else data
    except Exception as e:
        with open("out.json", "w+") as f:
            f.write(data)
        raise
