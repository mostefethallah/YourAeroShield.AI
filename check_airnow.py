import os, requests, json

r = requests.get(
    "https://www.airnowapi.org/aq/observation/current/ziplatlong/",
    params={"format": "application/json", "zipCode": "10001",
            "API_KEY": os.environ["AIRNOW_API_KEY"]},
    timeout=10,
)
print("Status:", r.status_code)
print("URL:", r.url.replace(os.environ["AIRNOW_API_KEY"], "KEY"))
print(r.text[:2000])

