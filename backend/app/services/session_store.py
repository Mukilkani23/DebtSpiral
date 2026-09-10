import json
import copy
from pathlib import Path
from ..schemas import Persona


_personas: dict[str, Persona] = {}
_baseline: dict[str, dict] = {}


def load_personas(path: str) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Personas file not found: {path}")
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    _baseline.clear()
    _personas.clear()
    for item in raw:
        persona = Persona(**item)
        _baseline[persona.persona_id] = item
        _personas[persona.persona_id] = persona


def get_persona(persona_id: str) -> Persona | None:
    return _personas.get(persona_id)


def get_all_personas() -> list[Persona]:
    return list(_personas.values())


def reset_all() -> None:
    _personas.clear()
    for pid, raw in _baseline.items():
        _personas[pid] = Persona(**copy.deepcopy(raw))


def update_persona(persona: Persona) -> None:
    _personas[persona.persona_id] = persona
