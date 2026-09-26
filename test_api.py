import requests

url = "https://api.weather.gov/points/40.7128,-74.0060"
headers = {"User-Agent": "AirGuard.AI-prototype (mostefethallah@gmail.com)"}

response = requests.get(url, headers=headers, timeout=10)

print("Status code:", response.status_code)
data = response.json()
print("Forecast office:", data["properties"]["gridId"])
