"""
Push the current branch to GitHub using a Personal Access Token from .env.

The token is only ever passed as a one-time argument to `git push` — it is never
written into .git/config, so it won't leak into the repo or persist on disk.

Usage:
    python push_to_github.py
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

REQUIRED = ["GITHUB_USERNAME", "GITHUB_TOKEN"]
missing = [k for k in REQUIRED if not os.environ.get(k) or "REPLACE_WITH" in os.environ.get(k, "")]
if missing:
    print(f"[ERROR] Missing/placeholder env vars: {missing}. Fill in real values in .env "
          f"(GITHUB_TOKEN must be a Personal Access Token, not your account password).")
    sys.exit(1)

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "yedla26/visdemo-fusion-mcp"
BRANCH = subprocess.run(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()

auth_url = f"https://{USERNAME}:{TOKEN}@github.com/{REPO}.git"

print(f"Pushing branch '{BRANCH}' to {REPO} ...")
result = subprocess.run(["git", "push", auth_url, BRANCH], capture_output=True, text=True)

# Scrub the token out of anything echoed back, just in case git includes the URL in output.
scrub = lambda s: s.replace(TOKEN, "***")
print(scrub(result.stdout))
print(scrub(result.stderr))

if result.returncode == 0:
    print("[OK] Pushed successfully.")
else:
    print(f"[ERROR] git push exited with code {result.returncode}")
    sys.exit(result.returncode)
