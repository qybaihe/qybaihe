import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_PATH = os.path.join(ROOT, "assets", "banner.svg")
README_PATH = os.path.join(ROOT, "README.md")


def fetch_json(url, headers=None):
    req_headers = {"User-Agent": "qybaihe-profile-updater"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_all_own_repos(username="qybaihe"):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    repos = []
    page = 1
    while True:
        batch = fetch_json(
            f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&type=owner",
            headers=headers,
        )
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if not r.get("fork")]


def format_compact(n):
    if n >= 1000:
        return f"{(n // 100) / 10:.1f}K+"
    return str(n)


def replace_tag(text, key, new_val):
    pattern = rf"(<!--stat:{re.escape(key)}-->).*?(<!--/stat:{re.escape(key)}-->)"
    return re.sub(pattern, rf"\g<1>{new_val}\g<2>", text, flags=re.S)


def main():
    repos = fetch_all_own_repos("qybaihe")
    total_stars = sum(r["stargazers_count"] for r in repos)
    total_forks = sum(r["forks_count"] for r in repos)
    total_repos = len(repos)

    by_name = {r["name"]: r for r in repos}
    bla_stars = by_name.get("bla", {}).get("stargazers_count", 0)
    mu_stars = by_name.get("mu", {}).get("stargazers_count", 0)
    codex_ppt_stars = by_name.get("codex-ppt", {}).get("stargazers_count", 0)
    sysu_stars = by_name.get("SYSU-Anything", {}).get("stargazers_count", 0)

    npm_label = None
    try:
        npm_data = fetch_json("https://api.npmjs.org/downloads/range/2026-10-25:2030-12-31/bla-agents")
        total_dl = sum(d["downloads"] for d in npm_data.get("downloads", []))
        if total_dl > 0:
            npm_label = format_compact(total_dl)
    except Exception as exc:
        print(f"Skipping npm update due to fetch error: {exc}")

    svg = open(SVG_PATH, "r", encoding="utf-8").read()
    svg = replace_tag(svg, "total_stars", f"{total_stars:,}")
    svg = replace_tag(svg, "total_forks", f"{total_forks:,}")
    svg = replace_tag(svg, "total_repos", str(total_repos))
    if bla_stars:
        svg = replace_tag(svg, "bla_stars", f"{bla_stars:,}")
    if mu_stars:
        svg = replace_tag(svg, "mu_stars", f"{mu_stars:,}")
    if npm_label:
        svg = replace_tag(svg, "npm_dl", npm_label)
    open(SVG_PATH, "w", encoding="utf-8").write(svg)

    readme = open(README_PATH, "r", encoding="utf-8").read()
    if bla_stars:
        readme = re.sub(
            r"(\*\*\[BLA — Blind LLM Agents\]\(https://github\.com/qybaihe/bla\)\*\* \(`)[^`]+( ★`)",
            rf"\g<1>{bla_stars:,}\g<2>",
            readme,
        )
    if mu_stars:
        readme = re.sub(
            r"(\*\*\[mu \(μ\) — Judgment Kernel Harness\]\(https://github\.com/qybaihe/mu\)\*\* \(`)[^`]+( ★`)",
            rf"\g<1>{mu_stars:,}\g<2>",
            readme,
        )
    if codex_ppt_stars:
        readme = re.sub(
            r"(\*\*\[codex-ppt\]\(https://github\.com/qybaihe/codex-ppt\)\*\* \| `)[^`]+( ★`)",
            rf"\g<1>{codex_ppt_stars:,}\g<2>",
            readme,
        )
    if sysu_stars:
        readme = re.sub(
            r"(\*\*\[SYSU-Anything\]\(https://github\.com/qybaihe/SYSU-Anything\)\*\* \| `)[^`]+( ★`)",
            rf"\g<1>{sysu_stars:,}\g<2>",
            readme,
        )
    open(README_PATH, "w", encoding="utf-8").write(readme)

    print(
        f"Updated stats: total={total_stars} ({total_forks} forks, {total_repos} repos), "
        f"bla={bla_stars}, mu={mu_stars}, npm={npm_label}"
    )


if __name__ == "__main__":
    main()
