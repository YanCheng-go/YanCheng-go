"""Fetch live data and update README.md between marker comments."""

import json
import re
import urllib.request
from datetime import datetime, timezone


SCHOLAR_ID = "O6azk1oAAAAJ"
GITHUB_USER = "YanCheng-go"
README_PATH = "README.md"


def fetch_scholar_stats() -> dict:
    """Scrape publication count, citations, and h-index from Google Scholar."""
    url = f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
        # Citation indices table: Citations, h-index, i10-index (All / Since 5yr)
        cells = re.findall(r'<td class="gsc_rsb_std">(\d+)</td>', html)
        # cells order: [citations_all, citations_5yr, h_all, h_5yr, i10_all, i10_5yr]
        citations = int(cells[0]) if len(cells) > 0 else 0
        h_index = int(cells[2]) if len(cells) > 2 else 0
        # Count publications
        pubs = len(re.findall(r'class="gsc_a_at"', html))
        return {"publications": pubs, "citations": citations, "h_index": h_index}
    except Exception as e:
        print(f"Scholar fetch failed: {e}")
        return {}


def fetch_pinned_repos() -> list[dict]:
    """Fetch pinned/popular repos via GitHub API."""
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?sort=stars&per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "readme-updater"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            repos = json.loads(resp.read().decode("utf-8"))
        # Filter out profile repo and forks
        keep = []
        for r in repos:
            if r.get("fork") or r["name"].endswith(".github.io"):
                continue
            keep.append({
                "name": r["name"],
                "url": r["html_url"],
                "description": r.get("description") or "",
                "stars": r["stargazers_count"],
            })
        # Sort by stars descending, take top 6
        keep.sort(key=lambda x: x["stars"], reverse=True)
        return keep[:6]
    except Exception as e:
        print(f"GitHub fetch failed: {e}")
        return []


def replace_section(text: str, marker: str, content: str) -> str:
    """Replace content between <!-- MARKER:START --> and <!-- MARKER:END -->."""
    pattern = rf"(<!-- {marker}:START -->)\n.*?\n(<!-- {marker}:END -->)"
    replacement = rf"\1\n{content}\n\2"
    return re.sub(pattern, replacement, text, flags=re.DOTALL)


def main():
    with open(README_PATH) as f:
        readme = f.read()

    # Update Scholar stats
    stats = fetch_scholar_stats()
    if stats:
        scholar_table = (
            "| Publications | Citations | h-index |\n"
            "|:---:|:---:|:---:|\n"
            f"| {stats['publications']} | {stats['citations']} | {stats['h_index']} |"
        )
        readme = replace_section(readme, "SCHOLAR-STATS", scholar_table)
        print(f"Scholar: {stats['publications']} pubs, {stats['citations']} citations, h={stats['h_index']}")

    # Update pinned repos
    repos = fetch_pinned_repos()
    if repos:
        rows = ["| Project | Description | Stars |", "|---------|-------------|:-----:|"]
        for r in repos:
            stars = r["stars"] if r["stars"] > 0 else "-"
            desc = r["description"][:60] + ("..." if len(r["description"]) > 60 else "")
            rows.append(f"| [{r['name']}]({r['url']}) | {desc} | {stars} |")
        readme = replace_section(readme, "PINNED-REPOS", "\n".join(rows))
        print(f"Repos: updated {len(repos)} repos")

    # Update timestamp
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme = re.sub(
        r"(<!-- LAST-UPDATED:START -->).*?(<!-- LAST-UPDATED:END -->)",
        rf"\g<1>{now}\g<2>",
        readme,
    )

    with open(README_PATH, "w") as f:
        f.write(readme)
    print(f"README updated at {now}")


if __name__ == "__main__":
    main()
