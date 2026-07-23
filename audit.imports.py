import importlib
import pathlib
import traceback

ROOT = pathlib.Path(".")

errors = []

for py in ROOT.rglob("*.py"):
    if "venv" in py.parts or "__pycache__" in py.parts:
        continue

    module = ".".join(py.with_suffix("").parts)

    try:
        importlib.import_module(module)
        print(f"✅ {module}")
    except Exception as e:
        errors.append((module, e))
        print(f"\n❌ {module}")
        traceback.print_exc()

print("\n" + "=" * 70)
print(f"TOTAL ERRORS: {len(errors)}")
print("=" * 70)

for module, err in errors:
    print(f"{module} -> {type(err).__name__}: {err}")