"""M3: Query — FTS5 keyword + model/LoRA/seed 查询"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database import Database
from parser.base import Generation, LoraRef


def setup_db():
    td = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db = Database(td.name)
    db.insert(Generation(
        image_path="/a.png", prompt="cyberpunk girl rain neon",
        negative="ugly blurry", model_name="sd_xl_base",
        loras=[LoraRef(name="add_detail", weight=0.8)],
        seed=1234567890, parser_name="ComfyUI"))
    db.insert(Generation(
        image_path="/b.png", prompt="sunset landscape mountains",
        negative="low quality", model_name="flux_dev",
        loras=[LoraRef(name="character_v3", weight=1.0)],
        seed=42, parser_name="ComfyUI"))
    db.insert(Generation(
        image_path="/c.png", prompt="portrait studio lighting",
        negative="", model_name="sd_xl_base",
        seed=999, parser_name="ComfyUI"))
    return db


def test_query_by_prompt():
    db = setup_db()
    # FTS5 搜索
    r = db.query("cyberpunk")
    assert len(r) == 1, f"Expected 1, got {len(r)}"
    assert r[0].prompt == "cyberpunk girl rain neon"
    print("  query_by_prompt: PASS")


def test_query_by_model():
    db = setup_db()
    r = db.query_by_model("flux")
    assert len(r) == 1
    assert r[0].model_name == "flux_dev"
    print("  query_by_model: PASS")


def test_query_by_lora():
    db = setup_db()
    r = db.query_by_lora("character_v3")
    assert len(r) == 1
    print("  query_by_lora: PASS")


def test_query_by_seed():
    db = setup_db()
    r = db.query_by_seed(42)
    assert len(r) == 1
    print("  query_by_seed: PASS")


def test_all_return_list_of_generation():
    db = setup_db()
    for method, args in [
        (db.query, ("cyberpunk",)),
        (db.query_by_model, ("sd",)),
        (db.query_by_lora, ("add_detail",)),
        (db.query_by_seed, (1234567890,)),
    ]:
        results = method(*args)
        assert isinstance(results, list)
        assert all(isinstance(g, Generation) for g in results)
    print("  uniform_return: PASS")


if __name__ == '__main__':
    print("=== M3: Query ===\n")
    tests = [test_query_by_prompt, test_query_by_model, test_query_by_lora,
             test_query_by_seed, test_all_return_list_of_generation]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  {t.__name__}: FAIL — {e}")

    print(f"\n{'='*40}")
    print(f"M3: {'ALL PASSED' if passed == len(tests) else 'SOME FAILED'} ({passed}/{len(tests)})")
    print(f"{'='*40}")
