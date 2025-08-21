import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import json
import tempfile
import pytest
from memory import get_history, append_brief, clear_conversation, list_conversations
from schemas import ResearchBrief


@pytest.fixture(autouse=True)
def temp_mem_dir(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setenv("RA_MEM_DIR", tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    yield tmpdir


def test_append_and_get_history(temp_mem_dir):
    brief = ResearchBrief(topic="Test Topic", summary="Test Summary", references=[])
    append_brief("test_conv", brief)

    history = get_history("test_conv")
    assert len(history) == 1
    assert history[0].topic == "Test Topic"


def test_get_history_empty(temp_mem_dir):
    history = get_history("unknown_conv")
    assert history == []


def test_clear_conversation(temp_mem_dir):
    brief = ResearchBrief(topic="Topic", summary="Summary", references=[])
    append_brief("conv1", brief)
    assert list_conversations() == ["conv1"]
    clear_conversation("conv1")
    assert list_conversations() == []

