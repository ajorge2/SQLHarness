# SQLHarness analysis: adversarial review of the reader experience

**Reviewed:** 2026-11-09 · **Reviewer:** Codex  
**Page:** [SQLHarness analysis](http://127.0.0.1:8000/)  
**Scope:** Content, visual design, learning experience, interaction, accessibility, and emotional consequences. Review only; no page changes.

## Judgment

The page contains several good explanations, but its overall learning experience is less considerate than its individual explanations. It gives the reader an approachable problem, a useful concrete example, and a strong AMR analogy. It then becomes less clear about what the reader needs to understand, what they may safely skim, and how much interpretive work the page expects them to supply.

That is the central emotional risk: **a reader can be willing to learn and still feel that the explanation is spending their willingness badly.** They may become impatient with an arbitrary prerequisite, privately doubt their understanding, resist the imposed sequence, or quietly stop investing attention. These are different experiences, with different remedies.

The harshest defensible criticism is that the page sometimes makes readers do two jobs simultaneously: understand SQLHarness and determine how they are supposed to learn about it. The second job includes interpreting dense reference material, discovering an interaction's persistent state, finding a corresponding explanation after the layout stacks, and deciphering low-contrast detail. Much of that work contributes little to understanding the system.

This does **not** justify stripping out the personality, removing the technical depth, or making every reader follow a shorter summary. The strongest direction is to protect the reader's ability to choose depth, verify a tentative understanding, and recover their place.

### Read these findings first

| Priority | Finding | Human cost at the point of difficulty |
|---|---|---|
| High; measured | Some essential text has insufficient contrast; algorithm detail is substantially smaller than the surrounding explanation. | Difficulty seeing an explanation can be mistaken for difficulty understanding it. |
| High; reproduced | A click can leave most of the algorithm at 18% opacity, with no visible clear action; Escape does not clear it. | A reader must repair the view before continuing their own investigation. |
| High; reproduced | At the laptop breakpoint, example and algorithm become separate long sequences. | The reader must preserve an emerging idea while searching for its counterpart. |
| High for learning clarity; conditional | The full relation inventory has little indication of what must be understood now. | A reference can feel like an entrance examination. |
| High for technical credibility; observed | The worked graph conflicts with a relation rule shown on the same page; the displayed SQL and output column name also disagree. | A diligent reader can spend effort resolving a distinction that the page has not actually supplied. |
| Medium; contextual | Built behavior, architectural rationale, and experimental findings need a clearer relationship. | Readers may build a confident but inaccurate account of what the project established. |

## How this review interprets context

This is an educational project analysis and architecture-intuition brief. It is not a checkout, an onboarding flow, or a benchmark dashboard. Its separate technical writeup can reasonably contain the full experiment and failure analysis.

Several choices are deliberate and have legitimate benefits:

- Generous vertical space creates chapter transitions and room to breathe.
- The serif typography and taupe, brown, blue, and pink palette give the work an authored identity.
- A familiar business story invites readers who would not begin with a compiler diagram.
- Reusing one question avoids making readers learn a new example at every stage.
- Paired example and algorithm columns support comparison.
- Persistent highlighting lets a reader study a stage without maintaining a hover position.
- A complete relation inventory gives a technically curious reader something inspectable.
- A negative result at the end can make an effective research narrative.

The review therefore asks **when each choice stops helping a particular reader**, rather than treating the choice itself as a violation.

Three independent page reviews covered newcomer comprehension, technical credibility, and interaction/accessibility. Three parallel research reviews covered frustration/control, exclusion/competence, and expectation/trust; those reviews were then challenged again against this page's educational purpose. The impatient-reader analysis below holds the basic task constant: **understand the intuition behind SQLHarness**. It varies the reader's relationship with unfamiliar information, confidence, effort, and control.

### Evidence boundaries

- **Observed:** Rendered page, accessibility tree, computed styles, geometry, carousel, click-to-pin behavior, keyboard reversal, and responsive stacking.
- **Source-supported:** Behavior established by the HTML/CSS/scripts or the project's recorded research artifacts.
- **Research-supported mechanism:** An effect or relationship found elsewhere, with its study context and limits stated in the research section.
- **Emotional hypothesis:** A plausible appraisal by a reader of this page. These are questions to investigate, not emotions measured in SQLHarness users.

The character portraits are analytical constructions, not validated personality types, diagnoses, or demographic segments. One person can move between them within a single visit. They are also not fixed “learning styles.” Prior knowledge, interest, fatigue, trust, and the particular concept can change how the same person wants to proceed.

### What was inspected

| Actual CSS viewport | Observed layout and extent |
|---|---|
| 1596 × 893 | Paired workflow columns; page approximately 4437px tall; findings heading near y=4057. |
| 1280 × 1000 | Example precedes the entire algorithm; example begins near y=2517 and algorithm near y=4232. |
| 433 × 938 | Single-column reading; page approximately 7829px tall; findings near y=7423. No document-level horizontal overflow observed. |

The narrow override requested 390px; the browser's effective CSS width was 433px. A true 320px reflow test and a physical touch-device test were not completed. Page height describes navigation distance, not reading time or emotional burden.

The existing browser also displays saved wording that differs from the source HTML. This review uses the rendered wording for the current experience and identifies relevant source owners. For example, the live introduction includes the longer architectural explanation, and the first retrieved answer is still raw JSON; the source has a shorter purpose paragraph and a human-readable retrieved answer. Saved drafts were not cleared. At completion, editing remained disabled, the carousel was restored to slide 1, and pinned highlighting was cleared.

## Empathy model: what impatience is protecting

An impatient reader is not necessarily unwilling to think. They may be protecting momentum, a fragile understanding, dignity, scarce energy, or the right to decide what deserves study. Their behavior is an unreliable guide to the underlying feeling:

- Rapid scrolling can express excitement, avoidance, skepticism, or an attempt to recover a lost thread.
- Repeated reading can express productive curiosity or an increasingly hopeless attempt to reconcile inconsistent information.
- A dismissive comment can coexist with genuine interest.
- Quiet completion can conceal substantial effort or self-blame.
- Leaving can be an entirely reasonable decision about the reader's available attention.

Research gives reasons to inspect these distinctions. Workplace frustration diaries recorded anger directed at oneself and helplessness as well as anger at the computer. A controlled accessibility study found that uncertainty about whether information was missing or inaccessible could consume effort and produce frustration. These findings support asking what readers attribute difficulty to; they do not establish that this page causes shame. See research sources 1 and 6 below.

Likewise, confusion about a difficult idea can support learning when the learner can resolve it. Confusion about restoring the display offers a different kind of work. The objective is to preserve useful thinking while reducing avoidable delivery and recovery costs. See sources 15–17.

## Eighteen flavors of impatience around new information

Each portrait includes a reasonable willingness to learn, an internal tension, a specific point at which this page can lose the reader, and a charitable interpretation of the current design. The quoted thoughts are invented diagnostic prompts, not participant quotations.

### 1. Willing to work, unwilling to memorize without a reason

This reader enjoys understanding mechanisms. Their impatience appears when an explanation seems to require accepting vocabulary before showing what the vocabulary buys them. They can tolerate complexity for a purpose; arbitrary prerequisites feel like a poor bargain.

The business question and AMR example give them that purpose. The twenty-relation inventory can interrupt it: “Which of these do I need to understand to see why this works?” Their curiosity can become resistance, even though they would happily examine the same inventory after a concrete need arises.

**Watch for:** Skipping the registry, then returning because they worry it contained a missing premise. **Respectful response:** Make the conceptual target of that existing section apparent; keep its completeness available. The inventory may already work well for readers treating it as a reference. Research connection: relevance and interest, sources 12 and 18; page evidence: finding 3.

### 2. Needs one concrete case before accepting a new abstraction

They are not hostile to theory. They want to build it from something they can inspect. They may understand SQL well while having little patience for “atomic semantic parts” until a specific transformation makes the phrase meaningful.

The repeated customer-count example is a strong invitation. The frustration point is having to infer how a particular connection becomes a particular SQL choice: “I recognize the boxes, but I still don't know why this relation produces that clause.” A list of correct-looking endpoints does not necessarily supply the missing connection.

**Watch for:** Accurately naming nodes but being unable to explain one mapping. **Respectful response:** Ensure a representative mapping earns its place in the existing explanation. Do not explain every row. A concrete-first entry can serve this moment without defining the reader permanently. Research connection: source 17; evidence: findings 3 and 8.

### 3. Wants the governing idea before investing in the story

This reader feels comfortable once they know the structure of an argument. Examples then become evidence they can organize. Their impatience with a long analogy can resemble coldness, although their underlying need is orientation.

The architecture table helps. The opening retail story may feel like waiting outside the explanation: “What distinction am I supposed to carry into this example?” The same story that welcomes another reader can temporarily block this one.

**Watch for:** Heading scans, then a return to the introduction after finding the mechanism. **Respectful response:** Let an existing early sentence identify the organizing problem. Preserve the personal story and the default narrative. This is a conditional entry-point mismatch, not evidence that stories are ineffective. Research connection: sources 12, 16, and 18; evidence: findings 10 and 11.

### 4. Understands quickly, verifies late

They enjoy the pleasure of an idea clicking and move ahead before checking all its boundaries. Their impatience is enthusiastic. They may sound more certain than their understanding warrants because the explanation has given them a coherent picture.

The clean workflow feeds that momentum. An unqualified “stable map” or the 0.21ms figure can become a stronger claim in memory than the page intended. At the ending, the comparison may force them to revisit assumptions: “Which part had I assumed was established?”

**Watch for:** Fluent summaries that overstate capability or performance. **Respectful response:** Put scope in the existing consequential sentence or measurement label. Avoid interrupting every paragraph with caveats. Research connection: sources 8 and 19; evidence: findings 9–11. A reader can successfully acquire the intended broad intuition without being able to implement the system; the comprehension check must respect that boundary.

### 5. Follows every local step, then loses the global reason

They can explain each box individually. Their irritation comes when those explanations fail to accumulate into a usable whole. Recognition begins to substitute for understanding, and the reader becomes impatient with themselves: “I know what these words mean. Why can't I explain the point?”

The repeated question and large labels offer continuity. The complete role inventory and multiple representations can weaken it if the reader must repeatedly reconstruct how the current step serves the original request. Stacked counterparts add a navigation cost to that reconstruction.

**Watch for:** Repeating labels accurately but struggling to explain why the graph is useful. **Respectful response:** Carry the same central action through the existing transition and corresponding stage. A new paragraph of synonyms may add more local clarity without repairing the global connection. Research connection: sources 15–17; evidence: findings 3 and 5.

### 6. Conscientious enough to treat optional detail as homework

They want to understand properly and dislike skipping a foundation they might need later. They may have learned from earlier explanations that one omitted definition can make the next five paragraphs incomprehensible. That is a plausible history for the character, not a fact about any visitor. They may persist longer than a more confident reader, then become discouraged when the apparent syllabus keeps expanding.

The complete algorithm reassures them that the system has substance. Its presentation can also imply an obligation: “Do I have to learn all twenty relations before I have understood this brief?” Their impatience comes from uncertainty about sufficiency, not aversion to technical work.

**Watch for:** Slow, dutiful reading of every reference row before advancing. **Respectful response:** Distinguish the conceptual thread from the optional registry through hierarchy or one existing sentence. Preserve the registry for inspection. It is not inherently an examination; that is an interpretation to test. Research connection: sources 1, 11, and 12; evidence: finding 3.

### 7. Experienced nearby, protective of being put back at the beginning

They know databases or compilers and are genuinely curious about this design. They can still resent spending attention on explanations they already possess. Their expertise is uneven: familiar SQL does not mean familiarity with this intent representation.

The exact SQL and full algorithm give them a route into substance. A familiar metaphor or repeated basic example can feel redundant if they cannot move easily to the novel decision. They may become impatient precisely because they are willing to study the unfamiliar part carefully.

**Watch for:** Skimming basic explanation, then slowing down at a technical distinction. **Respectful response:** Make the novel contribution findable; do not remove the beginner's foothold. Research shows that helpful guidance can change with expertise, not that all expert readers prefer less explanation. Research connection: sources 16–17; evidence: findings 3 and 11.

### 8. Has a working mental model and needs a reason to replace it

They already understand direct question-to-SQL generation. New terminology creates a switching cost: “Why should I rebuild my understanding around a graph and fragments?” They may look stubborn while actually asking a fair comparative question.

Explicit stages and inspectable choices can win their interest. The page loses them if the added structure is described more fully than the problem it addresses. The negative result may increase their respect if it reveals the limits of the hypothesis.

**Watch for:** Repeated questions about what the graph changes, rather than how it is drawn. **Respectful response:** Keep rationale separate from demonstrated improvement. The conclusion can preserve the discovery narrative while giving this reader a defensible lesson. Research connection: sources 8 and 18; evidence: findings 10–11.

### 9. Comfortable carrying an unknown term, impatient with compulsory detours

They can temporarily accept a term and continue building context. That tolerance is a strength, but a reference-heavy presentation can take away their ability to use it. “I'll come back to that if I need it” becomes difficult when the explanation visually makes everything equally obligatory.

The large stage labels support selective reading. The dense relation block may feel like an imposed detour rather than available depth.

**Watch for:** Efficiently skimming the registry without losing comprehension. **Respectful response:** Make optional depth legible as optional. If the current hierarchy already permits that behavior, preserve it. This reader should not be forced into a glossary, tutorial, or preparatory exercise. Evidence: findings 3–4.

### 10. Uncomfortable advancing with an unresolved premise

They want to follow the author but cannot comfortably proceed when a foundational word or relation remains uncertain. Their thoroughness and urgency conflict: they want the click now and keep stopping themselves from moving toward it.

Paired representations promise that each statement can be checked. An unclear mapping or inconsistent type signature can trap them in rereading. “There must be a distinction I'm missing” can turn into self-directed irritation before skepticism about the page.

**Watch for:** Repeated returns to one arrow or phrase rather than general difficulty. **Respectful response:** Resolve the actual inconsistency and make one important premise checkable. Do not interpret their persistence as a request for more detail everywhere. Research connection: sources 1 and 15; evidence: finding 8.

### 11. Learns by making a prediction and seeing whether it holds

They want to anticipate the next transformation. A prediction gives them an active role, and being slightly wrong can be enjoyable when the explanation shows why. They become impatient if the page simply displays a correct-looking answer without letting them distinguish a good prediction from a lucky guess.

The ranking rows are a promising place for this reader. They may wonder why `COUNT(customers.id)` beats `COUNT(*)`, or why the combined SELECT wins. Numbers and pink selection show the outcome, while the basis for that outcome remains harder to inspect.

**Watch for:** Asking a specific “why this candidate?” question. **Respectful response:** Make one representative rationale available if ranking is central to the teaching objective; label illustrative ordering appropriately. Avoid adding invented scores or explanations to every row. Research connection: source 15; evidence: finding 8.

### 12. Learns by selecting, annotating, and moving material elsewhere

They think with external supports: a selected clause, a note, a query editor, or a comparison beside the article. Their impatience emerges when the interface blocks a familiar thinking gesture.

The assembled SQL offers useful material to work with. Turning the entire box into a toggle and suppressing text selection can interrupt that strategy. “Let me hold onto this one clause” is different from “Give me a download button.”

**Watch for:** Repeated selection attempts, manual transcription, or screenshots. **Respectful response:** Preserve selection inside SQL while retaining the stage interaction elsewhere. This brief does not need to become an executable tutorial. Research connection: sources 1–2; evidence: finding 7.

### 13. Curious in public, privately protective of their competence

They want to learn without having to announce that they missed a foundation. They may dislike remedial language as much as unexplained jargon. Their impatience protects dignity during the interval before understanding.

The personal voice and familiar example offer a private foothold. A dense technical transition can become uncomfortable when they cannot discreetly confirm one interpretation: “I think I understand this, but I can't check.” They may criticize the prose before admitting uncertainty.

**Watch for:** Vague positive comments, fast skimming, then a quiet return to the diagram. **Respectful response:** Let the explanation itself confirm a representative relationship. Do not add patronizing reassurance or assume the reader is insecure. Research connection: sources 1 and 7; evidence: findings 3 and 8.

### 14. Enjoys difficulty, loses patience with an unresolvable puzzle

They welcome productive confusion. A surprising relation or a negative result can make the article more interesting. Their tolerance ends when effort cannot produce resolution because the displayed materials disagree.

The central example says the output is constrained by an operation, while the nearby rule lists a condition in that position. The unaliased SQL count also reappears under an alias in the returned JSON. The reader can reasonably wonder whether either discrepancy expresses a subtle principle.

**Watch for:** Careful attempts to reconcile the contradiction before asking about it. **Respectful response:** Align the illustration and reference, or identify a conceptual simplification. The desired difficulty is reasoning about the architecture; a display inconsistency does not earn its cognitive cost. Research connection: source 15; evidence: finding 8.

### 15. Gives goodwill freely, then notices whether understanding is accumulating

They appreciate the craft and want the project to succeed. They can tolerate a difficult idea longer than an apparently unnecessary obstacle. Their impatience emerges gradually rather than in an angry moment.

The palette, authored voice, chapter pacing, and repeated example earn attention. Small accumulated costs—tiny verification text, a distant counterpart, an undiscovered undo—can exhaust the benefit of doubt. “I'm meeting this halfway; I need the next part to help me.”

**Watch for:** Continuing to scroll after their explanations become vaguer. **Respectful response:** Remove the few recovery and perceptibility costs before rewriting the story. Their dwindling goodwill does not prove that the chapter spacing was wrong. Research connection: sources 1–4; evidence: findings 1–7.

### 16. Wants to learn carefully, with less energy than willingness

They still care about the idea after a demanding day. Their frustration comes from having to spend effort on seeing, locating, or holding the explanation before they can reason about it. A deadline is not necessary for this experience.

The spacious sections and large nodes can be unusually welcoming. The 9–10px secondary layer and weak contrast can undo that welcome when they try to verify a detail. They may leave calmly, with no complaint about the design.

**Watch for:** Zooming, repeated position recovery, and shortening attempts to inspect detail. **Respectful response:** Keep the quiet hierarchy and improve the smallest necessary text and weakest contrast. Treat comfortable access as support for their willingness, not an accommodation for assumed lack of ability. Research connection: sources 6 and 12; evidence: findings 1–2.

### 17. Has heard many AI promises, still hopes for a genuinely interesting account

They guard against enthusiasm because familiar claims have disappointed them before. That history is a hypothetical context, not something inferred from a sharp comment. Their skepticism contains a wish to be persuaded fairly.

The personal visual identity and concrete example can attract them. The quick Claude Code analogy may instead trigger premature dismissal: “I think I know this pitch.” The candid losing result can reopen their curiosity.

**Watch for:** A superficial dismissal followed by close attention to a precise claim. **Respectful response:** Preserve the personality and make consequential claims bounded. Do not flatten the page to satisfy a reader whose skepticism may be partly habitual. Research connection: sources 8–10; evidence: findings 10–11.

### 18. Roots for the author and wants the learning to end somewhere meaningful

They can value an unsuccessful hypothesis. Their impatience is a wish to arrive at the changed understanding that makes the project worth discussing. They feel deflated if the ending reports a score without helping them understand what the score changed.

The negative finding is an asset. It becomes a satisfying resolution when the distinction between inspectability, execution controls, and correctness is precise. It becomes less satisfying if those benefits are blended into a vague compensation for the score.

**Watch for:** Slowing down at the ending, rereading it, and asking what the author would now do differently. **Respectful response:** Make the existing conclusion carry the limited lesson; let the technical writeup hold its fuller evidence. Do not manufacture a triumphant ending or relocate the reveal automatically. Evidence: findings 10–11.

## More nuance within the apparent learning preference

Even “wants the why first” is too coarse to be a complete character. Similar requests can protect different concerns. These variations are interpretive hypotheses; the page cannot identify them from a click or a scroll speed.

| Apparent preference | A more specific emotional character | Why this matters on this page |
|---|---|---|
| Wants relevance before terminology | **Interested, but cautious about investing in another vocabulary.** They have absorbed impressive terminology before and later found that it explained little. | They need one useful distinction the graph enables. More enthusiasm about AI will not settle that concern. |
| Wants relevance before terminology | **Intellectually generous, financially protective of attention.** They believe the work has value but want to decide which parts deserve close study. | A clearly optional role registry may satisfy them; the explanation does not need to prove every relation's usefulness. |
| Wants relevance before terminology | **Emotionally invested in the business problem.** They care about the exhausted person in the opening and want the technical detour to stay connected to that person. | They may accept formalism once they see what retrieval interruption it addresses. A broad claim of task restoration could instead overextend the promise. |
| Wants a concrete example | **Needs one anchor before unfamiliar terms stop slipping away.** Their patience increases rapidly once a single example becomes dependable. | The recurring customer question is valuable. Adding more examples too soon could make their problem worse. |
| Wants a concrete example | **Understands the instance quickly, doubts whether it generalizes.** They become impatient when the same tiny example recurs without revealing a new limitation. | They need a boundary or transfer insight, which can live in the existing conclusion or technical writeup; another basic explanation would feel repetitive. |
| Wants a concrete example | **Distrusts metaphors that conceal the actual mechanism.** They want a real transformation, not an appealing comparison. | The AMR active/passive example can help; the retail scenario alone cannot show how graph relations produce SQL. |
| Wants an organizing model | **Feels calmer when the whole argument has a shape.** An unknown detail is tolerable if they know where it belongs. | A compact architectural relationship can help them enjoy the personal narrative rather than rush past it. |
| Wants an organizing model | **Has an existing model they suspect is sufficient.** They want to know what this architecture reveals that direct generation does not. | Their impatience asks for intellectual necessity or an informative experiment, not simply a faster summary. |
| Wants an organizing model | **Dislikes being led toward a conclusion before seeing the premises.** They may welcome a losing result because it restores interpretive freedom. | Clear boundaries between rationale and evidence matter more to them than relocating every metric to the top. |
| Stops at an unfamiliar term | **Protects against compounding a mistaken premise.** They will proceed once one foundational relationship is confirmed. | A representative mapping can unlock progress; a full glossary may be unnecessary. |
| Stops at an unfamiliar term | **Treats all presented detail as an obligation.** They cannot yet identify which parts are reference material. | The hierarchy of the twenty relations is the intervention point, rather than additional definitions. |
| Stops at an unfamiliar term | **Understands the word but doubts that everyone is using it consistently.** They may be detecting a genuine contradiction. | The operation/condition mismatch should be repaired. Encouraging them to tolerate ambiguity would misread an accurate concern. |

These distinctions change what counts as help. One reader needs the existing example to remain stable; another needs to see how it transfers. One needs a governing rule; another needs to see why that rule earns a place. Adding an explanation indiscriminately can reassure one and irritate another.

### Emotional trajectories deserve as much attention as initial dispositions

- **Recognition → curiosity → withholding effort:** The business story earns recognition, but the reason to learn the formal categories remains unclear. The reader is still interested; they have stopped committing new terms to memory.
- **Tentative understanding → verification → self-doubt:** A reader tries to confirm one relation, encounters the diagram/reference mismatch, and assumes the missing distinction is theirs to discover.
- **Exploration → useful focus → recovery frustration:** Hover and pin help until the reader wants comparison again and must work out how to restore the view.
- **Familiarity → premature certainty → defensive rereading:** Familiar words make the mechanism feel understood; attempting one causal explanation exposes a gap. That is a reason to check the intended conceptual outcome, not to demand implementation mastery.
- **Careful effort → resolved confusion → satisfaction:** An unfamiliar representation becomes understandable through the concrete example. This is a positive learning experience worth preserving, even if the reader was briefly confused.
- **Accumulated effort → reduced confidence → quiet withdrawal:** No dramatic failure occurs. Tiny verification text, a distant counterpart, and an unclear stopping point gradually consume willingness.

These are possible paths, not a universal decline from confusion to frustration. Tutoring research has found movement back into engagement as well as movement among confusion, frustration, and boredom. Successful explanation can change the emotional state during the visit. See sources 15 and 20.

## Additional emotional lenses to run alongside the impatient portraits

These lenses cross the portraits above. They are not additional claims that harm occurred.

| Emotional lens | Specific context and trigger to investigate | What respectful interpretation requires |
|---|---|---|
| Uncertainty | A newcomer cannot distinguish an architectural rationale from a tested result. | Check their interpretation before assuming distrust. |
| Self-directed frustration | A diligent reader repeatedly fails to reconcile the graph and rule table. | Correct the explanation before attributing difficulty to the reader. |
| Embarrassment | A reader discussing the page hesitates to ask what a formal term means. | Make a private comprehension check possible; do not infer this from age or role. |
| Exclusion | A screen-reader user cannot inspect the same specific graph relationship. | Establish whether an accessible equivalent exists; visible nodes alone are insufficient. |
| Dependence | Magnification or missing accessible relationships makes comparison require outside help. | Preserve independent inspection and comfortable reflow. |
| Loss of control | A chosen highlight persists after the reader wants the overview back. | Make reversal discoverable while keeping the useful persistent focus. |
| Apprehension about exploration | After an unexpected persistent effect, a reader becomes reluctant to click again. | Test the reaction; do not equate surprise with fear. |
| Boredom | A reader sees repetition without a new inference to make. | Ask what the repetition teaches; reuse of the example may actually reduce effort. |
| Disappointment | The human opening suggests a broader benefit than the example resolves. | Clarify the actual retrieval contribution without removing empathy from the opening. |
| Skepticism | A technical reader notices an unusually small unqualified timing number. | Name the measured operation; skepticism can be healthy engagement. |
| Fatigue | A reader understands the idea but tires of inspecting tiny detail. | Keep conceptual challenge separate from perceptual labor. |
| Resentment | A reader feels an avoidable interaction puzzle is consuming attention they offered generously. | Require evidence of failed recovery; length or decorative personality alone is not disrespect. |

## Concrete page findings

### 1. The weakest text contrast is a genuine access problem

Computed text colors and their effective solid backgrounds produce these ratios:

| Text | Foreground / background | Contrast | Interpretation |
|---|---|---:|---|
| Added FROM/JOIN line | `#e68a51` / `#c8bbbb` | 1.39:1 | Very weak; computed size 13.5px. |
| Selected SQL candidate | `#ffffff` / `#f72688` | 3.76:1 | Below the 4.5:1 normal-text threshold; computed size 12px. |
| Pink result code | `#e9eeff` / `#f72688` | 3.25:1 | Below the normal-text threshold; computed size 13.5px. |
| Pink stage captions | `#f72688` / `#b9aaaa` | 1.68:1 | Weak, especially at the 9px label size. |
| Blue prose link | `#3054c1` / `#b9aaaa` | 2.97:1 | Below the normal-text threshold. |
| Main body | `#202124` / `#b9aaaa` | 7.20:1 | Strong; the entire palette should not be described as low contrast. |
| Pale text on brown | `#e9eeff` / `#7a563f` | 5.62:1 | Strong enough for normal text. |

W3C specifies 4.5:1 for normal text and 3:1 for qualifying large text. A 19.5px bold node value can qualify for the large-text exception; that does not make a 12px SQL row or small label equivalent. These are specific contrast findings, not a complete WCAG conformance audit. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

**Emotional concern:** A reader may feel the idea is harder than it is, or conclude that the page's visual care does not extend to receiving its content. **Minimum direction:** Adjust luminance within the selected palette. The evidence does not justify replacing the identity with a generic neutral design. Owners: [palette overrides](/Users/ajorge/life/graphsql-harness/docs/index.html:53), [label colors](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:247).

### 2. Secondary hierarchy has become secondary legibility

The desktop body is 15.5px, while algorithm paragraphs are 10px and the relation inventory is 9px. The distinction makes the left side easy to scan, but a reader checking an important detail must accept a substantial drop in reading comfort. Smaller text is not automatically inaccessible, and there is no universal WCAG minimum font size; the issue is this particular verification task and the surrounding scale.

**Emotional concern:** Confidence can drop during the attempt to verify understanding. **Minimum direction:** Increase the smallest essential text without making every reference equally prominent. Preserve the larger left nodes and secondary hierarchy. Owners: [algorithm paragraphs](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:258), [relation inventory](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:280).

### 3. The relation inventory lacks a clear learning contract

The brief promises intuition, while the main reading path includes twenty supported relation signatures and graph invariants. Completeness is useful. The problem is that a newcomer has little help distinguishing “notice this principle” from “understand every rule before continuing.”

**Emotional concern:** Curiosity can become an anxious attempt to satisfy an unclear standard. Another reader may resist being assigned vocabulary before seeing its value. **Minimum direction:** Establish the conceptual target in the existing transition or distinguish reference depth through presentation. Preserve all the text; do not solve this by adding a paragraph explaining every relation. Owner: [relationship reference](/Users/ajorge/life/graphsql-harness/docs/index.html:424).

### 4. The use of space and detail sends mixed signals about importance

At the measured desktop size, the architecture carousel ends near y=1865, the workflow title begins near y=2121, and the actual workflow begins near y=2365. These gaps successfully announce a new chapter. Meanwhile, the densest explanatory material receives the smallest type.

**Emotional concern:** A reader can feel that considerable visual room exists while the part they need to inspect remains cramped. This is a hierarchy tension, not evidence that white space is wasteful. **Minimum direction:** Judge spacing and type together. Preserve the chapter transition; consider whether the conceptual thread and readable detail deserve more of the available emphasis. Owners: [chapter spacing](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:86), [column layout](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:140).

### 5. Responsive stacking changes the teaching relationship

At 1280px CSS width, the worked example starts near y=2517 and the algorithm near y=4232. The approximately 1715px separation between their starting points replaces the desktop pairing with two complete successive sequences.

Example-first teaching can be effective, and stacking preserves readable widths. The risk appears when a reader is actively comparing corresponding stages or cannot retain the connection during the search. Page length alone does not establish that problem.

**Emotional concern:** Momentum becomes navigation work; some readers may blame themselves for losing a connection. **Minimum direction:** Preserve a direct, recognizable correspondence across the breakpoint. A local jump or reciprocal reference may help more than shrinking both diagrams. Owner: [responsive stacking](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:503).

### 6. The persistent highlight has an insufficiently apparent exit

Clicking a stage pins it and fades unmatched right-side content to `opacity:.18`, with additional desaturation and darkening. Escape did not clear the selection. Clicking the same stage again did. Hover/focus previews cease while a stage is pinned. At the stacked breakpoint, the controlling box can be far above the faded content.

The feature has a strong purpose: chosen focus without holding a pointer still. The failure condition is wanting the full picture back without discovering the reversal rule.

**Emotional concern:** A helpful learning aid can become a recovery puzzle or interfere with a two-stage comparison. **Minimum direction:** Make selection and reversal apparent, and keep surrounding context inspectable enough for comparison. Test the current fade before deciding how much to soften it. Owners: [fade rule](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:133), [toggle behavior](/Users/ajorge/life/graphsql-harness/docs/index.html:1356).

### 7. Whole-box interaction blocks a familiar learning strategy

The retrieval, assembled SQL, and result sections suppress text selection. Pointer-down prevents default behavior, and clicks clear existing selections. This supports smooth stage activation, but it also prevents normal clause selection and copying inside the SQL.

**Emotional concern:** The reader's way of thinking with the text fails unexpectedly. This matters even for someone who never intends to execute the SQL. **Minimum direction:** Preserve selection within technical text and keep the toggle affordance distinct. Owners: [selection suppression](/Users/ajorge/life/graphsql-harness/docs/analysis-plain.css:91), [pointer/click handlers](/Users/ajorge/life/graphsql-harness/docs/index.html:1379).

### 8. A diligent reader can encounter contradictions, not just difficult concepts

Three issues matter at the central learning moment:

1. The graph labels **most** as an operation and connects the output to it using **constrained by**. The relation reference specifies **output format → constrained by → condition**. The displayed instance and displayed signature therefore disagree.
2. The assembled query selects `COUNT(customers.id)` without `AS customer_count`, while the displayed JSON calls the column `customer_count`. The recorded fixture query does include an alias. The illustration has drifted from its evidence.
3. Ranked alternatives are displayed, but the page supplies little local basis for understanding why one wins. Some alternatives can express similar meanings. A static instructional ranking should not acquire the appearance of a measured result merely through numbered rows.

**Emotional concern:** Conscientious readers can initially assign unresolved inconsistencies to their own lack of understanding. **Minimum direction:** Align the example with its stated rules and output. Clarify illustrative versus measured ranking, and make one representative choice understandable if needed. Avoid fabricating scores or flooding every row with justification. Owners: [example nodes](/Users/ajorge/life/graphsql-harness/docs/index.html:239), [rule](/Users/ajorge/life/graphsql-harness/docs/index.html:436), [SQL](/Users/ajorge/life/graphsql-harness/docs/index.html:335), [output](/Users/ajorge/life/graphsql-harness/docs/index.html:356).

### 9. Equivalent access to the graph's reasoning needs attention

The diagram's edge labels are inside an `aria-hidden` SVG. The observed accessibility tree exposes nodes but not an equivalent sequence of the example's specific labeled connections. Entire diagram sections become toggle controls named “Highlight the … stage”; the original graph description is replaced, and no `aria-controls` association or destination explanation is added.

The surrounding algorithm provides some related information, so this is not a claim that the entire explanation is unavailable. A real screen-reader walkthrough is still needed to assess the full reading experience and equivalence.

**Emotional concern:** A reader may be unsure whether they missed information or were never given access to it. **Minimum direction:** Preserve an accessible account of the specific graph relationships and separate the meaning of the graph from the operation of its highlight control. The visible composition can remain unchanged. Owners: [hidden relationship layer](/Users/ajorge/life/graphsql-harness/docs/index.html:222), [control labels](/Users/ajorge/life/graphsql-harness/docs/index.html:1371).

### 10. Some sentences invite a broader inference than the evidence warrants

- The live opening promises help resuming a task mentally; the example demonstrates data retrieval. The human story is useful, but the relationship between those benefits must stay clear.
- “I built,” “proposed architecture,” and present-tense system behavior coexist. Present tense is conventional in architectural explanations; a consequential ambiguity still deserves a precise verb.
- “Stable map” can mean a fixed representation format. Following the active/passive AMR example, it may also imply stable generated graphs. The project records substantial graph variation, so those meanings should be distinguished.
- “Safe” can be interpreted more broadly than the specific read-only, schema, row-cap, and deadline controls described.

**Emotional concern:** An enthusiast may overlearn the claim, while a skeptic may spend effort deciding which interpretation the author intended. **Minimum direction:** Bound the existing statements locally. No status dashboard or general warning panel is warranted. Owners: [introductory prose](/Users/ajorge/life/graphsql-harness/docs/index.html:140), [AMR bridge](/Users/ajorge/life/graphsql-harness/docs/index.html:186), [recorded parser variation](/Users/ajorge/life/graphsql-harness/docs/final-results.md:23).

### 11. The ending needs an accurate lesson more than a victorious lesson

The five-case comparison is candid: direct generation answered four correctly and both structured variants answered three. Putting that result at the end is defensible for this educational narrative. A reader who prefers evidence first may need a more direct route, but late placement alone is not deceptive.

Two local precision issues remain. First, `0.21 ms` is a deterministic fixture's SQL-execution latency, not a question-to-answer workflow time. Second, attributing easier governance to the semantic structure blends failure localization with a shared execution boundary; the study says all generated proposals crossed the same authority.

**Emotional concern:** The reader may be uncertain which earlier claims to revise, or leave without the interesting lesson of the negative result. **Minimum direction:** Name the timed operation beside the number. Separate inspectability from independently enforced execution limits. Preserve raw counts, the small-study qualification, and the negative result. Owners: [timing](/Users/ajorge/life/graphsql-harness/docs/index.html:521), [fixture](/Users/ajorge/life/graphsql-harness/docs/data/offline-demo.jsonl:1), [conclusion](/Users/ajorge/life/graphsql-harness/docs/index.html:528), [shared authority](/Users/ajorge/life/graphsql-harness/docs/final-results.md:41).

### 12. Small wording and version differences can interrupt the learning relationship

The live page contains “mentally pick up right a task right where you left it” and “AMR looks at past word order.” The latter can momentarily reverse the intended “looks past word order” meaning. The source already differs in some places. The link “Experimentation results recorded on technical writeup” is also harder to parse than the destination merits.

**Emotional concern:** Readers can stop to decode accidental phrasing or become unsure whether they misunderstood. **Minimum direction:** Consolidate the intended authored wording before publication and correct these small interruptions. Do not turn a copy edit into a rewrite of the personal voice. Owners: [intro](/Users/ajorge/life/graphsql-harness/docs/index.html:143), [draft restoration](/Users/ajorge/life/graphsql-harness/docs/index.html:646), [technical link](/Users/ajorge/life/graphsql-harness/docs/index.html:150).

## Research used, and what it actually supports

The literature helps identify mechanisms and questions. It does not validate these eighteen portraits or quantify emotional effects on this page. Several studies are foundational and use older interfaces, controlled educational tasks, or small samples; their original contexts matter.

1. **Lazar et al. (2006), workplace frustration diaries.** Fifty workplace users reported 149 incidents, including 15 reports of anger at oneself and 34 of helplessness/resignation; feelings could overlap. This supports examining inward-directed reactions and unsuccessful recovery, not equating difficulty with shame. Historic, self-reported, mixed technology incidents. [Original author-hosted paper](https://www.cs.umd.edu/~ben/papers/Lazar2006Workplace.pdf)

2. **Bessière et al. (2002), computer frustration.** A modified diary study of 108 users found associations between incident frustration, task importance, time lost, and repair time. It supports examining the cost imposed on a chosen goal. Correlation does not show that every obstacle causes frustration. [University of Maryland report](https://api.drum.lib.umd.edu/server/api/core/bitstreams/601b65f3-1b75-4bc8-9c27-5c6b88e40854/content)

3. **Mark, Gudith & Klocke (2008), interrupted work.** In a 48-participant office-task experiment, interrupted conditions increased reported frustration, stress, effort, and time pressure despite faster completion. This cautions against treating eventual success as a pleasant experience. Imposed interruptions differ from voluntarily comparing diagrams. [Original paper](https://www.ics.uci.edu/~gmark/chi08-mark.pdf)

4. **Carton & Aiello (2009), control over interruptions.** In a timed spreadsheet experiment with 70 analyzed undergraduates, the opportunity to prevent social interruptions reduced stress even though participants did not use it. This motivates checking perceived control; it does not prove that adding a clear button reduces article-reader stress. [Original journal article](https://onlinelibrary.wiley.com/doi/10.1111/j.1559-1816.2008.00434.x)

5. **Sellen, Kurtenbach & Buxton (1992), mode awareness.** Text-editing experiments found that feedback and how modes were maintained affected mode errors. Emotion was not measured. The appropriate transfer is to inspect whether a reader recognizes a persistent selection and its reversal. [Author-hosted research](https://www.billbuxton.com/ModeErrors.html)

6. **Bigham, Lin & Savage (2017), inaccessible versus absent information.** A controlled study with 30 blind and 30 sighted participants examined uncertainty about missing, inaccessible, and difficult information. It supports investigating wasted effort and frustration when access itself is unclear. It does not characterize all screen-reader experiences. [Original Carnegie Mellon paper](https://www.cs.cmu.edu/~jbigham/pubs/pdfs/2017/nkwydk.pdf)

7. **Jin et al. (2025), judgment and digital frustration.** A qualitative study with 20 adults aged 55–65 in Chinese cities reported internalized failure and concerns about judgment during e-commerce tasks. Its sequential, scripted-agent design and narrow sample limit generalization. It supplies a reason to ask privately about embarrassment, not to presume it from age or role or add a support agent here. [Original ASSETS paper](https://doi.org/10.1145/3663547.3759739)

8. **Luger & Sellen (2016), expectations of conversational agents.** Interviews with 14 users found substantial expectation/capability mismatches. This supports investigating how readers interpret the scope of an AI-related promise. It studied agents in use, not portfolio articles. [Original publication record](https://www.research.ed.ac.uk/en/publications/like-having-a-really-bad-pa-the-gulf-between-user-expectation-and/)

9. **Tractinsky, Katz & Ikar (2000), aesthetics and perceived usability.** An ATM-surrogate experiment with 132 students found that aesthetics affected perceived usability. It supports preserving visual identity as part of experience; it does not establish that attractive design compensates for unreadable text. [Original author-hosted paper](https://www.ise.bgu.ac.il/faculty/noam/papers/00_nt_ask_di_iwc.pdf)

10. **Fogg et al. (2002), web credibility.** In evaluations by 2,684 participants, design appearance appeared in 46.1% of credibility comments. That is a comment frequency, not a causal estimate or the proportion deceived by design. It supports taking information organization and appearance seriously without treating skepticism as proof of manipulation. [Stanford research report](https://credibility.stanford.edu/pdf/How_Do_People_Evaluate_a_Web_Site%27s_Credibility_v37.pdf)

11. **Peters, Calvo & Ryan (2018), METUX.** This theoretical design framework applies autonomy, competence, and relatedness to technology experience. It helps ask what a reader's impatience may be protecting. It is not an experiment establishing these emotions on this page or a validated segmentation of impatient people. [Original framework](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.00797/full)

12. **W3C (2021), cognitive accessibility guidance.** The Working Group Note addresses clear terminology, summaries, excessive content, fatigue, and recovery after distraction. It supports examining the burden of interpretation while preserving meaningful detail. It is supplemental guidance, not a controlled emotion experiment or a separate conformance requirement. [Making Content Usable](https://www.w3.org/TR/coga-usable/)

13. **Desmet (2003), product-emotion appraisal model.** This theoretical account treats emotion as an appraisal of a product in relation to a person's concerns. It supports asking why the same feature helps one reader and frustrates another. It does not provide a one-to-one mapping from a color, font, or layout to an emotion. [Original article](https://www.tandfonline.com/doi/full/10.2752/146069203789355480)

14. **W3C, contrast minimum.** This supplies the text-contrast thresholds used above. It establishes a perceptibility criterion, not a measured emotional consequence. [Understanding SC 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

15. **D'Mello, Lehman, Pekrun & Graesser (2014), confusion and learning.** Two experiments used contradictory statements in animated-agent lessons about scientific reasoning. Learning benefits depended on contradictions successfully inducing confusion and on its resolution; self-reported confusion was an imperfect manipulation measure. This supports distinguishing useful conceptual difficulty from peripheral confusion. It does not justify leaving an inconsistent graph unexplained. [Original study](https://www.sciencedirect.com/science/article/pii/S0959475212000357)

16. **Kalyuga, Ayres, Chandler & Sweller (2003), expertise reversal.** This review synthesizes experiments showing that guidance effective for less experienced learners can become unnecessary or counterproductive with expertise. It motivates optional depth and attention to prior knowledge. It is a review, not a new SQLHarness experiment, and does not support fixed learning-style labels. [Original review](https://doi.org/10.1207/S15326985EP3801_4)

17. **Worked-example and presentation experiments.** Sweller & Cooper (1985) conducted five algebra experiments in which worked examples could improve acquisition efficiency and subsequent performance on structurally similar problems; the finding did not establish broad transfer. Kalyuga, Chandler & Sweller (1998) reported three experiments in which useful presentation changed with expertise, including a shift away from redundant explanatory text. These support testing representative examples and integrated mappings while preserving a concise route for knowledgeable readers. They do not establish a universal article sequence. [Sweller & Cooper, original study](https://www.tandfonline.com/doi/abs/10.1207/s1532690xci0201_3), [Kalyuga et al., original study](https://doi.org/10.1518/001872098779480587)

18. **Hulleman, research on perceived utility and interest.** Experimental educational work investigated whether making personal connections to material affected interest and achievement. This supports testing whether readers understand why a formal step matters, not assuming that an author-provided business metaphor automatically supplies personal relevance. Classroom interventions differ from voluntary article reading. [Original doctoral research](https://eric.ed.gov/?id=ED498264)

19. **Rozenblit & Keil (2002), explanatory confidence.** Across experiments, attempting to explain mechanisms often reduced participants' estimates of their own prior understanding. The research principally examined beliefs about existing knowledge, not learning from this page. It supports checking a reader's own explanation alongside confidence; it does not establish that these diagrams produce false confidence or that a broad intuitive account is inadequate. [Original Yale paper](https://cogdevlab.yale.edu/sites/default/files/files/rozenblit%20%26%20keil%20%202002.pdf)

20. **D'Mello & Graesser (2012), dynamics during complex learning.** Two computer-tutoring studies tracked changing affect rather than treating a learner as having one permanent state. Their findings support investigating reversible movement between confusion and engagement, alongside other affective transitions. They do not imply that article readers inevitably become frustrated or bored, or validate the character trajectories proposed above. [Original study](https://www.sciencedirect.com/science/article/pii/S0959475211000806)

## What should survive an eventual revision

- The AMR active/passive example: it offers a concrete route into an unfamiliar idea.
- The recurring business question: familiarity frees attention for each new representation.
- The distinctive palette and serif identity, with specific contrast repairs.
- Spacious chapter transitions, judged together with the scale of essential detail.
- Both the conceptual overview and the complete technical reference, with clearer choice about depth.
- The stage-mapping interaction, with more apparent state and recovery.
- The candid negative result, raw counts, small-study qualification, and access to the technical writeup.
- Existing accessibility strengths: real labeled carousel buttons, disabled endpoints, polite slide status, keyboard activation, coarse-pointer target expansion, and reduced-motion handling.

## What this audit rejects

It does not support calling the palette ugly, treating serif type as inherently inappropriate, diagnosing readers from their impatience, calling the late finding deceptive, treating a losing experimental score as a failed project, or assuming that every unfamiliar word needs a definition on screen. Trust-game and dark-pattern research was considered too remote to justify claims of betrayal or manipulation here.

It also does not support optimizing the page for the most contemptuous possible reader. A skeptical or restless character is useful when it reveals an avoidable cost; their preferences do not automatically outweigh accuracy, personality, or the needs of a careful learner.

## Order of attention if changes are later authorized

1. Repair measured contrast and check the smallest essential type.
2. Reconcile the central example, relation rule, SQL, and output.
3. Make pinned-state recovery apparent and preserve ordinary technical-text selection.
4. Preserve stage correspondence across the stacked layout and supply equivalent accessible graph meaning.
5. Clarify the learning target of the relation reference and the scope of consequential claims using existing prose.
6. Test whether readers actually need a different entry route or earlier finding before changing the narrative order or reducing the chapter breaks.

These are priorities for a later decision, not changes made during this audit.

## How to test the emotional hypotheses without manufacturing them

Give readers the same basic goal—understand SQLHarness's intuition—and vary the starting conditions separately: prior SQL knowledge, familiarity with graph representations, available energy, and whether they prefer to establish relevance before examining a mechanism. Do not assign them a caricature to perform.

Ask them to explain one relationship, predict one fragment choice, locate the study's lesson, compare two stages, and restore the ordinary view after exploration. On a return visit, ask them to resume from an interrupted point. Include readers using their preferred magnification and an actual screen-reader walkthrough.

After a difficulty, ask: **“What were you expecting there?” “What did you think the page wanted you to understand?” “What made you continue or stop?”** Let participants describe their own feelings before offering an emotion list. Check whether uncertainty concerned the idea, its presentation, or the reader's confidence about their own interpretation.

Observe comprehension and recovery alongside emotional experience. A correct answer can be accompanied by frustration; a pleasant impression can coexist with a mistaken mental model. Preserve productive difficulty when it leads to a supported insight. Remove work that merely makes the explanation harder to receive.
