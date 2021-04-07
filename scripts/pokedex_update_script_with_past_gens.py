# -*- coding: utf-8 -*-
import requests
import re


for gen in range(1, 9):

    if gen == 8:
        # Fetch latest version
        data = requests.get(
            "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/pokedex.ts"
        ).text
    else:
        data = requests.get(
            "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen"
            + str(gen)
            + "/pokedex.ts"
        ).text

    # Remove start and end of the file
    data = "{" + "= {".join(data.split("= {")[1:])[:-2]

    # Transform tabs into spaces
    data = data.replace("\t", " ")

    # Transform keys into correct json strings
    data = re.sub(r"([\w\d]+): ", r'"\1": ', data)

    # Transform single quoted text into double quoted text
    data = re.sub(r"'([\w\d]+)'", r'"\1"', data)

    # Remove comments
    data = re.sub(r" +//.+", "", data)

    # Remove empty lines
    for _ in range(3):
        data = re.sub(r"\n\n", "\n", data)

    # Remove incorrect commas
    data = re.sub(r",\n( *)\}", r"\n\1}", data)
    data = re.sub(r",\n( +)\]", r"\n\1]", data)

    # Correct double-quoted text inside double-quoted text
    data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)

    if gen != 8:
        with open("gen" + str(gen) + "_pokedex_changes.json", "w+") as f:
            f.write(data)
    else:
        with open("gen8_pokedex.json", "w+") as f:
            f.write(data)
