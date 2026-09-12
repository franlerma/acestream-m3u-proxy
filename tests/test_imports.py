"""Ensure every application module imports cleanly."""

import importlib

import pytest

MODULES = [
    "acestream_proxy.models",
    "acestream_proxy.service",
    "acestream_proxy.cache",
    "acestream_proxy.config",
    "acestream_proxy.router",
    "acestream_proxy.main",
]


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name: str) -> None:
    assert importlib.import_module(f"src.{module_name}") is not None
