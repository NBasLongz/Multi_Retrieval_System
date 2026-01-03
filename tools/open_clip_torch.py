"""
Compatibility shim so code that does `import open_clip_torch` still works.
This project uses the `open_clip` module (installed from `open_clip_torch` PyPI package),
but some checks try to import `open_clip_torch` by name. Expose the `open_clip` symbols
through this module so `__import__('open_clip_torch')` succeeds.
"""
import importlib

open_clip = importlib.import_module("open_clip")

# expose common attributes
__all__ = getattr(open_clip, "__all__", [])
__version__ = getattr(open_clip, "__version__", None)

# re-export everything from open_clip for convenience
from open_clip import *  # noqa: F401,F403
