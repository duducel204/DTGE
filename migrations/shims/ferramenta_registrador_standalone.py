# shim for legacy module ferramenta_registrador_standalone.py
import importlib.util, os
ROOT = os.getcwd()
MOD_FILE = os.path.join(ROOT, "src", "dtge", "registrador.py")
if not os.path.exists(MOD_FILE):
    raise ImportError(f"Expected migrated module at {MOD_FILE}; run this shim after migration or ensure module moved.")
spec = importlib.util.spec_from_file_location("dtge_registrador", MOD_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
__all__ = [n for n in dir(mod) if not n.startswith("_")]
for n in __all__:
    globals()[n] = getattr(mod, n)

if __name__ == "__main__":
    if hasattr(mod, "main"):
        mod.main()
