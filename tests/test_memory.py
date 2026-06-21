import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryStore


@pytest.fixture
def store(tmp_path):
    s = MemoryStore(tmp_path / "test.db")
    yield s
    s.close()


def test_store_and_search(store):
    store.store("semantic", "k1", "Barge uses containerd for Windows containers")
    results = store.search("containerd Windows")
    assert len(results) == 1
    assert results[0].key == "k1"
    assert results[0].category == "semantic"


def test_search_no_match(store):
    results = store.search("completely unrelated xyz123")
    assert results == []


def test_upsert(store):
    store.store("semantic", "k1", "original content")
    store.store("semantic", "k1", "updated content")
    results = store.search("updated")
    assert len(results) == 1
    assert "updated" in results[0].content


def test_delete(store):
    store.store("episodic", "bug_001", "fixed null pointer in auth")
    store.delete("bug_001")
    assert store.search("null pointer") == []


def test_all_categories(store):
    store.store("semantic", "s1", "code conventions")
    store.store("episodic", "e1", "past bug fix")
    store.store("procedural", "p1", "always run go test")
    assert len(store.all()) == 3


def test_top_k(store):
    for i in range(10):
        store.store("semantic", f"key_{i}", f"barge windows container fact {i}")
    results = store.search("barge windows container", top_k=3)
    assert len(results) <= 3
