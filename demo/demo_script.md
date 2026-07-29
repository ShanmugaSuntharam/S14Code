[Open http://127.0.0.1:8113/vuln-triage]

"This is a UI-only vulnerability triage assistant. Every screen you're about to see is composed live by Gemini — there's no fixed template behind it."

[Paste seed prompt into the textbox]

"I'm giving it a single open-ended goal: show me recent critical vulnerabilities in a popular Python web framework, let me pick one to drill into, see its proposed fix, see community reaction, see where it's being exploited, and decide whether to approve a remediation action."

[Click Ask]

"While it composes, you can see the run steps on the right — this is the actual execution graph, not a loading spinner."

[Wait for composition to finish]

"The example CVE data here is fabricated for this demo — it is not a real disclosed vulnerability."

"The header shows twenty-one components, zero executable. That means every component the model generated was checked against a deterministic injection wall, and all of them passed clean."

"At the top: a heading, an intro paragraph, and three stat tiles — CVSS score, affected versions, and exploitation risk."

"Below that, a card with the list of vulnerabilities to choose from."

"And here's the drill-down, laid out as tabs: Proposed Patch, Community Reaction, Exploitation Map, and Remediation Action."

"The Proposed Patch tab is open by default — this is a CodeDiff component, rendering a real unified diff."

[Click "Community Reaction" tab]

"Community Reaction — a CommentThread component, with authored, timestamped remarks."

[Click "Exploitation Map" tab]

"Exploitation Map — a Map component, plotting the real-world locations where exploitation was reported."

[Click "Remediation Action" tab]

"Remediation Action — an ApprovalCard, with a summary, the remediation options, and an approve action."

[Click "Approve"]

"I'm approving the remediation. This sends a real action back to the agent and triggers a brand-new composition."

[Wait for composition to finish]

"And here's the result — a fresh confirmation surface: a notice, four stat tiles showing deployment status, instances patched, rollout time, and exploit attempts blocked, and the execution steps that were taken."

"Every screen you just saw came from the same shared component catalog and the same injection wall — nothing here is hardcoded to vulnerabilities specifically."

[Optional — open a terminal]

"Now let's look at the security boundary directly."

[Run: uv run python proofs/adversarial_attack_proof.py]

"This sends six different attacks straight at the validator — a stored cross-site scripting payload, an unregistered destructive action, a smuggled event handler, a javascript colon URL, an unknown component type, and inline script markup."

[Wait for output]

"All six are rejected, each one flagged with the exact rule it broke. And the two safe components in the same surface still render — one poisoned component can't take down the whole screen."
