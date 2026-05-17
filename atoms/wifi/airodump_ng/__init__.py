"""
airodump-ng Atom Package — Acid Burn

This package contains the deterministic Python toolchain for the
wifi.airodump_ng Atom.

It is designed to be imported as:
    from atoms.wifi.airodump_ng.command_builder import build_command
    from atoms.wifi.airodump_ng.output_parser import parse_csv_output
"""

from . import command_builder, output_parser

__all__ = ["command_builder", "output_parser"]
__version__ = "0.1.0"
