import os

CONFIG_FILE = ".test_settings.local"
GITIGNORE_FILE = ".gitignore"

TEMPLATE = """# .test_settings.local
# This file is ignored by git.
# Configure your local test environment here.

# Set to True to run tests in headless mode (no browser window)
HEADLESS_MODE = False

# GAS Web App URL for testing
# IMPORTANT: Use a separate deployment for testing, not production!
TEST_GAS_URL = ""

# Base URL for the local server
BASE_URL = "http://localhost:8000"
"""

def create_config():
    if os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} already exists. Skipping creation.")
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(TEMPLATE)
        print(f"Created {CONFIG_FILE}. Please edit it with your settings.")

def update_gitignore():
    if not os.path.exists(GITIGNORE_FILE):
        print(f"{GITIGNORE_FILE} not found. Creating one.")
        with open(GITIGNORE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{CONFIG_FILE}\n")
        print(f"Added {CONFIG_FILE} to {GITIGNORE_FILE}.")
        return

    with open(GITIGNORE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if any(CONFIG_FILE in line for line in lines):
        print(f"{CONFIG_FILE} is already in {GITIGNORE_FILE}.")
    else:
        with open(GITIGNORE_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n{CONFIG_FILE}\n")
        print(f"Added {CONFIG_FILE} to {GITIGNORE_FILE}.")

if __name__ == "__main__":
    create_config()
    update_gitignore()
