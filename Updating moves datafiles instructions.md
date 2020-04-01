# Updating `moves.json`

`src/poke_env/data/moves.json` is an adapted version of PokemonShowdown's `moves.js`.

This guide explains how to generate a `poke-env`-compatible version of `moves.json` from `moves.js`, as of April 1, 2020. Given the frequent updates of PokemonShowdown, these instructions might not remain up-to-date long after this date, but should nonetheless provide useful insights for future updates.

**All the following regex replacements were performed using VSCode's Regex engine.**

- Raw file:
    - Import PokemonShowdown data from [PokemonShowdown's `moves.js`](https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/moves.js).
    - Delete the start of the file, until the start of the object declaration (everything until the first relevant `{`.
    - Delete the end of the file, from the end of the object declaration (everything after the last relevant `}`.
    - Apply the following regex replacement: replace `\t` with ` ` (space character)
- Functions:
    - Apply the following regex replacement: replace `^  ((\S+Callback)|(on.+))\(.*\) \{\n(.*\n)+?  \},` with `  "$1": "$1",`
    - Apply the following regex replacement: replace `^   ((\S+Callback)|(on.+))\(.*\) \{\n(.*\n)+?   \},` with `   "$1": "$1",`
    - Apply the following regex replacement: replace `^    ((\S+Callback)|(on.+))\(.*\) \{\n(.*\n)+?    \},` with `    "$1": "$1",`
- Misc. corrections:
    - Apply the following regex replacement: replace `([ \{]+)([^ "]+):` with `$1"$2":` (double quotes properties)
    - Apply the following regex replacement: replace `//.+\n` with `` (comments)
    - Apply the following regex replacement: replace `'(.+?)'([,\]])` with `"$1"$2` (single quotes text)
    - Apply the following regex replacement: replace `,\n *([\}\]])` with `$1` (trailing commas)
    - Apply the following regex replacement: replace `: "(.*)"(.*)":(.*)",` with `: "$1$2:$3",` (double quotes inside double quoted text)

