# SQLHarness analysis page

Prepared and revised by Codex · 2026-11-09

Main editing page: <http://127.0.0.1:8000/>

Production: <https://andrewjorge.com/SQLHarness/>

The approved preview is promoted to `docs/index.html`. The former preview URL redirects to the main page and preserves its section fragment.

This revision grew from an independent proposal based on the [adversarial UX audit](analysis-adversarial-ux-audit-2026-11-09.md). It is designed to reduce avoidable reading and interaction effort while retaining the original page’s character. User satisfaction has not been measured with visitors.

## Changes and their purpose

| Change | Reader concern addressed |
| --- | --- |
| Three quiet links to architecture, workflow, and findings | Readers can choose where to enter without being assigned a single reading order. |
| Original overview prose and order restored | Preserve the author’s sequence: the retail problem, the AI/data-retrieval bridge, then the architecture’s purpose. This includes the original browser-saved wording rather than replacing it with a new opening. |
| Larger algorithm text and stronger text contrast | Verification should not require squinting or concentrating on low-contrast detail. The serif typography, palette families, node shapes, and chapter spacing remain. |
| Six stage pairs in the document’s actual reading order | Each example stays beside its own explanation on wide screens; on narrow screens, its explanation follows immediately before the next example begins. Readers do not have to reconstruct a correspondence between two distant sequences. |
| Continuous column backgrounds with a clear center gutter | The outer panels use the author’s selected #d6c5bd, distinct from the existing #c8bbbb example boxes, so both levels of grouping remain visible. Each panel extends 18px beyond its content column on both sides. The “produces” connector stays between the panels; graph checks and relationship references sit in the algorithm column. On phones, the backgrounds give way to the existing labeled, interleaved layout. |
| The question names its example data and exposes both source tables | The commerce fixture has five customers across three regions. A native disclosure shows the exact rows and the region_id-to-id relationship, so the question has a concrete database context. |
| Four construction steps explicitly produce the completed graph | A measured left-pointing connector links the last step to the completed graph on wide screens. On phones, DOM order is construction steps → downward handoff → completed graph → validation/reference. Both column transition arrows continue after this shared stage. |
| The 20 supported relationships and five graph checks in separate native disclosures | Readers can understand the graph before inspecting the complete rulebook. Validation remains explicit in the default explanation. No relationship signatures or graph checks were removed. |
| Direct stage interaction, a Clear focus action, and Escape | Persistent focus remains reversible. The redundant visible Compare buttons and long-distance counterpart links are removed. Keyboard users retain an equivalent toggle; surrounding stages remain readable. |
| Ordinary SQL selection and copying | Readers can inspect a clause without accidentally changing the comparison. |
| A complete count-connection walkthrough in the retrieval explanation | The relationship becomes a job description, compatible SQL templates are retrieved, matching words and fixed preferences order them, and assembly fills the named-field placeholder with customers.id. COUNT(*) remains a valid alternative; no probabilities or invented learned scores are displayed. |
| Graph relationship text available to assistive technology | Understanding the five connections does not depend entirely on seeing the SVG. |
| Bounded claims and consistent examples | Candidate order is marked illustrative; SELECT aliases match the returned JSON; the example’s order-by connection matches the relation registry; the fixture timing is labeled as SQL execution. The negative five-query result remains visible. |

## Boundaries

- Before promotion, the preview left the original page untouched. The approved version now owns `docs/index.html` and uses the reviewed shared stylesheet.
- The main page neither reads nor writes old browser drafts or saved layout. Text and graph positions are maintained in source.
- Text editing remains disabled. Existing writeup, catalog, and execution-rule links remain available.
- The page adds no backend calls, telemetry, or onboarding dialogue. Publication uses the existing GitHub Pages deployment from `main:/docs`.
- The displayed data is the recorded **commerce showcase** fixture from `scripts/build_showcase.py`, corroborated by `docs/data/offline-demo.jsonl`. It is separate from the MCP’s current **shop** demo database; those datasets are not conflated.
- The count-ranking explanation follows the current deterministic ranker in `src/sqlharness/workflow_retrieval.py`: a small explicit preference for a named-column count changes the ordering. The research fragment-catalog link is labeled as research; the illustrative left-hand candidate list is not presented as a recorded live ranking.

## Verification

- Inspected the revised wide layout and 390px layout; no horizontal overflow was observed. The intent stage now deliberately follows construction → handoff → completed graph → validation on narrow screens. Its measured element order passed that sequence check; the example tables also fit without horizontal overflow.
- Pairing remains side by side above 760px, where the graph still has room for readable nodes and collision-free labels. At 760px and below, each pair interleaves in the DOM reading order rather than shrinking the type or separating the two full sequences.
- Checked the narrow diagram for overlapping nodes and node/label intersections; none were detected in the tested layout.
- Exercised direct stage focus, keyboard activation, the clear action, Escape, SQL selection, and both reference disclosures. The carousel code remains unchanged from the earlier verified copy.
- Verified that SQL text can be selected without pinning a stage, and that unmatched algorithm sections retain full opacity.
- Checked HTML IDs/internal anchors, preservation of all 20 relationship entries, absence of enabled editing, JavaScript syntax, and browser console output. No errors were reported.
- Extracted the displayed data tables and compared every cell with the exact showcase SQL fixture. Executing the displayed assembled SQL against that fixture returned Northeast, 3.
- Restored both column continuation arrows after the intent stage, and replaced the retrieval example’s leading dash with an arrow.
- Column panels retain a 64px clear desktop gutter, including the intermediate desktop breakpoint. Content grids use a 100px gap to allow 18px panel padding on each side of that gutter. The measured “produces” arrow uses the panel edges so its shaft, arrowhead, and label stay inside the clear gutter.
- Verified the column update at the normal desktop width and at a 433px narrow layout: panels disappear for the stacked layout, construction → graph → references remains intact, and the graph-check disclosure opens without horizontal overflow. Keyboard focus and Escape still work.
- Baked the author’s selected #d6c5bd into the stylesheet and removed the temporary picker, its styles, and its browser-storage initializer. Both outer panels now use the source default; inner boxes remain #c8bbbb.
- Checked the changed text/background color pairs; each exceeds 4.5:1. This is a targeted contrast check, not a complete accessibility certification.

Internal simplification rubric: default necessity 4/4; hierarchy 4/4; microcopy 4/4; disclosure 4/4; functional preservation 4/4; trust/accessibility 4/4. These are design-review judgments, not user-study scores. The next useful validation would observe whether unfamiliar readers can explain one graph-to-SQL connection, choose their own depth, and leave a focused state without assistance.
