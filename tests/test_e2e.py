"""M4: End-to-End test — PNG → Import → DB → Search → Detail"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import ComfyUIParser
from core.database import Database


def test_e2e():
    """sample_001.png → Import → DB → Search → Detail"""
    sample = os.path.join(
        os.path.dirname(__file__), 'comfyui', 'sample_001.png')
    td = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = td.name; td.close()

    try:
        db = Database(db_path)
        parser = ComfyUIParser()

        # Import
        gen = parser.parse(sample)
        gen_id = db.insert(gen)
        assert gen_id == 1

        # Search by prompt
        results = db.query("cyberpunk")
        assert len(results) == 1
        assert results[0].prompt == "a cyberpunk girl in rain, neon lights, 8k"

        # Search by model
        results = db.query_by_model("sd_xl")
        assert len(results) == 1

        # Search by seed
        results = db.query_by_seed(1234567890)
        assert len(results) == 1

        # Detail
        detail = db.get(gen_id)
        assert detail.seed == 1234567890
        assert detail.parser_name == "ComfyUI"

        print("  E2E: PASS")
        db.close()
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    print("=== M4: E2E Test ===\n")
    try:
        test_e2e()
        print(f"\n{'='*40}")
        print("M4: ALL PASSED")
        print(f"{'='*40}")
    except Exception as e:
        print(f"\nM4: FAIL — {e}")
