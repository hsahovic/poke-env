"""
Move indexes to gen:
    Gen 1: 001 - 165
    Gen 2: 166 - 251
    Gen 3: 252 - 354
    Gen 4: 355 - 467
    Gen 5: 468 - 559
    Gen 6: 560 - 621
    Gen 7: 622 - 742
    Gen 8: 743 - 826 (Gmax moves are all 1000)
"""
import json

max_move_index = {1: 165, 2: 251, 3: 354, 4: 467, 5: 559, 6: 621, 7: 742}

for gen in range(7, 0, -1):
    file = open("gen" + str(gen + 1) + "_moves.json", "r")
    new_gen = json.load(file)
    file.close()

    file = open("gen" + str(gen) + "_move_changes.json", "r")
    old_gen = json.load(file)
    file.close()

    for move, value in new_gen.items():
        print("{}, gen {}".format(move, gen))
        if value["num"] > max_move_index[gen]:
            continue
        if move not in old_gen:
            old_gen[move] = value
            continue
        if old_gen[move].get("inherit", False):
            old_gen[move] = {**value, **old_gen[move]}
            old_gen[move].pop("inherit")

    with open("gen" + str(gen) + "_moves.json", "w+") as f:
        f.write(json.dumps(old_gen, indent=4, sort_keys=True))
