from functools import lru_cache


@lru_cache(2**13)
def to_id_str(name: str) -> str:
    """Converts a full-name to its corresponding id string.
    :param name: The name to convert.
    :type name: str
    :return: The corresponding id string.
    :rtype: str
    """
    return "".join(char for char in name if char.isalnum()).lower()
