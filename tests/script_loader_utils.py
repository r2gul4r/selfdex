from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, *, root: Path | None = None) -> ModuleType:
    script_root = ROOT if root is None else root
    path = script_root / "scripts" / name
    module_name = name.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
