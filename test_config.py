import os
import sys

# Default settings
HEADLESS_MODE = False
TEST_GAS_URL = ""
BASE_URL = "http://localhost:8000"

# Try to load local settings
local_settings_path = os.path.join(os.path.dirname(__file__), ".test_settings.local")
try:
    with open(local_settings_path, 'r', encoding='utf-8') as f:
        local_config_content = f.read()
    
    # Execute the content within the current module's namespace
    # This will set HEADLESS_MODE, TEST_GAS_URL, BASE_URL if defined in the local file
    exec(local_config_content, globals())
    
    print(f"Loaded .test_settings.local successfully from: {local_settings_path}")
    print(f"HEADLESS_MODE after local settings: {HEADLESS_MODE}")
    print(f"TEST_GAS_URL after local settings: {TEST_GAS_URL}")
    print(f"BASE_URL after local settings: {BASE_URL}")

except FileNotFoundError:
    print(f"Note: .test_settings.local not found at {local_settings_path}. Using default settings.")
except Exception as e:
    print(f"Note: Could not load or parse .test_settings.local: {e}")
    print("Using default settings.")

# Environment variables override everything
if "HEADLESS_MODE" in os.environ:
    HEADLESS_MODE = os.environ["HEADLESS_MODE"].lower() == "true"
if "TEST_GAS_URL" in os.environ:
    TEST_GAS_URL = os.environ["TEST_GAS_URL"]
if "BASE_URL" in os.environ:
    BASE_URL = os.environ["BASE_URL"]

# Print final effective settings for debugging
print(f"DEBUG: Final HEADLESS_MODE: {HEADLESS_MODE}")
print(f"DEBUG: Final TEST_GAS_URL: {TEST_GAS_URL}")
print(f"DEBUG: Final BASE_URL: {BASE_URL}")
