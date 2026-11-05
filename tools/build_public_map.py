#!/usr/bin/env python3
"""Build the GitHub copy of the HRTO 2026-66847-I case map.

Input:  the HTML of the Claude case map artifact (shared layer only; private
        notes live in the artifact's owner-only database and are never in the HTML).
Output: a plain HTML page, ready to be locked with StatiCrypt.

Changes made for the GitHub copy:
  * removes lawyers and clinics the Applicant contacted (keeps HRLSC and The 519)
    and every link touching them;
  * removes the owner-only review band, the Claude comments/owner script and the
    "To comment" footer line.

Usage: build_public_map.py ARTIFACT.html OUT.html
"""
import json
import re
import sys

DROP_TYPES = {"lawyer"}
DROP_IDS = {"blac", "dls"}          # clinics contacted, other than HRLSC / The 519
KEEP_IDS = {"hrlsc", "the519"}


def main(src, out):
    t = open(src, encoding="utf-8").read()

    m = re.search(r"const SHARED = (\{.*?\});\n", t, re.S)
    if not m:
        sys.exit("SHARED data block not found; artifact layout changed")
    s = json.loads(m.group(1))

    drop = {n["id"] for n in s["nodes"]
            if (n.get("type") in DROP_TYPES or n["id"] in DROP_IDS) and n["id"] not in KEEP_IDS}
    s["nodes"] = [n for n in s["nodes"] if n["id"] not in drop and not n.get("private")]
    s["links"] = [l for l in s["links"]
                  if l["source"] not in drop and l["target"] not in drop and not l.get("private")]
    s["version"] = "github"
    t = t[:m.start(1)] + json.dumps(s, ensure_ascii=False) + t[m.end(1):]

    # owner-only review band
    t, n1 = re.subn(r'<section id="owner".*?</section>', "", t, count=1, flags=re.S)
    # capabilities block (comments + owner layer), up to the end of the script
    t, n2 = re.subn(r"// ---- capabilities:.*?(?=</script>)", "", t, count=1, flags=re.S)
    # footer line about commenting
    t = re.sub(r"To comment, select a party[^<]*", "", t)
    if not (n1 and n2):
        sys.exit("owner section or capabilities block not found; check artifact layout")

    open(out, "w", encoding="utf-8").write(t)
    print(f"nodes={len(s['nodes'])} links={len(s['links'])} removed={sorted(drop)} built={s.get('built')}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
