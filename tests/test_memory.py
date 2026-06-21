import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryStore, SEMANTIC, EPISODIC, PROCEDURAL, SOURCE_SEED, SOURCE_SESSION


@pytest.fixture
def store(tmp_path):
    s = MemoryStore(tmp_path / "test.db")
    yield s
    s.close()


def test_store_and_search(store):
    store.store(SEMANTIC, "k1", "Barge uses containerd for Windows containers")
    results = store.search("containerd Windows")
    assert len(results) == 1
    assert results[0].key == "k1"
    assert results[0].category == SEMANTIC
    assert results[0].source == SOURCE_SEED
    assert results[0].importance == 3


def test_search_no_match(store):
    assert store.search("completely unrelated xyz123") == []


def test_upsert(store):
    store.store(SEMANTIC, "k1", "original content")
    store.store(SEMANTIC, "k1", "updated content")
    results = store.search("updated")
    assert len(results) == 1
    assert "updated" in results[0].content


def test_delete(store):
    store.store(EPISODIC, "bug_001", "fixed null pointer in auth")
    store.delete("bug_001")
    assert store.search("null pointer") == []


def test_category_filter(store):
    store.store(SEMANTIC, "s1", "barge networking uses HCN")
    store.store(EPISODIC, "e1", "barge networking bug was fixed")
    semantic_results = store.search("barge networking", category=SEMANTIC)
    assert all(r.category == SEMANTIC for r in semantic_results)
    episodic_results = store.search("barge networking", category=EPISODIC)
    assert all(r.category == EPISODIC for r in episodic_results)


def test_all_returns_all(store):
    store.store(SEMANTIC, "s1", "code conventions")
    store.store(EPISODIC, "e1", "past bug fix")
    store.store(PROCEDURAL, "p1", "always run go test")
    assert len(store.all()) == 3


def test_all_category_filter(store):
    store.store(SEMANTIC, "s1", "fact one")
    store.store(SEMANTIC, "s2", "fact two")
    store.store(EPISODIC, "e1", "past session")
    results = store.all(category=SEMANTIC)
    assert len(results) == 2
    assert all(r.category == SEMANTIC for r in results)


def test_importance_stored(store):
    store.store(SEMANTIC, "k1", "high importance fact", importance=5)
    results = store.all()
    assert results[0].importance == 5


def test_source_stored(store):
    store.store(EPISODIC, "e1", "learned in session", source=SOURCE_SESSION)
    results = store.all()
    assert results[0].source == SOURCE_SESSION


def test_invalid_category_raises(store):
    with pytest.raises(ValueError, match="category must be one of"):
        store.store("invalid_cat", "k1", "content")


def test_invalid_source_raises(store):
    with pytest.raises(ValueError, match="source must be one of"):
        store.store(SEMANTIC, "k1", "content", source="unknown")


def test_invalid_importance_raises(store):
    with pytest.raises(ValueError, match="importance must be between"):
        store.store(SEMANTIC, "k1", "content", importance=6)


def test_top_k(store):
    for i in range(10):
        store.store(SEMANTIC, f"key_{i}", f"barge windows container fact {i}")
    results = store.search("barge windows container", top_k=3)
    assert len(results) <= 3
