const traceContent = document.querySelector("#trace-content");
const provenance = document.querySelector("#trace-provenance");
const choices = document.querySelectorAll(".trace-choice");

let successfulTrace;
let blockedTrace;
let manifest;

function text(value) {
  if (Array.isArray(value)) return value.join("\n");
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function card(label, title, body, tone = "") {
  const article = document.createElement("article");
  article.className = "trace-step";

  const labelNode = document.createElement("span");
  labelNode.className = "trace-label";
  labelNode.textContent = label;

  const titleNode = document.createElement("h3");
  titleNode.className = tone;
  titleNode.textContent = title;

  const pre = document.createElement("pre");
  pre.textContent = text(body);

  article.append(labelNode, titleNode, pre);
  return article;
}

function renderSuccessful() {
  const trace = successfulTrace;
  const receipt = trace.authority_receipt;
  traceContent.replaceChildren(
    card("Input", "Business request", `${trace.example.question}\n\nEvidence\n${trace.example.evidence}`),
    card("Proposal", "Candidate SQL", trace.generation.sql),
    card(
      "Authority boundary",
      receipt?.decision === "executed" ? "Validated and committed" : "Proposal blocked",
      `Decision: ${text(receipt?.decision)}\nReceipt: ${text(receipt?.receipt_id)}\nTables: ${text(trace.validation.referenced_tables)}\nColumns: ${text(trace.validation.referenced_columns)}\nErrors: ${text(trace.validation.errors)}`,
      receipt?.decision === "executed" ? "pass" : "block",
    ),
    card(
      "Execution",
      trace.execution_correct ? "Result matched gold" : "Result differed",
      `Columns: ${text(trace.candidate_execution?.columns)}\nRows: ${JSON.stringify(trace.candidate_execution?.rows)}\nLatency: ${Number(trace.candidate_execution?.latency_ms || 0).toFixed(2)} ms`,
      trace.execution_correct ? "pass" : "block",
    ),
  );
}

function renderBlocked() {
  const trace = blockedTrace;
  traceContent.replaceChildren(
    card("Input", "Requested operation", trace.request),
    card("Proposal", "Candidate SQL", trace.proposed_sql),
    card(
      "Authority boundary",
      "Policy rejected proposal",
      trace.validation.errors,
      "block",
    ),
    card(
      "Execution",
      "Database untouched",
      `Decision: ${trace.decision}\nExecuted: ${trace.database_touched ? "yes" : "no"}\nReceipt: ${text(trace.receipt_id)}`,
      "pass",
    ),
  );
}

async function loadTraceData() {
  try {
    const [traceResponse, policyResponse, manifestResponse] = await Promise.all([
      fetch("data/offline-demo.jsonl"),
      fetch("data/policy-demo.json"),
      fetch("data/manifest.json"),
    ]);
    const traceText = await traceResponse.text();
    successfulTrace = JSON.parse(traceText.trim().split("\n")[0]);
    blockedTrace = await policyResponse.json();
    manifest = await manifestResponse.json();
    provenance.textContent = `${manifest.trace_examples} reproducible fixtures · zero API calls`;
    renderSuccessful();
  } catch (error) {
    provenance.textContent = "Trace unavailable";
    traceContent.replaceChildren(
      card(
        "Local preview",
        "Serve the docs directory",
        "Run: python3 -m http.server 8000 -d docs\nThen open http://localhost:8000",
      ),
    );
  }
}

choices.forEach((choice) => {
  choice.addEventListener("click", () => {
    choices.forEach((item) => item.classList.toggle("active", item === choice));
    if (!successfulTrace || !blockedTrace) return;
    choice.dataset.trace === "blocked" ? renderBlocked() : renderSuccessful();
  });
});

loadTraceData();

async function loadPreflight() {
  const stats = document.querySelector("#preflight-stats");
  const disclosure = document.querySelector("#preflight-disclosure");
  if (!stats || !disclosure) return;
  try {
    const response = await fetch("data/preflight-summary.json");
    const preflight = await response.json();
    const audit = preflight.gold_execution_audit;
    const coverage = `${((audit.succeeded_under_local_limits / audit.attempted) * 100).toFixed(1)}%`;
    const values = [
      [preflight.selected_examples, "Frozen examples"],
      [preflight.databases, "SQLite databases"],
      [coverage, "Local gold coverage"],
      [audit.truncated, "Result truncations"],
    ];
    const nodes = values.map(([value, label]) => {
      const item = document.createElement("div");
      item.className = "preflight-stat";
      const strong = document.createElement("strong");
      strong.textContent = value;
      const caption = document.createElement("span");
      caption.textContent = label;
      item.append(strong, caption);
      return item;
    });
    stats.replaceChildren(...nodes);
    disclosure.textContent = preflight.disclosure;
  } catch (error) {
    stats.textContent = "Preflight artifact unavailable.";
  }
}

loadPreflight();
