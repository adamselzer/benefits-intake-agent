# Information architecture

Information architecture is the structure beneath the visuals: how content is
organized, labeled, navigated, and found, and whether that structure mirrors the
user's mental model rather than the builder's. This document states the IA
deliberately, in the canon's terms (Rosenfeld & Morville's four systems; Abby
Covert's "structure follows the mental model"), and is honest about the gaps.

## The decision that comes first: who, and when

IA is downstream of the task model, so the task model is settled first.

This tool is **not** a standalone application a caseworker opens between cases. State
systems of record (Bridges, CalSAWS) already run the deterministic eligibility math;
a worker will not leave that system for a separate app, and re-computing eligibility
is the least valuable thing here. The value is upstream: reading messy uploaded
documents, cross-checking them, and triaging what needs a human.

So the tool is a **document-intake triage layer**. It runs on incoming applications,
extracts and validates the uploads, and produces two surfaces:

1. a prioritized **queue** for whoever distributes work (a supervisor or an
   auto-assignment step), and
2. a per-case **review surface** for the caseworker, designed to write its flags
   into the case record rather than replace it.

The web app is the demonstration of those two surfaces, not a claim that a worker
opens it cold. Every IA choice below follows from this model.

## Users and task model

- **Caseworker (primary).** On a flagged case: grasp the outcome, resolve what needs
  their judgment, verify the basis, act. Task units, in priority order:
  outcome → what-to-resolve → basis → evidence.
- **Queue owner / supervisor.** Triage and assign: which cases are clean, which need
  attention, in what order.

These two task models map one-to-one to the two surfaces (case review, queue).

## Organization systems

Schemes are named here on purpose (Rosenfeld & Morville distinguish exact schemes,
like alphabetical, chronological, or status, from ambiguous schemes, like task,
audience, or topic):

- **Queue → by task-status.** Needs review, then Cleared, with counts. The user's
  question is "what needs me," so status is the primary axis. Within a group, by
  case id (chronological-ish). A status scheme, chosen over a scenario scheme
  because scenario ("conflicting", "missing") is the builder's taxonomy, not the
  worker's question.
- **Case review → by task sequence / decision priority.** Outcome, then
  what-to-resolve, then the determination, then evidence-on-demand. A task-based
  scheme, overview-first.
- **Documentation → by audience.** Operate it (Live demo), understand it (How it
  works), reuse it (Design system).

## Labeling: controlled vocabulary

One concept, one name, everywhere. Product chrome uses the worker's language;
implementation jargon is confined to the explanatory surfaces.

| Concept | Canonical label | Not |
|---|---|---|
| Route requiring a person | **needs review** | flagged, human-in-the-loop, escalated |
| Clear-eligible + clear-ineligible at queue level | **cleared** | done, complete |
| The agent's output packet | **recommendation** | decision, determination |
| The rules-core result | **determination** | the agent's call |
| Extracted facts | **evidence** | data, fields |
| Sourcing of a fact | **provenance** | source, origin |

Implementation terms ("agents", "LangGraph", "MCP", "rules-as-code") belong in
**How it works** rather than the working surface's chrome. (Applied: the app's eyebrow
now reads as the product, "Intake triage · food assistance", not "Agents".)

## Navigation and wayfinding

- **Global:** three tabs by audience (operate / understand / reuse), with active
  state.
- **Local:** the queue is the case navigator; the active case is highlighted and its
  id is always visible on the review surface ("you are here").
- **Contextual:** within a case, the action items link the outcome to the specific
  thing to resolve; citations link to policy.
- **Gaps:** no breadcrumb or cross-surface "where am I" beyond the active tab; fine
  at this scale, needed when the queue grows.

## Search and findability

None today, which is acceptable at ~30 cases. At scale the status organization
already supports **faceting**: filter the queue by status, then search by case id or
applicant. Search is a scale feature, deliberately deferred, not an oversight.

## Per-surface structure

- **Queue:** status groups → case rows (id + scenario tag + status dot). One screen,
  scannable.
- **Case review:** decision header → "what you need to resolve" → determination →
  evidence (disclosure) → footer. Overview-first, details on demand.
- **Docs:** Live demo (the surfaces), How it works (user/need, pipeline, decisions),
  Design system (Civil tokens + components, links to the showcase).

## Honest gaps (the work an IA pass still owes)

1. **Suite-level IA is absent.** Four tools + a design system + a portfolio
   narrative, with no navigable hub, no cross-linking, and inconsistent navigation
   (this app has three tabs; the Streamlit tools have two; labels differ). Architecting
   the portfolio as one information space (a hub with consistent global nav and a
   shared vocabulary) is the largest remaining IA task.
2. **The controlled vocabulary is not yet enforced** across the sibling apps.
3. **No search**, by deliberate deferral.

## Sources

- Rosenfeld & Morville, *Information Architecture for the World Wide Web* (the four
  systems: organization, labeling, navigation, search).
- Abby Covert, *How to Make Sense of Any Mess* (structure follows the mental model).
- Nielsen Norman Group, information architecture and findability.
