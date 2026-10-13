import os
for name in ["DATABASE_URL", "NEON_DATABASE_URL"]:
    url = os.environ.get(name)
    host = url.split("@")[1].split("/")[0] if url and "@" in url else url
    print(name, "->", host)
