import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import (
    MemoryStore, KeyExistsError,
    SEMANTIC, EPISODIC, PROCEDURAL,
    SOURCE_SEED, SOURCE_SESSION,
)


@pytest.fixture
def store(tmp_path):
    s = MemoryStore(tmp_path / "test.db")
    yield s
    s.close()


# ── store() ───────────────────────────────────────────────────────────────────

def test_store_new_key(store):
    store.store(SEMANTIC, "k1", "Barge uses containerd")
    assert store.exists("k1")


def test_store_raises_if_key_exists(store):
    store.store(SEMANTIC, "k1", "original")
    with pytest.raises(KeyExistsError, match="k1"):
        store.store(SEMANTIC, "k1", "duplicate")


def test_store_invalid_category(store):
    with pytest.raises(ValueError, match="category must be one of"):
        store.store("invalid", "k1", "content")


def test_store_invalid_source(store):
    with pytest.raises(ValueError, match="source must be one of"):
        store.store(SEMANTIC, "k1", "content", source="unknown")


def test_store_invalid_importance(store):
    with pytest.raises(ValueError, match="importance must be between"):
        store.store(SEMANTIC, "k1", "content", importance=6)


# ── exists() and get() ────────────────────────────────────────────────────────

def test_exists_true(store):
    store.store(SEMANTIC, "k1", "content")
    assert store.exists("k1") is True


def test_exists_false(store):
    assert store.exists("nonexistent") is False


def test_get_returns_memory(store):
    store.store(SEMANTIC, "k1", "content", source=SOURCE_SEED, importance=4)
    m = store.get("k1")
    assert m is not None
    assert m.key == "k1"
    assert m.category == SEMANTIC
    assert m.importance == 4


def test_get_returns_none_if_missing(store):
    assert store.get("nonexistent") is None


# ── overwrite() ───────────────────────────────────────────────────────────────

def test_overwrite_replaces_content(store):
    store.store(SEMANTIC, "k1", "original content")
    store.overwrite("k1", "new content")
    assert store.get("k1").content == "new content"


def test_overwrite_updates_importance(store):
    store.store(SEMANTIC, "k1", "content", importance=3)
    store.overwrite("k1", "content", importance=5)
    assert store.get("k1").importance == 5


def test_overwrite_keeps_importance_if_not_provided(store):
    store.store(SEMANTIC, "k1", "content", importance=4)
    store.overwrite("k1", "new content")
    assert store.get("k1").importance == 4


def test_overwrite_raises_if_key_missing(store):
    with pytest.raises(KeyError, match="k1"):
        store.overwrite("k1", "content")


# ── append() ─────────────────────────────────────────────────────────────────

def test_append_adds_content(store):
    store.store(SEMANTIC, "k1", "original")
    store.append("k1", "addition")
    content = store.get("k1").content
    assert "original" in content
    assert "addition" in content
    assert "---" in content


def test_append_raises_if_key_missing(store):
    with pytest.raises(KeyError, match="k1"):
        store.append("k1", "content")


# ── search() ─────────────────────────────────────────────────────────────────

def test_search_finds_match(store):
    store.store(SEMANTIC, "k1", "Barge uses containerd for Windows containers")
    results = store.search("containerd Windows")
    assert len(results) == 1
    assert results[0].key == "k1"


def test_search_no_match(store):
    assert store.search("completely unrelated xyz123") == []


def test_search_category_filter(store):
    store.store(SEMANTIC, "s1", "barge networking uses HCN")
    store.store(EPISODIC, "e1", "barge networking bug was fixed")
    semantic = store.search("barge networking", category=SEMANTIC)
    assert all(r.category == SEMANTIC for r in semantic)
    episodic = store.search("barge networking", category=EPISODIC)
    assert all(r.category == EPISODIC for r in episodic)


def test_search_top_k(store):
    for i in range(10):
        store.store(SEMANTIC, f"key_{i}", f"barge windows container fact {i}")
    results = store.search("barge windows container", top_k=3)
    assert len(results) <= 3


# ── all() ─────────────────────────────────────────────────────────────────────

def test_all_returns_everything(store):
    store.store(SEMANTIC, "s1", "fact")
    store.store(EPISODIC, "e1", "past fix")
    store.store(PROCEDURAL, "p1", "always test")
    assert len(store.all()) == 3


def test_all_category_filter(store):
    store.store(SEMANTIC, "s1", "fact one")
    store.store(SEMANTIC, "s2", "fact two")
    store.store(EPISODIC, "e1", "past session")
    results = store.all(category=SEMANTIC)
    assert len(results) == 2
    assert all(r.category == SEMANTIC for r in results)


# ── delete() ─────────────────────────────────────────────────────────────────

def test_delete_removes_key(store):
    store.store(EPISODIC, "bug_001", "fixed null pointer")
    store.delete("bug_001")
    assert store.exists("bug_001") is False


def test_delete_silent_if_missing(store):
    store.delete("nonexistent")  # should not raise
