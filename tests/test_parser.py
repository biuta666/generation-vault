"""M1: ComfyUIParser — Unit + Golden Files + Capability Tests"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import ComfyUIParser, Generation

TEST_DIR = os.path.join(os.path.dirname(__file__), 'comfyui')


def test_dataclass():
    gen = Generation(image_path="test.png", prompt="cat", seed=42)
    d = gen.to_dict()
    assert d['prompt'] == 'cat'
    gen2 = Generation.from_dict(d)
    assert gen2.prompt == gen.prompt and gen2.seed == gen.seed
    return True


def test_capability():
    parser = ComfyUIParser()
    # 应该识别 ComfyUI PNG
    assert parser.can_parse(os.path.join(TEST_DIR, 'sample_001.png')) == True, "Should detect ComfyUI PNG"
    # 不应识别普通 PNG
    assert parser.can_parse(os.path.join(TEST_DIR, 'normal.png')) == False, "Should reject normal PNG"
    # 不应识别非 PNG
    assert parser.can_parse("test.txt") == False, "Should reject .txt"
    assert parser.can_parse("test.jpg") == False, "Should reject .jpg"
    return True


def test_golden_files():
    parser = ComfyUIParser()
    passed = 0
    for fname in sorted(os.listdir(TEST_DIR)):
        if not fname.startswith('sample_') or not fname.endswith('.png'):
            continue
        png_path = os.path.join(TEST_DIR, fname)
        json_path = png_path.replace('.png', '.json')
        if not os.path.exists(json_path):
            continue

        gen = parser.parse(png_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        for key in ['prompt', 'negative', 'model_name', 'seed', 'cfg', 'sampler', 'steps', 'parser_name']:
            if key in expected:
                actual = getattr(gen, key)
                assert actual == expected[key], f"{fname}: {key} mismatch: {actual!r} != {expected[key]!r}"

        if 'loras' in expected:
            assert len(gen.loras) == len(expected['loras']), f"{fname}: Lora count mismatch"

        passed += 1
    return passed >= 1


if __name__ == '__main__':
    print("=== M1: ComfyUIParser ===\n")

    results = []
    for name, test in [("dataclass", test_dataclass), ("capability", test_capability), ("golden_files", test_golden_files)]:
        try:
            ok = test()
            print(f"  [{name}] {'PASS' if ok else 'FAIL'}")
            results.append(ok)
        except Exception as e:
            print(f"  [{name}] FAIL: {e}")
            results.append(False)

    all_pass = all(results)
    print(f"\n{'='*40}")
    print(f"M1: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
    print(f"{'='*40}")
