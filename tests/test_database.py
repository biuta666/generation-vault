"""M2: Database — Round-trip test: Generation → SQLite → Generation"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.database import Database
from parser.base import Generation, LoraRef


def test_roundtrip():
    """Generation → SQLite → Generation 闭环"""
    gen_in = Generation(
        image_path="C:/images/test.png",
        prompt="a cyberpunk cat, neon lights, masterpiece",
        negative="ugly, blurry",
        model_name="sd_xl_base_1.0",
        model_hash="abc123",
        loras=[LoraRef(name="add_detail", weight=0.8)],
        seed=1234567890,
        cfg=7.5,
        sampler="euler",
        steps=30,
        width=1024,
        height=1024,
        workflow_json='{"nodes":[]}',
        source_tool="ComfyUI",
        parser_name="ComfyUI",
    )

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name

    try:
        db = Database(db_path)

        # Insert
        gen_id = db.insert(gen_in)
        assert gen_id == 1, f"Expected id=1, got {gen_id}"

        # Read back
        gen_out = db.get(gen_id)
        assert gen_out is not None, "get() returned None"

        # Compare every field
        for field in ['prompt', 'negative', 'model_name', 'seed', 'cfg', 'sampler',
                       'steps', 'width', 'height', 'source_tool', 'parser_name']:
            actual = getattr(gen_out, field)
            expected = getattr(gen_in, field)
            assert actual == expected, f"{field}: {actual!r} != {expected!r}"

        # LoRA
        assert len(gen_out.loras) == 1, f"Lora count: {len(gen_out.loras)}"
        assert gen_out.loras[0].name == "add_detail"
        assert gen_out.loras[0].weight == 0.8

        # Count
        assert db.count() == 1, f"Count: {db.count()}"
        print("  roundtrip: PASS")
        db.close()
    finally:
        os.unlink(db_path)


def test_multiple():
    """多条记录"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name

    try:
        db = Database(db_path)
        for i in range(5):
            db.insert(Generation(image_path=f"img_{i}.png", prompt=f"test_{i}", seed=i))
        assert db.count() == 5

        all_gen = db.get_all()
        assert len(all_gen) == 5
        print("  multiple: PASS")
        db.close()
    finally:
        os.unlink(db_path)


def test_schema_version():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tf:
        db_path = tf.name
    try:
        db = Database(db_path)
        row = db.conn.execute("SELECT value FROM _meta WHERE key='schema_version'").fetchone()
        assert row['value'] == '1'
        print("  schema_version: PASS")
        db.close()
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    print("=== M2: Database ===\n")
    tests = [test_roundtrip, test_multiple, test_schema_version]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  {t.__name__}: FAIL — {e}")

    print(f"\n{'='*40}")
    print(f"M2: {'ALL PASSED' if passed == len(tests) else 'SOME FAILED'} ({passed}/{len(tests)})")
    print(f"{'='*40}")
