"""
components package initializer for SCOM project.

This file makes the local `components` directory a regular package so
that Python imports prefer the project-local modules over any
installed package named `components` in site-packages.

Keep this file minimal — it only exposes the package and helps
relative imports work reliably.
"""

__all__ = []
