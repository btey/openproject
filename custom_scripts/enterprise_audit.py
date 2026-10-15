#!/usr/bin/env python3
"""Maintenance helper for the "all Enterprise features unlocked" fork of OpenProject.

Subcommands (run from anywhere inside the repository, Python 3.8+, standard library only):

  scan [--update-baseline]
      Search the working tree for every known way OpenProject implements an Enterprise restriction
      (custom_maintenance/restriction_patterns.tsv) and compare the result with the triaged baseline
      (custom_maintenance/known_residuals.tsv). NEW hits are restrictions nobody has reviewed yet.

  verify
      Check the invariants (custom_maintenance/invariants.tsv): assertions that our customizations
      are still in place. Run it right after every upstream merge.

  upstream-impact <old_tag> <new_tag>
      Before/after merging: (1) files that upstream changed AND we customized (conflict-prone),
      (2) files where upstream ADDED hits of a restriction pattern between the two tags
      (new restrictions to remove). Needs both tags locally: git fetch upstream --tags

  delta-diff <old_tag> <new_tag> [--before REV] [--after REV]
      Compare OUR customization delta before and after an upstream merge, file by file:
      delta_before = git diff <old_tag> <before>   (default before = HEAD, i.e. run it while the merge is uncommitted)
      delta_after  = git diff <new_tag> <after>    (default after = working tree)
      Reports preserved / DROPPED / NEW / CHANGED customizations, ignoring context, line numbers and indentation.
      Use it to review what an agent (or a human) really did during a merge.

  markers
      List the explicit in-code markers of our custom changes (OP-CUSTOM / CUSTOM CHANGE).

Exit status is 1 when scan finds NEW hits, verify finds a violation, or upstream-impact finds new
restriction hits, so the commands can be used in CI.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
MAINT = os.path.join(REPO, "custom_maintenance")
PATTERNS_FILE = os.path.join(MAINT, "restriction_patterns.tsv")
BASELINE_FILE = os.path.join(MAINT, "known_residuals.tsv")
INVARIANTS_FILE = os.path.join(MAINT, "invariants.tsv")

# Paths that never contain restriction logic worth reviewing.
EXCLUDE = re.compile(
    r"^(spec/|docs/|lookbook/|db/migrate/|config/locales/|custom_maintenance/|custom_scripts/|\.github/|"
    r"modules/[^/]+/(spec|config/locales|doc)/|frontend/src/assets/|frontend/node_modules/)"
    r"|(\.spec\.ts|_spec\.rb|\.md|\.lock|\.svg|\.png|\.jpg|\.mp4|\.ya?ml)$"
)
# YAML is excluded above except for the static link catalog, which is itself an upsell surface.
INCLUDE_ANYWAY = re.compile(r"^config/static_links\.yml$")


def git(*args, check=True):
    res = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)
    if check and res.returncode not in (0, 1):
        sys.exit("git %s failed: %s" % (" ".join(args), res.stderr.strip()))
    return res.stdout


def read_tsv(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            rows.append(line.rstrip("\n").split("\t"))
    return rows


def load_patterns():
    return [(r[0], re.compile(r[1]), r[2], r[3] if len(r) > 3 else "") for r in read_tsv(PATTERNS_FILE)]


def considered(path):
    return bool(INCLUDE_ANYWAY.match(path)) or not EXCLUDE.search(path)


def count_hits(text, patterns):
    out = collections.Counter()
    for pid, rx, _, _ in patterns:
        n = len(rx.findall(text))
        if n:
            out[pid] = n
    return out


def scan_tree():
    patterns = load_patterns()
    files = [f for f in git("ls-files").splitlines() if considered(f)]
    hits = {}
    for f in files:
        full = os.path.join(REPO, f)
        try:
            with open(full, encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        counts = count_hits(text, patterns)
        for pid, n in counts.items():
            hits[(f, pid)] = n
    return hits, {p[0]: p for p in patterns}


def cmd_scan(args):
    hits, pats = scan_tree()
    if args.update_baseline:
        with open(BASELINE_FILE, "w", encoding="utf-8") as fh:
            fh.write("# Triaged residual restriction hits (file, pattern id, count). Regenerate with:\n")
            fh.write("#   custom_scripts/enterprise_audit.py scan --update-baseline   (ONLY after triaging every NEW hit)\n")
            for (f, pid), n in sorted(hits.items()):
                fh.write("%s\t%s\t%d\n" % (f, pid, n))
        print("Baseline written: %d entries -> %s" % (len(hits), os.path.relpath(BASELINE_FILE, REPO)))
        return 0

    baseline = {}
    if os.path.exists(BASELINE_FILE):
        for f, pid, n in read_tsv(BASELINE_FILE):
            baseline[(f, pid)] = int(n)

    new = {k: v for k, v in hits.items() if k not in baseline}
    grown = {k: (baseline[k], v) for k, v in hits.items() if k in baseline and v > baseline[k]}
    gone = [k for k in baseline if k not in hits]

    def report(title, rows):
        print("\n== %s (%d)" % (title, len(rows)))
        for line in rows:
            print("  " + line)

    report(
        "NEW restriction hits - triage each one (remove the restriction or add to baseline)",
        ["%-12s %s  x%d  [%s]  recipe %s" % (pid, f, v, pats[pid][2], pats[pid][3])
         for (f, pid), v in sorted(new.items(), key=lambda kv: (kv[0][1], kv[0][0]))],
    )
    report("GROWN hits (count increased in a baselined file)",
           ["%-12s %s  %d -> %d" % (pid, f, a, b) for (f, pid), (a, b) in sorted(grown.items())])
    report("GONE from baseline (file removed or cleaned - refresh baseline)", ["%s  %s" % (pid, f) for f, pid in sorted(gone)])
    print("\nTotal current hits: %d | baselined: %d" % (len(hits), len(baseline)))
    if new or grown:
        print("\nLine numbers: git grep -nE '<regex from restriction_patterns.tsv>' -- <file>")
        return 1
    return 0


def cmd_verify(_args):
    failures = 0
    for inv_id, path, mode, regex, why in [r + [""] * (5 - len(r)) for r in read_tsv(INVARIANTS_FILE)]:
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            print("MISSING  %-26s %s (file not found) - %s" % (inv_id, path, why))
            failures += 1
            continue
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        found = re.search(regex, text, re.DOTALL | re.MULTILINE) is not None
        ok = found if mode == "present" else not found
        if not ok:
            failures += 1
            print("VIOLATED %-26s %s (%s %s) - %s" % (inv_id, path, mode, regex, why))
    total = len(read_tsv(INVARIANTS_FILE))
    print("\n%d/%d invariants hold." % (total - failures, total))
    return 1 if failures else 0


def parse_delta(diff_text):
    """file -> Counter of (sign, stripped line) for every added/removed line of a -U0 diff."""
    delta = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            current = None if path == "/dev/null" else (path[2:] if path.startswith("b/") else path)
            if current:
                delta.setdefault(current, collections.Counter())
        elif line.startswith("--- "):
            if line[4:] != "/dev/null" and not current:
                current = line[6:] if line.startswith("--- a/") else None
                if current:
                    delta.setdefault(current, collections.Counter())
        elif current and (line.startswith("+") or line.startswith("-")):
            body = line[1:].strip()
            if body:
                delta[current][(line[0], body)] += 1
    return delta


def cmd_delta_diff(args):
    before_rev = args.before or "HEAD"
    before = parse_delta(git("diff", "-U0", "--no-renames", "--diff-algorithm=patience", args.old_tag, before_rev))
    after_args = ["diff", "-U0", "--no-renames", "--diff-algorithm=patience", args.new_tag] + ([args.after] if args.after else [])
    after = parse_delta(git(*after_args))
    skip = re.compile(r"^(custom_scripts/|custom_maintenance/|\.serena/|\.claude/)")
    buckets = collections.defaultdict(list)
    for path in sorted(set(before) | set(after)):
        if skip.search(path):
            continue
        b, a = before.get(path, collections.Counter()), after.get(path, collections.Counter())
        if not b and not a:
            continue
        if b == a:
            buckets["preserved"].append((path, ""))
        elif b and not a:
            buckets["DROPPED"].append((path, "%d changed lines no longer differ from %s (lost, or upstream adopted it)" % (sum(b.values()), args.new_tag)))
        elif a and not b:
            buckets["NEW"].append((path, "%d changed lines vs %s did not exist before" % (sum(a.values()), args.new_tag)))
        else:
            lost = sum((b - a).values())
            gained = sum((a - b).values())
            buckets["CHANGED"].append((path, "-%d/+%d lines of delta vs %s" % (lost, gained, args.new_tag)))
    print("Delta compare: before = diff(%s..%s)  after = diff(%s..%s)\n" % (args.old_tag, before_rev, args.new_tag, args.after or "working tree"))
    for name in ("DROPPED", "CHANGED", "NEW"):
        print("== %s (%d)" % (name, len(buckets[name])))
        for path, note in buckets[name]:
            print("  %s  %s" % (path, note))
        print()
    print("== preserved unchanged (%d)  [list with --verbose]" % len(buckets["preserved"]))
    if args.verbose:
        for path, _ in buckets["preserved"]:
            print("  " + path)
    print("\nReview order: DROPPED (lost customization?) -> CHANGED (re-applied differently) -> NEW (agent additions / merge artifacts).")
    print("Inspect one file: git diff %s -- <file>   |   git diff %s %s -- <file>" % (args.new_tag, args.old_tag, before_rev))
    return 0


def cmd_markers(_args):
    out = git("grep", "-nE", "OP-CUSTOM|CUSTOM CHANGE", "--", ".", ":!custom_maintenance", ":!custom_scripts", check=False)
    print(out or "No markers found.")
    return 0


def cmd_upstream_impact(args):
    for tag in (args.old_tag, args.new_tag):
        if subprocess.run(["git", "-C", REPO, "rev-parse", "-q", "--verify", "refs/tags/%s" % tag],
                          capture_output=True).returncode != 0:
            sys.exit("Tag %s not found locally. Run: git fetch upstream --tags" % tag)

    ours = set(git("diff", "--name-only", args.old_tag, "HEAD").splitlines())
    upstream = git("diff", "--name-status", "--no-renames", args.old_tag, args.new_tag).splitlines()
    changed = {}
    for line in upstream:
        status, path = line.split("\t", 1)
        changed[path] = status

    overlap = [p for p in changed if p in ours]
    if changed and len(overlap) > 0.5 * len(changed):
        print("WARNING: HEAD differs from %s in most of the files upstream changed - it probably already contains %s.\n"
              "         Run this command BEFORE merging (HEAD = %s + our customizations), otherwise section 1 is meaningless.\n" %
              (args.old_tag, args.new_tag, args.old_tag))
    print("== 1. Upstream changed %d files; %d of them are files WE customized (expect merge conflicts / re-verify)" %
          (len(changed), len(overlap)))
    for p in sorted(overlap):
        print("  %s %s" % (changed[p], p))

    patterns = load_patterns()
    print("\n== 2. Restriction hits ADDED by upstream between %s and %s (new restrictions to remove)" % (args.old_tag, args.new_tag))
    new_hits = 0
    for path, status in sorted(changed.items()):
        if status == "D" or not considered(path):
            continue
        new = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (args.new_tag, path)], capture_output=True)
        try:
            new_text = new.stdout.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new_counts = count_hits(new_text, patterns)
        if not new_counts:
            continue
        old_counts = collections.Counter()
        if status != "A":
            old = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (args.old_tag, path)], capture_output=True)
            old_counts = count_hits(old.stdout.decode("utf-8", "replace"), patterns)
        for pid, n in sorted(new_counts.items()):
            if n > old_counts.get(pid, 0):
                new_hits += 1
                custom = "  (customized locally)" if path in ours else ""
                print("  %-12s %s %s  %d -> %d%s" % (pid, status, path, old_counts.get(pid, 0), n, custom))
    print("\n%d new restriction hit group(s)." % new_hits)
    return 1 if new_hits else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--update-baseline", action="store_true")
    s.set_defaults(fn=cmd_scan)
    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    sub.add_parser("markers").set_defaults(fn=cmd_markers)
    d = sub.add_parser("delta-diff")
    d.add_argument("old_tag")
    d.add_argument("new_tag")
    d.add_argument("--before", help="revision holding our delta before the merge (default HEAD)")
    d.add_argument("--after", help="revision holding the result (default: working tree)")
    d.add_argument("--verbose", action="store_true")
    d.set_defaults(fn=cmd_delta_diff)
    u = sub.add_parser("upstream-impact")
    u.add_argument("old_tag")
    u.add_argument("new_tag")
    u.set_defaults(fn=cmd_upstream_impact)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
