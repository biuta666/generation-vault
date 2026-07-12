"""M1: ComfyUIParser Golden Files 测试"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser import ComfyUIParser, Generation


def test_golden_files():
    """遍历 tests/comfyui/ 下的所有 sample_*.png 和 expected_*.json"""
    test_dir = os.path.join(os.path.dirname(__file__), 'comfyui')
    parser = ComfyUIParser()
    passed = 0
    failed = 0

    for fname in sorted(os.listdir(test_dir)):
        if not fname.startswith('sample_') or not fname.endswith('.png'):
            continue

        png_path = os.path.join(test_dir, fname)
        json_path = os.path.join(test_dir, fname.replace('.png', '.json'))

        if not os.path.exists(json_path):
            print(f"  SKIP {fname}: no expected.json")
            continue

        print(f"  Testing {fname}...")
        try:
            gen = parser.parse(png_path)
        except Exception as e:
            print(f"    FAIL: parse error - {e}")
            failed += 1
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            expected = json.load(f)

        mismatches = []
        for key in ['prompt', 'negative', 'model_name', 'seed', 'cfg', 'sampler', 'steps']:
            if key in expected:
                actual = getattr(gen, key)
                if actual != expected[key]:
                    mismatches.append(f"{key}: got={actual!r}, want={expected[key]!r}")

        # Check LoRA count
        if 'loras' in expected:
            if len(gen.loras) != len(expected['loras']):
                mismatches.append(f"lora_count: got={len(gen.loras)}, want={len(expected['loras'])}")

        if mismatches:
            print(f"    FAIL: {', '.join(mismatches)}")
            failed += 1
        else:
            print(f"    PASS")
            passed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_can_parse():
    parser = ComfyUIParser()
    # Non-png file should return False
    assert not parser.can_parse("test.txt"), "Should reject .txt"
    assert not parser.can_parse("test.jpg"), "Should reject .jpg"
    print("  can_parse: PASS")


def test_generation_dataclass():
    """测试 Generation 序列化"""
    gen = Generation(
        image_path="test.png",
        prompt="a cat",
        negative="ugly",
        model_name="sd_xl",
        seed=42,
    )
    d = gen.to_dict()
    assert d['prompt'] == 'a cat'
    assert d['seed'] == 42

    gen2 = Generation.from_dict(d)
    assert gen2.prompt == gen.prompt
    assert gen2.seed == gen.seed
    print("  dataclass: PASS")


if __name__ == '__main__':
    print("=== M1: ComfyUIParser Tests ===\n")

    print("[Unit] Generation dataclass")
    test_generation_dataclass()

    print("\n[Unit] can_parse()")
    test_can_parse()

    print("\n[Golden Files] ComfyUI samples")
    ok = test_golden_files()

    print(f"\n{'='*40}")
    print(f"M1: {'✅ ALL PASSED' if ok else '❌ SOME FAILED'}")
    print(f"{'='*40}")
