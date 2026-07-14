import subprocess, json, sys, os, shutil
from collections import Counter

# Local dev uses the full Windows path; CI (GitHub Actions) has `gh` on PATH.
_WIN_GH = r"C:\Program Files\GitHub CLI\gh.exe"
GH = _WIN_GH if os.path.exists(_WIN_GH) else (shutil.which("gh") or "gh")

# Allow overriding the account so this isn't hardcoded to one user.
USER = os.environ.get("GH_USER", "danielrltan")

def gh(*args):
    p = subprocess.run([GH] + list(args), capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise RuntimeError(f"gh error on {args}: {p.stderr}")
    return p.stdout

print("listing repos...", flush=True)
repos = json.loads(gh("repo", "list", USER, "--limit", "1000",
                      "--json", "name,stargazerCount,isPrivate,isFork,isArchived"))
print(f"  total: {len(repos)}", flush=True)

# Skip forks (language stats reflect upstream code, not Daniel's)
own = [r for r in repos if not r["isFork"]]
print(f"  non-fork: {len(own)}", flush=True)

lang_bytes = Counter()
for r in own:
    name = r["name"]
    try:
        langs = json.loads(gh("api", f"/repos/{USER}/{name}/languages"))
        for lang, b in langs.items():
            lang_bytes[lang] += b
    except Exception as e:
        print(f"  skip {name}: {e}", flush=True)

total = sum(lang_bytes.values()) or 1
top = lang_bytes.most_common(15)

print("\nlanguages:")
for lang, b in top:
    print(f"  {lang:15} {b:>12,}  ({b/total*100:5.1f}%)")

user = json.loads(gh("api", "/user"))

# Safety net for CI: if the token authenticates as someone other than USER
# (e.g. the default github-actions[bot] token), the numbers below would be
# wrong. Bail out so the caller keeps the last-good committed stats.json.
if user.get("login", "").lower() != USER.lower():
    sys.exit(f"authenticated as '{user.get('login')}', expected '{USER}' "
             f"— set the STATS_TOKEN secret to a PAT for {USER}. Keeping existing stats.")

total_stars = sum(r["stargazerCount"] for r in repos)

# Commits in last year via GraphQL
gql = """
query {
  viewer {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
    }
  }
}
"""
cc = json.loads(gh("api", "graphql", "-f", f"query={gql}"))["data"]["viewer"]["contributionsCollection"]

out = {
    "languages_top": top,
    "languages_total_bytes": total,
    "followers": user["followers"],
    "following": user["following"],
    "public_repos": user["public_repos"],
    "total_repos": len(repos),
    "non_fork_repos": len(own),
    "stars": total_stars,
    "commits_last_year": cc["totalCommitContributions"],
    "prs_last_year": cc["totalPullRequestContributions"],
    "issues_last_year": cc["totalIssueContributions"],
    "private_contribs_last_year": cc["restrictedContributionsCount"],
}
with open("stats.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\nwrote stats.json")
print(json.dumps(out, indent=2))
