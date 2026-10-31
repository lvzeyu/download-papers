"""Export selected cookies from your own Chrome profile for the institutional downloader.

Only cookies whose domain ends with one of the allowed suffixes are kept. Values are
never printed. The output file is created with mode 0600 outside the repository and is
read by scripts/download_institutional.py when present.
"""

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_OUTPUT = Path.home() / ".local/share/download-papers/imported-cookies.json"
DEFAULT_DOMAINS = ("nature.com", "springer.com", "springernature.com")


def export(domains: tuple[str, ...], output: Path, browser: str) -> dict[str, int]:
    import browser_cookie3

    loader = getattr(browser_cookie3, browser)
    cookies = []
    counts: dict[str, int] = {}
    for domain in domains:
        for c in loader(domain_name=domain):
            host = c.domain.lstrip(".")
            if not any(host == d or host.endswith("." + d) for d in domains):
                continue
            cookies.append({
                "name": c.name, "value": c.value, "domain": c.domain, "path": c.path or "/",
                "expires": int(c.expires) if c.expires else -1,
                "httpOnly": bool(c._rest.get("HttpOnly", False)), "secure": bool(c.secure),
            })
            counts[host] = counts.get(host, 0) + 1
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(cookies, handle)
    os.chmod(output, 0o600)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--browser", default="chrome", choices=("chrome", "brave", "edge", "firefox", "safari"))
    ap.add_argument("--domain", action="append", help="Allowed domain suffix (repeatable); default: nature/springer")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    counts = export(tuple(args.domain or DEFAULT_DOMAINS), args.output.expanduser(), args.browser)
    if not counts:
        print("No matching cookies found. Are you logged in in this browser?", file=sys.stderr)
        return 1
    print(f"Wrote {sum(counts.values())} cookies to {args.output} (mode 600):")
    for host, n in sorted(counts.items()):
        print(f"  {host}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
