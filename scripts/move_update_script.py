# -*- coding: utf-8 -*-
import requests
import re

# Fetch latest version
data = requests.get(
    "https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/moves.ts"
).text

# Remove start and end of the file
data = "{" + "= {".join(data.split("= {")[1:])[:-2]

# Transform tabs into spaces
data = data.replace("\t", " ")

# Transform keys into correct python strings
data = re.sub(r"(\w+): ", r'"\1": ', data)

# Transform single quoted text into double quoted text
data = re.sub(r"'(\w+)'", r'"\1"', data)

# Remove comments
data = re.sub(r" +//.+", "", data)

# Remove empty lines
for _ in range(3):
    data = re.sub(r"\n\n", "\n", data)

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

# Remove incorrect commas
data = re.sub(r",\n( *)\}", r"\n\1}", data)
data = re.sub(r",\n( +)\]", r"\n\1]", data)

# Correct double-quoted text inside double-quoted text
data = re.sub(r': "(.*)"(.*)":(.*)",', r': "\1\2:\3",', data)
data = re.sub(r': ""(.*)":(.*)",', r': "\1:\2",', data)


with open("out.json", "w+") as f:
    f.write(data)
