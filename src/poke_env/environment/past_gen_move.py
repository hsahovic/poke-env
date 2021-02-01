from move import Move
from poke_env.data import GEN4_MOVES, GEN5_MOVES, GEN6_MOVES, GEN7_MOVES

from typing import Optional

class Gen4Move(Move):
    
    #def __init__(self, move: str = "", move_id: Optional[str] = None):
    #    super().__init__(move, move_id)
            
    @property
    def entry(self) -> dict:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: dict
        """
        if self._id in GEN4_MOVES:
            return GEN4_MOVES[self._id]
        else:
            raise ValueError("Unknown move: %s" % self._id)
            
class Gen5Move(Move):
    
    #def __init__(self, move: str = "", move_id: Optional[str] = None):
    #    super().__init__(self, move, move_id)
            
    @property
    def entry(self) -> dict:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: dict
        """
        if self._id in GEN5_MOVES:
            return GEN5_MOVES[self._id]
        else:
            raise ValueError("Unknown move: %s" % self._id)
            
class Gen6Move(Move):
    
    #def __init__(self, move: str = "", move_id: Optional[str] = None):
    #    super().__init__(self, move, move_id)
            
    @property
    def entry(self) -> dict:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: dict
        """
        if self._id in GEN6_MOVES:
            return GEN6_MOVES[self._id]
        else:
            raise ValueError("Unknown move: %s" % self._id)
            
class Gen7Move(Move):
    
    #def __init__(self, move: str = "", move_id: Optional[str] = None):
    #    super().__init__(self, move, move_id)
            
    @property
    def entry(self) -> dict:
        """
        Should not be used directly.

        :return: The data entry corresponding to the move
        :rtype: dict
        """
        if self._id in GEN7_MOVES:
            return GEN7_MOVES[self._id]
        elif self._id.startswith("z") and self._id[1:] in GEN7_MOVES:
            return GEN7_MOVES[self._id[1:]]
        else:
            raise ValueError("Unknown move: %s" % self._id)