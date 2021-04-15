"""
Pokedex numbers by gen:
    Gen 1: 001 - 151
    Gen 2: 152 - 251
    Gen 3: 252 - 386
    Gen 4: 387 - 493
    Gen 5: 494 - 649
    Gen 6: 650 - 721
    Gen 7: 722 - 809
    Gen 8: 810 - 898
"""
import json

max_mon_index = {1: 151, 2: 251, 3: 386, 4: 493, 5: 649, 6: 721, 7: 809}

for gen in range(7, 0, -1):
    print("Load gen {}".format(gen + 1))
    with open("gen" + str(gen + 1) + "_pokedex.json", "r") as f:
        new_gen = json.load(f)

    print("Load gen {} changes".format(gen))
    with open("gen" + str(gen) + "_pokedex_changes.json", "r") as f:
        file_content = f.read()
        if file_content != "{":
            old_gen = json.loads(file_content)
        else:
            with open("gen" + str(gen) + "_pokedex.json", "w+") as file:
                file.write(json.dumps(new_gen, indent=4, sort_keys=True))
                continue

    for mon, value in new_gen.items():
        if value["num"] > max_mon_index[gen]:
            continue
        if mon not in old_gen:
            old_gen[mon] = value
        elif old_gen[mon].get("inherit", False):
            old_gen[mon] = {**value, **old_gen[mon]}
            old_gen[mon].pop("inherit")
        if gen == 4:
            old_gen[mon]["abilities"].pop("H", None)

    print("Dump gen {}".format(gen))
    with open("gen" + str(gen) + "_pokedex.json", "w+") as f:
        f.write(json.dumps(old_gen, indent=4, sort_keys=True))
