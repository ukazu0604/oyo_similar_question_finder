from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("Starting Selenium check...")
try:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    print("Initializing driver with webdriver_manager...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Driver initialized.")
    
    driver.get("http://localhost:8000")
    print(f"Title: {driver.title}")
    
    driver.quit()
    print("Selenium check passed.")
except Exception as e:
    print(f"Selenium check failed: {e}")
