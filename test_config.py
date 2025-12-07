import os
import sys

# Default settings
HEADLESS_MODE = True
TEST_GAS_URL = ""
BASE_URL = "http://localhost:8000"

# Try to load local settings
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("local_settings", ".test_settings.local")
    if spec and spec.loader:
        local_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(local_settings)
        
        if hasattr(local_settings, "HEADLESS_MODE"):
            HEADLESS_MODE = local_settings.HEADLESS_MODE
        if hasattr(local_settings, "TEST_GAS_URL"):
            TEST_GAS_URL = local_settings.TEST_GAS_URL
        if hasattr(local_settings, "BASE_URL"):
            BASE_URL = local_settings.BASE_URL
            
except Exception as e:
    print(f"Note: Could not load .test_settings.local: {e}")
    print("Using default settings.")

# Environment variables override everything
if "HEADLESS_MODE" in os.environ:
    HEADLESS_MODE = os.environ["HEADLESS_MODE"].lower() == "true"
if "TEST_GAS_URL" in os.environ:
    TEST_GAS_URL = os.environ["TEST_GAS_URL"]
if "BASE_URL" in os.environ:
    BASE_URL = os.environ["BASE_URL"]
