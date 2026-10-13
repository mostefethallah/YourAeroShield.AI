from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/")
def home():
    return {"status": "YourAeroShield API is running"}

@app.get("/collect")
def collect():
    result1 = subprocess.run(["python3", "collect_and_store.py"], capture_output=True, text=True)
    result2 = subprocess.run(["python3", "simulate_indoor.py"], capture_output=True, text=True)
    return {
        "outdoor": result1.stdout.strip() or result1.stderr.strip(),
        "indoor": result2.stdout.strip() or result2.stderr.strip(),
    }
