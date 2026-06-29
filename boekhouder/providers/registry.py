"""Provider factory — pick a real implementation when configured, else a keyless stub.

Same idea as ``apex/data/registry.py``: one place that decides which concrete provider
backs each capability, based on settings and optional dependencies.
"""
from __future__ import annotations

import importlib.util
from functools import lru_cache

from boekhouder.config import get_settings
from boekhouder.providers.bank_import import FileBankImporter
from boekhouder.providers.base import BankImporter, BookkeepingProvider, OcrProvider
from boekhouder.providers.moneybird import MoneybirdProvider
from boekhouder.providers.obsidian import ObsidianVault
from boekhouder.providers.ocr_tesseract import StubOcr, TesseractOcr


def _tesseract_available() -> bool:
    return importlib.util.find_spec("pytesseract") is not None


@lru_cache
def get_ocr() -> OcrProvider:
    choice = get_settings().ocr_provider.lower()
    if choice == "stub":
        return StubOcr()
    if choice == "tesseract" or (choice == "auto" and _tesseract_available()):
        return TesseractOcr()
    return StubOcr()


@lru_cache
def get_bank_importer() -> BankImporter:
    return FileBankImporter()


@lru_cache
def get_bookkeeping() -> BookkeepingProvider:
    return MoneybirdProvider()


@lru_cache
def get_obsidian() -> ObsidianVault:
    return ObsidianVault()
