# Demo transcript — Vuln Triage (`/vuln-triage`)

**URL:** `http://127.0.0.1:8113/vuln-triage`
**Seed prompt (paste into the textbox, then click Ask):**

> Show me recent critical vulnerabilities in a popular Python web framework, and let me pick one to drill into: first see its proposed fix, then see community reaction to the disclosure, then see where it is being reported as exploited, and finally decide whether to approve a remediation action.

**Before recording:** confirm both servers are up (`netstat -ano | findstr ":8111 :8113"`) and `glc_v3/.env` has `GEMINI_MODEL=gemini-flash-latest`. Composing takes 15–30s per turn (it's two chained LLM calls: `content` then `compose_surface`) — narrate over the wait rather than cutting it, since the "Run Steps" progress list (`run_started` → `task_started content` → `task_succeeded content` → `task_started surface` → ...) is worth showing live as proof nothing is pre-scripted.

---

## Framing note — read this before recording

The app was designed so each drill-down stage is a separate agent turn (tap → new compose call). In practice, the model in use now (**`gemini-flash-latest`**, via the `gemini_1` provider slot) tends to **front-load the entire drill-down into one rich composition** the moment you ask, rather than doling it out stage-by-stage. So the actual live flow is **2 real agent turns** (the initial ask, and the final Approve tap) with the 4 middle stages appearing as **tabs inside turn 1's single composed surface** — you switch between them client-side, no server round-trip, no new Gemini call.

This is worth saying out loud in the recording: it demonstrates that the UI composer is **adaptive to the data actually present**, not a fixed template — the same domain-agnostic prompt produces a leaner turn-by-turn UI with one model and a denser all-at-once UI with another, and the injection wall validates either way. Narrate the 5 "reveals" the assignment asks for as 5 *conceptual* moments, and call out which are server-composed vs. tab switches as you go.

---

## Turn 1 — Ask (real agent turn: `content` → `compose_surface`)

**Say:** "I'm asking a single open-ended goal — not picking from a menu — and the agent is going to compose the entire interface live, no template."

Type the seed prompt, click **Ask**. While it composes, point out the **Run Steps** trace appearing on the right (`run_started`, `graph_patched`, `task_started content`, `task_succeeded content`, `task_started surface`) — this is the real execution graph, not a spinner.

When it lands, the header badge reads **`gemini_1 · 21 components · 0 executable`** — call this out: *"0 executable"* means the deterministic injection wall (`validate_surface`) ran against the model's own output and rejected zero components — every one of the 21 passed the catalog / data-not-code / event invariants.

**Components visible (top of screen + "Proposed Fix" tab active by default):**

| Component | Role |
|---|---|
| `Text` (heading) | Title — e.g. "Django Web Framework Security Advisory: CVE-2024-42005" |
| `Text` (body) | Intro/summary paragraph |
| `Row` → 3× `StatTile` | CVSS v3 Score, Affected Versions, Exploitation Risk |
| `Card` → `Column` → 3× `Button` | "Select Vulnerability to Inspect" — the CVE choice list (turn 1's original design intent — clicking one of the *other* two CVEs would fire a new `request_data` server turn) |
| `Tabs` (4 labels) | Proposed Patch / Community Reaction / Exploitation Map / Remediation Action |
| `Column` → `CodeDiff` | The active tab: the proposed fix, rendered as a real unified diff |

**Say:** "This is the fix stage of the drill-down — a `CodeDiff` component, bound to real diff text the model generated for this CVE, not a static fixture."

---

## Turn 2 (conceptual) — Community Reaction tab

**Client-side tab switch — no new agent call.** Click the **"Community Reaction"** tab.

**Components revealed:** `Column` → `CommentThread` — an authored, threaded list of remarks (security lead, dev lead, an automated threat-intel note), each with author + timestamp.

**Say:** "This is the same composed surface from turn 1 — I'm just switching tabs client-side. The `CommentThread` component was already validated and sitting in the DOM."

---

## Turn 3 (conceptual) — Exploitation Map tab

**Client-side tab switch.** Click **"Exploitation Map"**.

**Components revealed:** `Column` → `Map` — pins for the real-world probe/exploit-origin locations the model generated (e.g. Ashburn VA, Frankfurt, Singapore), each with a label and real lat/lng.

**Say:** "The `Map` component — one of the three catalog components built for this course — rendering live geographic data bound straight from the model's structured output."

---

## Turn 4 (conceptual) — Remediation Action tab

**Client-side tab switch.** Click **"Remediation Action"**.

**Components revealed:** `Column` → `ApprovalCard` — a summary line, a bound `params` block listing the remediation options (approve emergency patch / apply WAF mitigation / reject and request more analysis), and an **Approve** button.

**Note to mention on camera:** the `ApprovalCard` schema defines both a `confirm` and a `reject` action, and both are present in the composed JSON — but the client renderer currently only surfaces the **Approve** button visually. Worth flagging as a known follow-up, not a validator gap (the reject action *is* registered and would be accepted if wired up).

---

## Turn 5 — Approve (real agent turn: new `content` → `compose_surface`)

**Say:** "Tapping Approve sends a real action back to the agent — this is a brand-new compose call, not a cached view."

Click **Approve**. Composing again (~15-30s). Watch the conversation breadcrumb at the bottom gain a `› approve` segment — proof the tap round-tripped through the server and the new turn is conditioned on the prior pick (`"So far the user then picked: approve."` appears in the new turn's prompt if you inspect the network tab).

**Components on the result surface:**

| Component | Role |
|---|---|
| `Text` (heading) | "Remediation Action Executed" |
| `Notice` (tone: good) | Confirmation summary sentence |
| `Row` → 4× `StatTile` | Deployment Status, Instances Patched, Rollout Time, Exploit Attempts Blocked |
| `Card` → `Text` | Remediation execution steps (bulleted) |
| `Divider` | Visual separator |
| `Row` → 2× `Button` | Follow-up choices ("Return to Vulnerability Dashboard", "Run On-Demand Security Scan") — each would fire yet another live turn if tapped |

**Say to close:** "Every screen you just saw — the fix, the comments, the map, the approval, and this confirmation — came from one shared, domain-agnostic component catalog and one shared injection wall. Nothing here is a vuln-triage-specific template; the same `/app` protocol drives a completely different domain just by changing the seed goal."

---

## Bonus segment (optional, no Gemini call needed) — the injection wall

If you want to demonstrate the security boundary explicitly (recommended — this is the "attack the boundary" requirement):

```bash
uv run python proofs/adversarial_attack_proof.py
```

This posts a hand-crafted surface straight at the deterministic validator — 2 safe components (`Notice`, `ApprovalCard`) alongside 6 attacks: a stored-XSS payload in a CVE comment title, a `Button` wired to an unregistered `delete_all_data` action, a smuggled `onclick` handler, a `javascript:` URL, an unknown component type standing in for an iframe, and inline `<script>` markup. **Say:** "All six attacks are rejected — one for each of the three invariants — and the two safe components still render. One poisoned component can't blank the whole surface."

Console output shows each attack's id, whether it was `REJECTED`, and which invariant (`catalog` / `data-not-code` / `event`) it broke.

---

## Quick reference — full component inventory across the demo

`Text`, `Row`, `Column`, `Card`, `Button`, `Divider`, `StatTile`, `Tabs`, `Notice`, `CodeDiff`, `CommentThread`, `Map`, `ApprovalCard` — 13 distinct catalog component types used across the two real turns, three of them (`CodeDiff`, `CommentThread`, `Map`) built specifically for this course's Part 1 submissions and now proven working end-to-end with live Gemini output in a real application, not just the isolated proof harness.
