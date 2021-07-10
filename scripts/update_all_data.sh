python scripts/learnset_update_script.py
cp out.json src/poke_env/data/learnset.json
rm out.json

python scripts/pokedex_update_script_with_past_gens.py
python scripts/update_pokedex_from_following_gen.py

cp gen1_pokedex.json src/poke_env/data/pokedex_by_gen/gen1_pokedex.json
cp gen2_pokedex.json src/poke_env/data/pokedex_by_gen/gen2_pokedex.json
cp gen3_pokedex.json src/poke_env/data/pokedex_by_gen/gen3_pokedex.json
cp gen4_pokedex.json src/poke_env/data/pokedex_by_gen/gen4_pokedex.json
cp gen5_pokedex.json src/poke_env/data/pokedex_by_gen/gen5_pokedex.json
cp gen6_pokedex.json src/poke_env/data/pokedex_by_gen/gen6_pokedex.json
cp gen7_pokedex.json src/poke_env/data/pokedex_by_gen/gen7_pokedex.json
cp gen8_pokedex.json src/poke_env/data/pokedex.json

rm gen1_pokedex.json
rm gen2_pokedex.json
rm gen3_pokedex.json
rm gen4_pokedex.json
rm gen5_pokedex.json
rm gen6_pokedex.json
rm gen7_pokedex.json
rm gen8_pokedex.json

rm gen1_pokedex_changes.json
rm gen2_pokedex_changes.json
rm gen3_pokedex_changes.json
rm gen4_pokedex_changes.json
rm gen5_pokedex_changes.json
rm gen6_pokedex_changes.json
rm gen7_pokedex_changes.json

python scripts/move_update_script_with_past_gens.py
python scripts/update_moves_from_following_gen.py

cp gen1_moves.json src/poke_env/data/moves_by_gen/gen1_moves.json
cp gen2_moves.json src/poke_env/data/moves_by_gen/gen2_moves.json
cp gen3_moves.json src/poke_env/data/moves_by_gen/gen3_moves.json
cp gen4_moves.json src/poke_env/data/moves_by_gen/gen4_moves.json
cp gen5_moves.json src/poke_env/data/moves_by_gen/gen5_moves.json
cp gen6_moves.json src/poke_env/data/moves_by_gen/gen6_moves.json
cp gen7_moves.json src/poke_env/data/moves_by_gen/gen7_moves.json
cp gen8_moves.json src/poke_env/data/moves.json

rm gen1_moves.json
rm gen2_moves.json
rm gen3_moves.json
rm gen4_moves.json
rm gen5_moves.json
rm gen6_moves.json
rm gen7_moves.json
rm gen8_moves.json

rm gen1_move_changes.json
rm gen2_move_changes.json
rm gen3_move_changes.json
rm gen4_move_changes.json
rm gen5_move_changes.json
rm gen6_move_changes.json
rm gen7_move_changes.json