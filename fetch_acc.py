# Copyright 2026 MV2 of Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Setup step of job acc02: download published files of munimtechnologies/ac-discovery (saved under
their base name), waiting (up to 40 minutes) for a file that is not committed yet.

Usage: python fetch_acc.py PATH [PATH ...]     e.g. acc01.py
"""
import os
import sys
import time
import urllib.request

BASE = "https://raw.githubusercontent.com/munimtechnologies/ac-discovery/main/"

for path in sys.argv[1:]:
    name = os.path.basename(path)
    for attempt in range(40):
        try:
            urllib.request.urlretrieve(BASE + path, name)
            print(f"{path}: downloaded", flush=True)
            break
        except Exception as e:
            print(f"{path}: attempt {attempt + 1} failed ({e}); waiting 60 s", flush=True)
            time.sleep(60)
    else:
        sys.exit(f"could not download {path}")
