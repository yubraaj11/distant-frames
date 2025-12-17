import sys
import os
print(f"CWD: {os.getcwd()}")
sys.path.insert(0, os.path.abspath("src"))
try:
    import distant_frames
    print(f"Imported from: {distant_frames.__file__}")
except ImportError as e:
    print(f"Import failed: {e}")
