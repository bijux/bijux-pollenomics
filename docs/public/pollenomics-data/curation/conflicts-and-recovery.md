---
title: Conflicts and Recovery
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Conflicts And Recovery

Scientific curation is incomplete when disagreement or missing evidence is
hidden behind one convenient value. Bijux Pollenomics preserves competing
claims, identifies their owners and scopes, and records the evidence required
to resolve or safely bound the disagreement.

## Distinguish The Gap

| State | Meaning | Appropriate response |
| --- | --- | --- |
| absent upstream | the identified source does not provide the needed fact | retain the absence and seek another authoritative source if justified |
| not captured | the source may contain the fact, but the governed capture does not | recover the named artifact or field and record retrieval identity |
| captured but unparsed | useful source text exists but cannot be normalized safely | preserve text, improve a bounded parser only when semantics are known |
| ambiguous | several identities or interpretations remain plausible | keep alternatives and require a discriminating locator or review decision |
| conflicting | captured sources make incompatible claims | preserve both, compare scope and authority, and record the governing decision |
| unsupported for use | the fact may be real, but it does not satisfy the proposed product claim | qualify, use as context, defer, or refuse without weakening the gate |
| outside scope | evidence is valid but not a member of this geography or product | retain source evidence and account for the non-membership |

Missing, false, excluded, and out of scope are not synonyms. Recovery begins
only after the state is correctly classified.

## Conflict Record

A conflict is reviewable when it preserves:

- the governed subject and claim dimension;
- every competing value at its original scope;
- source family, release or accession, artifact, locator, and source wording;
- whether each claim is sample-, site-, project-, paper-, or product-owned;
- precision, dating basis, coordinate basis, and other material qualifiers;
- the selected governing claim, if one is justified, and why;
- the public effect and the evidence that would reopen the decision.

```mermaid
flowchart LR
    Left["claim A + locator + scope"] --> Compare{"authority and meaning review"}
    Right["claim B + locator + scope"] --> Compare
    Compare -->|one governs| Decision["select for declared use; retain both"]
    Compare -->|both compatible at different scopes| Qualify["preserve scoped claims"]
    Compare -->|unresolved| Queue["named recovery item"]
    Decision --> Descendants["re-evaluate affected products"]
    Qualify --> Descendants
```

A sample-owned date can govern that sample while a broader project interval
remains valid context. The two claims need not be averaged or reduced to one
unqualified field.

## Recovery Is Evidence Acquisition

Recovery items name a scientific deficit, not merely an unfinished file:

| Recovery target | Completion evidence |
| --- | --- |
| supporting material | content-identified artifact, paper link, manifest membership, and retrieval context |
| sample identity | source-owned label, stable repository identity, project relation, and ambiguity disposition |
| locality | sample-owned wording, source locator, site relation, hierarchy, and resolution posture |
| chronology | source wording, owner, normalized point or interval when defensible, basis, and precision |
| coordinate | source pair or documented named-place resolution, method, basis, confidence, and mapping posture |
| product admission | rerun decision with passed rules, updated accountability, and descendant review |

Finding a plausible value on the web is not completion. The value becomes
governed evidence only when its identity, source, locator, ownership, meaning,
and downstream impact are recorded.

## Recovery Loop

```mermaid
stateDiagram-v2
    [*] --> Classified: gap or conflict identified
    Classified --> Acquired: supporting material captured
    Acquired --> Curated: identity and claims reviewed
    Curated --> Rejected: evidence remains insufficient
    Rejected --> Classified: retain reason and next condition
    Curated --> Accepted: governing decision supported
    Accepted --> Rebuilt: affected descendants regenerated
    Rebuilt --> Verified: semantic and membership diffs reviewed
    Verified --> [*]
```

Recovery does not patch the visible report first. It changes the governing
source or claim record, then rebuilds normalized, review, admission, and
publication descendants. This order prevents a map from disagreeing with the
database that is supposed to explain it.

## Accept A Recovery

A recovery is complete when the intended evidence boundary is coherent and
the causal diff is explainable:

1. the recovered artifact has stable source and content identity;
2. the object and claim owners are unambiguous or explicitly qualified;
3. original wording, nulls, conflicts, and precision remain preserved;
4. previous recovery and exclusion records close by reason, not disappearance;
5. every affected normalized and published member is identified;
6. unchanged descendants are also explainable when the new evidence does not
   cross their product contract.

Continue with [record admission](record-admission.md) to interpret the revised
decision, [animal source intake](../sources/animal-source-intake.md) for the
literature and archive boundary, and [verification evidence](../../pollenomics/quality/test-strategy.md)
for claim-specific proof.
