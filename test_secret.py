import os

key = os.environ.get("AIRNOW_API_KEY")

if key:
    print("Key found, length:", len(key))
else:
    print("Key NOT found")
