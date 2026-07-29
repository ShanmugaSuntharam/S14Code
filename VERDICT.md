# Verdict — vuln-triage app (Part 2)

This app works: it answers exclusively in composed interfaces, drives a real
multi-turn vulnerability-triage workflow, and rejects six different injection
attempts while still rendering the safe parts of the same surface. But "it
works" is doing some load-bearing hiding here. This is the honest version.

## The catalog-discovery bet doesn't hold uniformly

The whole architecture rests on one idea: hand the model a raw catalog
manifest (component names, props, nothing else) and trust it to pick the
right component for a given piece of data, with no per-component prompting.
For most of the catalog this genuinely works — `Map`, `CodeDiff`, and
`CommentThread` were all composed correctly the first time they were needed,
purely from matching prop shapes in the manifest to data pointers in the
model, with zero prompt engineering pointing at them by name.

`ApprovalCard` broke that streak. Across multiple live runs, the model
consistently built an "approval" tab and then left it empty — it had the
component available, the data (`/summary`, an approve/reject decision named
directly in the goal) was present, and it still didn't reach for it without
an explicit instruction added to the compose prompt naming `ApprovalCard` by
type. That's a real asymmetry, not a fluke: components whose purpose is
obvious from their prop names (`Map.points`, `CodeDiff.diff`) get discovered;
a component whose purpose is more about *intent* than *shape* (approve vs.
reject as a decision, not a data type) apparently doesn't. "Unprompted
discovery" is a real property of this system, but it's not a guaranteed one,
and it silently fails closed (an empty tab) rather than failing loud.

There was also a moment this session where the fix for that exact problem
almost cost the property for the other three components — a "just in case"
hint was added naming `CodeDiff`/`CommentThread`/`Map` explicitly too, "for
robustness," even though they didn't need it. It was caught and reverted, but
it's worth naming: once you're inside a prompt telling the model what to use
for one thing, it's very easy to keep going and tell it what to use for
everything, and the codebase stops proving what it claims to prove.

## The intended 5-turn drill-down isn't what actually happens

The domain was designed as five separate stages, each one a fresh turn: pick
a CVE, see the fix, see the reaction, see where it's exploited, decide.
In practice, the model in use for most of this work (`gemini-flash-latest`)
tends to front-load the entire drill-down — fix, reactions, exploitation map,
and the approval card — into tabs inside a *single* composed surface, right
after the first ask. The five-stage narrative still holds up as a *user
experience* (you still see all five things, in order, by tapping tabs and
then approving), but only two of those moments are actual live agent turns;
the rest are client-side tab switches inside one response.

Neither behavior is wrong, exactly. The compose prompt literally instructs
the model to build "the RICHEST interface that serves the goal" — which
straightforwardly encourages front-loading once the model is capable enough
to reason about the whole goal at once. But it does mean the demo doesn't
show what the original design implied it would show: five independent
LLM-driven composition steps, each reacting only to the latest user action.
It shows two, plus navigation. That distinction matters for what's actually
being demonstrated versus what the domain narrative claims is happening, and
it's worth saying so on camera rather than letting the tab UI imply five
separate agent decisions were made.

## The injection wall is real, but it's a structural check, not a semantic one

`validate_surface`'s three invariants — every type must be in the catalog,
every value must be data (no markup, no script/data URLs, no smuggled event
handlers), every action must be registered — are deterministic and
demonstrably effective: six distinct attack shapes (stored XSS in a comment
title, an unregistered destructive button action, a smuggled `onclick`, a
`javascript:` URL, an unknown component type, inline `<script>`) were all
rejected with the correct, specific invariant, and the safe components in
the same surface still rendered. That's a genuinely solid boundary, and it
doesn't depend on the model "behaving" — it would catch a hostile surface
even if it came from a compromised or adversarially-prompted model, because
it inspects structure, not intent.

What it can't catch: a model that writes something false, misleading, or
unsafe *in prose*, inside a field the schema correctly expects text in. If
Gemini asserted a fabricated CVE had "no known exploits" while also
generating exploit location data, the wall would validate that surface
cleanly — every field is exactly the shape it claims to be. The wall is a
data-shape boundary, not a truth boundary. That's a reasonable scope for what
it's meant to do, but it shouldn't be oversold as "the model can't say
anything wrong" — it can, as long as it says it in the right shape.

## The stack's reliability during development had little to do with the code

A large share of this session's actual debugging time went into fighting
Gemini's free-tier quota and an undocumented model-availability restriction —
not the app. `gemini-2.5-flash` started 404ing with "no longer available to
new users" months ahead of its own published retirement date, for reasons
Google hasn't documented. Switching to the rolling alias `gemini-flash-latest`
fixed that, but introduced a second, genuinely subtle bug: the gateway's
reasoning-disable logic recognized dated model names like `2.5-flash` but not
a rolling alias, so `reasoning: "off"` silently did nothing, and an
unrelated retry-on-400 fallback (built for a different purpose) quietly
absorbed a first attempted fix and made it look like nothing had changed.
Getting to the real fix required adding raw HTTP status-code logging — the
app-level error messages alone weren't enough to tell "wrong config" apart
from "model doesn't support this."

None of that reflects badly on this specific app's design. But it's worth
being honest that, for stretches of this session, whether the demo worked at
all was determined more by which of five pooled API keys happened to have
quota left than by anything in this repository. That's a fragile foundation
for a demo, and it would be an unacceptable one for anything beyond a demo.

## One small, real gap left as-is

`ApprovalCard`'s schema defines both `confirm` and `reject` actions, and the
composed JSON correctly includes both, every time. The client-side renderer
only ever displays the confirm ("Approve") button. This wasn't investigated
or fixed — that renderer predates this branch — but it means the actual
human-in-the-loop safety story ("the user can approve *or* reject") is
currently weaker in practice than the data model promises. Worth fixing
before this is anything more than a course demo.

## Bottom line

The three invariants hold under real adversarial pressure, and the
"compose everything, never plain text" property holds without exception
across every turn observed. The "discover components unprompted" property is
real but not uniform — it holds for data-shaped components and needed help
for an intent-shaped one. The five-stage narrative is true experientially
but not architecturally — it's two agent decisions wearing a five-stage
costume. None of that makes the app not work. It makes "it works" a more
specific and more interesting claim than it first looks, and that's the
claim worth standing behind rather than the simpler one.
