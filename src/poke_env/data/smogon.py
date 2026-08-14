"""Access to Smogon's monthly Pokemon Showdown usage statistics."""

import gzip
import re
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import MappingProxyType
from typing import Any, Mapping, Optional, Union

import orjson
import requests

from poke_env.data.normalize import to_id_str

JsonPayload = Union[str, bytes, bytearray, memoryview]
_MONTH_PATTERN = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_DEFAULT_CACHE_DIR = Path(".poke_env_stats_cache")


class SmogonStatsError(Exception):
    """Base exception raised while loading Smogon usage statistics."""


class SmogonStatsNotFoundError(SmogonStatsError):
    """Raised when Smogon does not have the requested statistics snapshot."""


class SmogonStatsParseError(SmogonStatsError):
    """Raised when a statistics snapshot cannot be parsed."""


@dataclass(frozen=True, slots=True)
class Spread:
    """A nature and EV spread reported by Smogon.

    EVs are ordered as HP, Attack, Defense, Special Attack, Special Defense, and
    Speed.
    """

    nature: str
    evs: tuple[int, int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class CounterStats:
    """Smogon's checks-and-counters statistics for one opposing Pokemon.

    ``knockout_or_switch_probability`` is the probability that the subject Pokemon
    was knocked out by, or switched out against, this opposing Pokemon during a
    relevant encounter. ``standard_error`` measures the uncertainty in that
    probability.
    """

    id: str
    name: str
    weighted_encounters: float
    knockout_or_switch_probability: float
    standard_error: float

    @property
    def score(self) -> float:
        """Return Smogon's conservative checks-and-counters ranking score."""
        return self.knockout_or_switch_probability - 4 * self.standard_error


@dataclass(frozen=True, slots=True)
class PokemonUsageStats:
    """Usage statistics for one Pokemon in a Smogon snapshot.

    Frequencies are represented as fractions. For example, an item value of ``0.4``
    means that 40% of the weighted sets for this Pokemon held that item. Teammate
    scores are the signed difference between conditional teammate usage and overall
    metagame usage, rather than probabilities. Moves are marginal frequencies, so
    their values generally sum to four rather than one.
    """

    id: str
    name: str
    usage: float
    raw_count: int
    abilities: Mapping[str, float]
    items: Mapping[str, float]
    moves: Mapping[str, float]
    spreads: Mapping[Spread, float]
    tera_types: Mapping[str, float]
    teammate_scores: Mapping[str, float]
    checks_and_counters: Mapping[str, CounterStats]

    def top_counters(
        self, limit: Optional[int] = None, *, min_weighted_encounters: float = 0
    ) -> tuple[CounterStats, ...]:
        """Return checks and counters ordered by Smogon's conservative score."""
        _validate_limit(limit)
        _validate_finite_number(min_weighted_encounters, "min_weighted_encounters")
        if min_weighted_encounters < 0:
            raise ValueError("min_weighted_encounters must not be negative")

        matches = (
            counter
            for counter in self.checks_and_counters.values()
            if counter.weighted_encounters >= min_weighted_encounters
        )
        ordered = sorted(matches, key=lambda counter: (-counter.score, counter.id))
        return tuple(ordered[:limit])


@dataclass(frozen=True, slots=True)
class SmogonStats:
    """One cutoff-specific monthly snapshot of Smogon usage statistics."""

    battle_format: str
    month: str
    cutoff: int
    battle_count: int
    source_url: Optional[str]
    pokemon: Mapping[str, PokemonUsageStats]

    @classmethod
    def fetch(
        cls,
        battle_format: str,
        *,
        month: str,
        cutoff: int = 0,
        timeout: float = 30,
        cache_dir: Optional[Union[str, Path]] = _DEFAULT_CACHE_DIR,
        refresh: bool = False,
        compressed: bool = True,
    ) -> "SmogonStats":
        """Fetch and parse a snapshot from Smogon's public chaos directory.

        ``month`` is deliberately explicit so experiments remain reproducible.
        The default ``cutoff=0`` selects Smogon's unweighted statistics.

        Downloads use Smogon's gzip-compressed snapshots by default and are cached
        under ``.poke_env_stats_cache`` in the current directory. Pass
        ``cache_dir=None`` to disable caching, ``refresh=True`` to replace a cached
        snapshot, or ``compressed=False`` to request uncompressed JSON. If a
        compressed snapshot is unavailable, fetching falls back to uncompressed
        JSON.
        """
        normalized_format = to_id_str(battle_format)
        if not normalized_format:
            raise ValueError("battle_format must not be empty")
        _validate_month(month)
        _validate_non_negative_int(cutoff, "cutoff")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        filename = f"{normalized_format}-{cutoff}.json"
        source_url = f"https://www.smogon.com/stats/{month}/chaos/{filename}"
        cache_filename = f"{filename}.gz" if compressed else filename
        cache_path = (
            Path(cache_dir) / month / cache_filename if cache_dir is not None else None
        )

        if cache_path is not None and cache_path.is_file() and not refresh:
            try:
                stats = cls.from_file(cache_path, month=month, source_url=source_url)
                _validate_snapshot_metadata(stats, normalized_format, cutoff)
                return stats
            except SmogonStatsError:
                # A partial or otherwise invalid cache entry is replaced below.
                pass

        download_url = f"{source_url}.gz" if compressed else source_url
        try:
            response = requests.get(download_url, timeout=timeout)
            if response.status_code == 404 and compressed:
                download_url = source_url
                response = requests.get(download_url, timeout=timeout)
            if response.status_code == 404:
                raise SmogonStatsNotFoundError(
                    f"Smogon stats snapshot not found: {source_url}"
                )
            response.raise_for_status()
        except SmogonStatsNotFoundError:
            raise
        except requests.RequestException as exc:
            raise SmogonStatsError(
                f"Failed to fetch Smogon stats snapshot: {download_url}"
            ) from exc

        payload = (
            _decompress(response.content, download_url)
            if download_url.endswith(".gz")
            else response.content
        )
        stats = cls.from_json(payload, month=month, source_url=source_url)
        _validate_snapshot_metadata(stats, normalized_format, cutoff)
        if cache_path is not None:
            cache_payload = (
                response.content
                if download_url.endswith(".gz") or not compressed
                else gzip.compress(response.content)
            )
            _write_cache(cache_path, cache_payload)
        return stats

    @classmethod
    def from_file(
        cls, path: Union[str, Path], *, month: str, source_url: Optional[str] = None
    ) -> "SmogonStats":
        """Parse a locally stored Smogon chaos JSON or JSON.gz file."""
        file_path = Path(path)
        try:
            payload = file_path.read_bytes()
        except OSError as exc:
            raise SmogonStatsError(f"Failed to read Smogon stats file: {path}") from exc

        if file_path.suffix == ".gz":
            payload = _decompress(payload, str(file_path))

        return cls.from_json(
            payload, month=month, source_url=source_url or file_path.resolve().as_uri()
        )

    @classmethod
    def from_json(
        cls, payload: JsonPayload, *, month: str, source_url: Optional[str] = None
    ) -> "SmogonStats":
        """Parse a Smogon chaos JSON payload."""
        _validate_month(month)
        try:
            document = orjson.loads(payload)
            root = _mapping(document, "root")
            info = _mapping(root["info"], "info")
            data = _mapping(root["data"], "data")

            battle_format = to_id_str(_string(info["metagame"], "info.metagame"))
            if not battle_format:
                raise SmogonStatsParseError("info.metagame must not be empty")
            cutoff = _non_negative_int(info["cutoff"], "info.cutoff")
            battle_count = _non_negative_int(
                info["number of battles"], "info.number of battles"
            )

            pokemon = {}
            for name, pokemon_document in data.items():
                pokemon_name = _string(name, "Pokemon name")
                pokemon_id = to_id_str(pokemon_name)
                if not pokemon_id:
                    raise SmogonStatsParseError("Pokemon name must not be empty")
                if pokemon_id in pokemon:
                    raise SmogonStatsParseError(
                        f"Duplicate normalized Pokemon id: {pokemon_id}"
                    )
                pokemon[pokemon_id] = _parse_pokemon(
                    pokemon_name, _mapping(pokemon_document, pokemon_name)
                )
        except SmogonStatsParseError:
            raise
        except (KeyError, TypeError, orjson.JSONDecodeError) as exc:
            raise SmogonStatsParseError("Invalid Smogon chaos JSON payload") from exc

        return cls(
            battle_format=battle_format,
            month=month,
            cutoff=cutoff,
            battle_count=battle_count,
            source_url=source_url,
            pokemon=MappingProxyType(pokemon),
        )

    def __getitem__(self, species: str) -> PokemonUsageStats:
        """Return statistics for a Pokemon name or Showdown id."""
        return self.pokemon[to_id_str(species)]

    def get(self, species: str) -> Optional[PokemonUsageStats]:
        """Return statistics for a Pokemon name or Showdown id, if present."""
        return self.pokemon.get(to_id_str(species))

    def top_pokemon(
        self,
        limit: Optional[int] = None,
        *,
        min_usage: float = 0,
        min_raw_count: int = 0,
    ) -> tuple[PokemonUsageStats, ...]:
        """Return Pokemon ordered by weighted usage, with optional filters."""
        _validate_limit(limit)
        _validate_finite_number(min_usage, "min_usage")
        if min_usage < 0:
            raise ValueError("min_usage must not be negative")
        _validate_non_negative_int(min_raw_count, "min_raw_count")

        matches = (
            pokemon
            for pokemon in self.pokemon.values()
            if pokemon.usage >= min_usage and pokemon.raw_count >= min_raw_count
        )
        ordered = sorted(matches, key=lambda pokemon: (-pokemon.usage, pokemon.id))
        return tuple(ordered[:limit])


def _parse_pokemon(name: str, document: Mapping[str, Any]) -> PokemonUsageStats:
    pokemon_id = to_id_str(name)
    raw_count = _non_negative_int(document["Raw count"], f"{name}.Raw count")
    usage = _finite_number(document["usage"], f"{name}.usage")
    if usage < 0:
        raise SmogonStatsParseError(f"{name}.usage must not be negative")

    abilities = _weight_mapping(document["Abilities"], f"{name}.Abilities")
    weighted_count = sum(abilities.values())
    if weighted_count <= 0:
        raise SmogonStatsParseError(
            f"{name}.Abilities must have a positive total weight"
        )

    return PokemonUsageStats(
        id=pokemon_id,
        name=name,
        usage=usage,
        raw_count=raw_count,
        abilities=_normalized_named_mapping(abilities, weighted_count),
        items=_normalized_named_mapping(
            _weight_mapping(document["Items"], f"{name}.Items"), weighted_count
        ),
        moves=_normalized_named_mapping(
            _weight_mapping(document["Moves"], f"{name}.Moves"), weighted_count
        ),
        spreads=_spread_mapping(
            _weight_mapping(document["Spreads"], f"{name}.Spreads"),
            weighted_count,
            name,
        ),
        tera_types=_normalized_named_mapping(
            _weight_mapping(document.get("Tera Types", {}), f"{name}.Tera Types"),
            weighted_count,
        ),
        teammate_scores=_normalized_named_mapping(
            _weight_mapping(document["Teammates"], f"{name}.Teammates"), weighted_count
        ),
        checks_and_counters=_counter_mapping(
            document["Checks and Counters"], f"{name}.Checks and Counters"
        ),
    )


def _normalized_named_mapping(
    weights: Mapping[str, float], denominator: float
) -> Mapping[str, float]:
    normalized: dict[str, float] = {}
    for name, weight in weights.items():
        if weight == 0:
            continue
        id_ = to_id_str(name)
        if not id_:
            continue
        normalized[id_] = normalized.get(id_, 0.0) + weight / denominator
    return MappingProxyType(normalized)


def _spread_mapping(
    weights: Mapping[str, float], denominator: float, pokemon_name: str
) -> Mapping[Spread, float]:
    spreads: dict[Spread, float] = {}
    for spread_text, weight in weights.items():
        if weight == 0:
            continue
        try:
            nature, ev_text = spread_text.split(":", 1)
            raw_evs = tuple(int(ev) for ev in ev_text.split("/"))
        except (TypeError, ValueError) as exc:
            raise SmogonStatsParseError(
                f"Invalid spread for {pokemon_name}: {spread_text}"
            ) from exc
        if len(raw_evs) != 6 or any(ev < 0 for ev in raw_evs):
            raise SmogonStatsParseError(
                f"Invalid spread for {pokemon_name}: {spread_text}"
            )
        evs = (raw_evs[0], raw_evs[1], raw_evs[2], raw_evs[3], raw_evs[4], raw_evs[5])
        spread = Spread(nature=nature, evs=evs)
        spreads[spread] = spreads.get(spread, 0.0) + weight / denominator
    return MappingProxyType(spreads)


def _counter_mapping(value: Any, field: str) -> Mapping[str, CounterStats]:
    raw_mapping = _mapping(value, field)
    counters = {}
    for name, counter_document in raw_mapping.items():
        counter_name = _string(name, f"{field} key")
        counter_id = to_id_str(counter_name)
        if not counter_id:
            raise SmogonStatsParseError(f"{field} contains an empty Pokemon name")
        if counter_id in counters:
            raise SmogonStatsParseError(
                f"{field} contains duplicate normalized Pokemon id: {counter_id}"
            )

        counter = _mapping(counter_document, f"{field}.{counter_name}")
        weighted_encounters = _finite_number(counter["n"], f"{field}.{counter_name}.n")
        probability = _finite_number(counter["p"], f"{field}.{counter_name}.p")
        standard_error = _finite_number(counter["d"], f"{field}.{counter_name}.d")
        if weighted_encounters <= 0:
            raise SmogonStatsParseError(
                f"{field}.{counter_name}.n must be greater than zero"
            )
        if not 0 <= probability <= 1:
            raise SmogonStatsParseError(
                f"{field}.{counter_name}.p must be between zero and one"
            )
        if standard_error < 0:
            raise SmogonStatsParseError(
                f"{field}.{counter_name}.d must not be negative"
            )

        counters[counter_id] = CounterStats(
            id=counter_id,
            name=counter_name,
            weighted_encounters=weighted_encounters,
            knockout_or_switch_probability=probability,
            standard_error=standard_error,
        )
    return MappingProxyType(counters)


def _weight_mapping(value: Any, field: str) -> Mapping[str, float]:
    raw_mapping = _mapping(value, field)
    weights = {}
    for name, weight in raw_mapping.items():
        weights[_string(name, f"{field} key")] = _finite_number(
            weight, f"{field}.{name}"
        )
    return weights


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SmogonStatsParseError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise SmogonStatsParseError(f"{field} must be a string")
    return value


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SmogonStatsParseError(f"{field} must be a number")
    result = float(value)
    if not isfinite(result):
        raise SmogonStatsParseError(f"{field} must be finite")
    return result


def _non_negative_int(value: Any, field: str) -> int:
    number = _finite_number(value, field)
    if number < 0 or not number.is_integer():
        raise SmogonStatsParseError(f"{field} must be a non-negative integer")
    return int(number)


def _validate_month(month: str) -> None:
    if not isinstance(month, str) or not _MONTH_PATTERN.fullmatch(month):
        raise ValueError("month must use YYYY-MM format")


def _validate_finite_number(value: Any, field: str) -> None:
    try:
        _finite_number(value, field)
    except SmogonStatsParseError as exc:
        raise ValueError(str(exc)) from exc


def _validate_non_negative_int(value: Any, field: str) -> None:
    try:
        _non_negative_int(value, field)
    except SmogonStatsParseError as exc:
        raise ValueError(str(exc)) from exc


def _validate_limit(limit: Optional[int]) -> None:
    if limit is not None:
        _validate_non_negative_int(limit, "limit")


def _decompress(payload: bytes, source: str) -> bytes:
    try:
        return gzip.decompress(payload)
    except (OSError, EOFError) as exc:
        raise SmogonStatsParseError(
            f"Invalid gzip-compressed Smogon stats snapshot: {source}"
        ) from exc


def _validate_snapshot_metadata(
    stats: SmogonStats, battle_format: str, cutoff: int
) -> None:
    if stats.battle_format != battle_format or stats.cutoff != cutoff:
        raise SmogonStatsParseError(
            "Smogon stats metadata does not match the requested format and cutoff"
        )


def _write_cache(path: Path, payload: bytes) -> None:
    temporary_path: Optional[Path] = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(path)
    except OSError as exc:
        raise SmogonStatsError(
            f"Failed to cache Smogon stats snapshot: {path}"
        ) from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
