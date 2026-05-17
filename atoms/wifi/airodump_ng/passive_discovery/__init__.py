"""
wifi.airodump_ng.passive_discovery

Gold Standard Reference Atom for passive 802.11 discovery using airodump-ng.

This package contains the deterministic Python toolchain that backs the Atom.

Usage:
    from atoms.wifi.airodump_ng.passive_discovery import command_builder, output_parser

    cmd = command_builder.build_command({...})
    result = output_parser.parse_output(csv_path="...")   # or raw_text="..."
"""

from . import command_builder, output_parser

__all__ = ["command_builder", "output_parser"]
__version__ = "0.9.0"
