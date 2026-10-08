# 60-second demo script

**0–10 seconds — problem**

“Direct NL-to-SQL hides the system's reasoning inside one model call. SQLHarness asks whether explicit semantic structure can improve reliability and cost while making every decision inspectable.”

**10–25 seconds — research lens**

Show the architecture. Explain that the request becomes an intent graph, the graph retrieves parameterized SQL fragments, and a lightweight model assembles the query. Then show the frozen result: direct generation scored 4/5 while both SQLHarness variants scored 3/5. The project keeps the loss visible and decomposes it into parser, catalog, retrieval, and assembly stages.

**25–45 seconds — engineering lens**

Open the successful cached trace. Follow the natural-language request, SQL proposal, schema-aware AST validation, MCP-backed authority decision, bounded read-only execution, receipt, and gold-result comparison. Switch to “Blocked write” to show a destructive proposal rejected before execution.

**45–60 seconds — close**

“The same repository tests a research hypothesis and implements the authority boundary needed to operate it responsibly. The direct call wins this small slice; the useful output is knowing exactly why, and having a governed system in which the next hypothesis can be tested.”
