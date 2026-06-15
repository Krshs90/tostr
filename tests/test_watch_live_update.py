"""Integration tests for the live watcher / incremental tree updates.

These exercise the real path the MCP server uses: when a file is saved, the
background watcher must reparse it and update the cached tree in the SQLite DB.

They are hermetic: `get_llm_client` is forced into no-LLM mode so no API key or
network call is required. Embeddings use the locally-cached ONNX model.
"""
from __future__ import annotations
import asyncio
import shutil
import sqlite3
from pathlib import Path

import pytest

import tostr.commands as commands
from tostr.commands import init_async, process_single_file, watch_async
from tostr.exceptions import APIKeyError

# Whole module is integration: it runs a real init (downloads/loads the embedding
# model) and a live file watcher. CI runs `pytest -m "not integration"` to skip these.
pytestmark = pytest.mark.integration

TEST_PROJECT = Path(__file__).parent / "testcode" / "PythonTestProject"

NEW_METHOD = (
    "\n\n    def promo_special(self) -> float:\n"
    "        return self.apply_discount(0.5)"
)
ANCHOR = "        return self.price * (1 - rate)"


@pytest.fixture
def no_llm(monkeypatch):
    """Force the watcher into no-LLM mode regardless of the ambient GEMINI_API_KEY."""
    def _raise(*args, **kwargs):
        raise APIKeyError("no key (test)")
    monkeypatch.setattr(commands, "get_llm_client", _raise)


@pytest.fixture
def project(tmp_path):
    """A fresh, initialized copy of the Python test project."""
    proj = tmp_path / "proj"
    shutil.copytree(TEST_PROJECT, proj)
    return proj


def method_uids(proj: Path) -> list[str]:
    con = sqlite3.connect(proj / ".tostr" / "cache.db")
    try:
        return [r[0] for r in con.execute("SELECT uid FROM structs WHERE type='method'")]
    finally:
        con.close()


def add_method(proj: Path) -> None:
    models = proj / "models.py"
    models.write_text(models.read_text().replace(ANCHOR, ANCHOR + NEW_METHOD))


async def test_process_single_file_updates_tree(no_llm, project):
    """A modified file is reparsed and the new struct lands in the cached tree."""
    await init_async(project, no_llm=True)

    before = method_uids(project)
    assert any("apply_discount" in m for m in before)
    assert not any("promo_special" in m for m in before)

    add_method(project)
    # The watcher always hands process_single_file an absolute path.
    await process_single_file(project, (project / "models.py").resolve(), None)

    after = method_uids(project)
    assert any("promo_special" in m for m in after), "new method was not added to the tree"
    # Existing structs are retained and not duplicated.
    assert sum("apply_discount" in m for m in after) == 1
    assert len(after) == len(set(after)), "duplicate structs written on update"


async def test_watcher_live_updates_on_modification(no_llm, project):
    """End-to-end: the running watcher detects a save and updates the DB itself."""
    await init_async(project, no_llm=True)
    assert not any("promo_special" in m for m in method_uids(project))

    stop_event = asyncio.Event()
    watch_task = asyncio.create_task(watch_async(project, stop_event=stop_event))
    try:
        await asyncio.sleep(1.0)  # let awatch initialize before we touch the file
        add_method(project)

        updated = False
        for _ in range(50):  # poll up to ~15s
            await asyncio.sleep(0.3)
            if any("promo_special" in m for m in method_uids(project)):
                updated = True
                break
        assert updated, "watcher did not live-update the tree after a file modification"
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(watch_task, timeout=5)
        except asyncio.TimeoutError:
            watch_task.cancel()
