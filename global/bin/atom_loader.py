#!/usr/bin/env python3
"""
Atom Loader — Acid Burn

Responsible for discovering, validating, and loading true Atoms that live under
`atoms/` with a deterministic Python toolchain.

This is the core of making Atoms first-class citizens in the harness.

Design principles:
- Python native imports only
- Strict validation (fail fast and loud)
- No special cases per Atom — everything driven by the YAML declaration
- Designed to be usable by both dispatch and by Qwen/Hermes for planning
"""

import importlib
import yaml
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field


@dataclass
class AtomToolchain:
    """Represents the loaded Python toolchain for an Atom."""
    package_name: str
    command_builder: Callable
    output_parser: Callable
    module: Any  # the imported module


@dataclass
class AtomDefinition:
    """Fully loaded and validated Atom."""
    id: str
    yaml_path: Path
    definition: dict
    toolchain: AtomToolchain
    safety_class: str
    requires_sudo: bool = False


class AtomLoadError(Exception):
    """Raised when an Atom fails to load or validate."""
    pass


def find_all_atoms(atoms_root: Path = None) -> list[Path]:
    """Discover all Atom YAML files under atoms/."""
    if atoms_root is None:
        atoms_root = Path(__file__).parent.parent.parent / "atoms"

    atom_yamls = []
    for yaml_file in atoms_root.rglob("*.yaml"):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data and data.get("kind") == "atom":
                atom_yamls.append(yaml_file)
        except Exception:
            continue  # Skip invalid YAMLs
    return atom_yamls


def load_atom(yaml_path: Path | str) -> AtomDefinition:
    """
    Load a single Atom from its YAML declaration.

    This is the main entry point.
    """
    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        raise AtomLoadError(f"Atom YAML not found: {yaml_path}")

    with open(yaml_path) as f:
        atom_def = yaml.safe_load(f)

    if not atom_def or atom_def.get("kind") != "atom":
        raise AtomLoadError(f"{yaml_path} is not a valid Atom (missing kind: atom)")

    atom_id = atom_def.get("id")
    if not atom_id:
        raise AtomLoadError(f"Atom at {yaml_path} is missing required 'id' field")

    impl = atom_def.get("implementation", {})
    toolchain_decl = impl.get("toolchain", {})

    package_name = toolchain_decl.get("python_package")
    if not package_name:
        raise AtomLoadError(f"Atom '{atom_id}' does not declare a python_package in implementation.toolchain")

    # Dynamically import the Python toolchain
    try:
        module = importlib.import_module(package_name)
    except ImportError as e:
        raise AtomLoadError(f"Failed to import Python package '{package_name}' for Atom '{atom_id}': {e}")

    # Validate required functions exist
    builder_name = toolchain_decl.get("command_builder", "command_builder.build_command")
    parser_name = toolchain_decl.get("output_parser", "output_parser.parse")

    try:
        command_builder = _resolve_dotted_name(module, builder_name)
        output_parser = _resolve_dotted_name(module, parser_name)
    except AttributeError as e:
        raise AtomLoadError(f"Atom '{atom_id}' toolchain is incomplete: {e}")

    toolchain = AtomToolchain(
        package_name=package_name,
        command_builder=command_builder,
        output_parser=output_parser,
        module=module
    )

    return AtomDefinition(
        id=atom_id,
        yaml_path=yaml_path,
        definition=atom_def,
        toolchain=toolchain,
        safety_class=atom_def.get("safety_class", "unknown"),
        requires_sudo=atom_def.get("implementation", {}).get("requires_sudo", False),
    )


def _resolve_dotted_name(module: Any, dotted_name: str) -> Callable:
    """Resolve 'command_builder.build_command' or 'output_parser.parse_csv_output'."""
    parts = dotted_name.split(".")
    obj = module
    for part in parts:
        obj = getattr(obj, part)
    if not callable(obj):
        raise AttributeError(f"{dotted_name} is not callable")
    return obj


def load_all_atoms(atoms_root: Path = None) -> dict[str, AtomDefinition]:
    """Load every valid Atom in the atoms/ tree."""
    atoms = {}
    for yaml_path in find_all_atoms(atoms_root):
        try:
            atom = load_atom(yaml_path)
            atoms[atom.id] = atom
        except AtomLoadError as e:
            print(f"[atom_loader] WARNING: Failed to load {yaml_path}: {e}")
    return atoms


if __name__ == "__main__":
    # Bootstrap so "atoms.*" namespace packages are importable when running the
    # self-test directly (required for Gold Standard Atoms and all future Atoms).
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("=== Acid Burn Atom Loader Self-Test ===\n")
    print(f"Project root added to sys.path: {project_root}\n")
    atoms = load_all_atoms()
    print(f"Discovered and loaded {len(atoms)} Atoms:\n")
    for atom_id, atom in atoms.items():
        print(f"  • {atom_id}")
        print(f"    Safety Class : {atom.safety_class}")
        print(f"    Python Package: {atom.toolchain.package_name}")
        print(f"    YAML: {atom.yaml_path}")
        print()
