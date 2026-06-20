"""Pluggable integrations behind clean interfaces with keyless fallback.

Pattern borrowed from Apex's ``data/`` package: a small interface per capability and a
``registry`` factory that returns a real implementation when configured, otherwise a
deterministic offline stub so the whole system runs and tests without credentials.
"""
