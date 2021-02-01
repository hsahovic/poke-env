from poke_env.environment.pokemon import Pokemon
from poke_env.environment.past_gen_move import Gen4Move, Gen5Move, Gen6Move, Gen7Move
from poke_env.data.pokedex_by_gen import gen4_pokedex, gen5_pokedex, gen6_pokedex, gen7_pokedex
from poke_env.environment.pokemon_type import PokemonType
from poke_env.utils import to_id_str

from typing import Any
from typing import Dict
from typing import Optional

class Gen4Pokemon(Pokemon):
    
    def __init__(self,
        *,
        species: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        ) -> None:
        super().__init__(species,request_pokemon,details)
        
    def _add_move(self, move_id: str, use: bool = False) -> None:
        """Store the move if applicable."""
        id_ = Gen4Move.retrieve_id(move_id)

        if not Gen4Move.should_be_stored(id_):
            return

        if id_ not in self._moves:
            move = Gen4Move(move_id=id_)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()
                  
    def _update_from_pokedex(self, species: str, store_species: bool = True) -> None:
        species = to_id_str(species)
        dex_entry = gen4_pokedex[species]
        if store_species:
            self._species = species
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        self._possible_abilities = dex_entry["abilities"]
        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]
        
class Gen5Pokemon(Pokemon):
    
    def __init__(self,
        *,
        species: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        ) -> None:
        super().__init__(species,request_pokemon,details)
        
    def _add_move(self, move_id: str, use: bool = False) -> None:
        """Store the move if applicable."""
        id_ = Gen5Move.retrieve_id(move_id)

        if not Gen5Move.should_be_stored(id_):
            return

        if id_ not in self._moves:
            move = Gen5Move(move_id=id_)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()
                        
    def _update_from_pokedex(self, species: str, store_species: bool = True) -> None:
        species = to_id_str(species)
        dex_entry = gen5_pokedex[species]
        if store_species:
            self._species = species
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        self._possible_abilities = dex_entry["abilities"]
        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]

class Gen6Pokemon(Pokemon):
    
    def __init__(self,
        *,
        species: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        ) -> None:
        super().__init__(species,request_pokemon,details)
        
    def _add_move(self, move_id: str, use: bool = False) -> None:
        """Store the move if applicable."""
        id_ = Gen6Move.retrieve_id(move_id)

        if not Gen6Move.should_be_stored(id_):
            return

        if id_ not in self._moves:
            move = Gen6Move(move_id=id_)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()
            
    def _mega_evolve(self, stone):
        species_id_str = to_id_str(self.species)
        mega_species = (
            species_id_str + "mega"
            if not species_id_str.endswith("mega")
            else species_id_str
        )
        if mega_species in gen6_pokedex:
            self._update_from_pokedex(mega_species, store_species=False)
        elif stone[-1] in "XY":
            mega_species = mega_species + stone[-1].lower()
            self._update_from_pokedex(mega_species, store_species=False)
            
    def _update_from_pokedex(self, species: str, store_species: bool = True) -> None:
        species = to_id_str(species)
        dex_entry = gen6_pokedex[species]
        if store_species:
            self._species = species
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        self._possible_abilities = dex_entry["abilities"]
        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]

class Gen7Pokemon(Pokemon):
    
    def __init__(self,
        *,
        species: Optional[str] = None,
        request_pokemon: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None,
        ) -> None:
        super().__init__(species,request_pokemon,details)
        
    def _add_move(self, move_id: str, use: bool = False) -> None:
        """Store the move if applicable."""
        id_ = Gen7Move.retrieve_id(move_id)

        if not Gen7Move.should_be_stored(id_):
            return

        if id_ not in self._moves:
            move = Gen7Move(move_id=id_)
            self._moves[id_] = move
        if use:
            self._moves[id_].use()
            
    def _mega_evolve(self, stone):
        species_id_str = to_id_str(self.species)
        mega_species = (
            species_id_str + "mega"
            if not species_id_str.endswith("mega")
            else species_id_str
        )
        if mega_species in gen7_pokedex:
            self._update_from_pokedex(mega_species, store_species=False)
        elif stone[-1] in "XY":
            mega_species = mega_species + stone[-1].lower()
            self._update_from_pokedex(mega_species, store_species=False)
            
    def _update_from_pokedex(self, species: str, store_species: bool = True) -> None:
        species = to_id_str(species)
        dex_entry = gen7_pokedex[species]
        if store_species:
            self._species = species
        self._base_stats = dex_entry["baseStats"]

        self._type_1 = PokemonType.from_name(dex_entry["types"][0])
        if len(dex_entry["types"]) == 1:
            self._type_2 = None
        else:
            self._type_2 = PokemonType.from_name(dex_entry["types"][1])

        self._possible_abilities = dex_entry["abilities"]
        self._heightm = dex_entry["heightm"]
        self._weightkg = dex_entry["weightkg"]
