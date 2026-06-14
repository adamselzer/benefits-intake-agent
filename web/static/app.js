const $ = (s, r = document) => r.querySelector(s);
const money = (n) => "$" + Math.round(Number(n)).toLocaleString();
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

const ROUTE = {
  clear_eligible: { cls: "eligible", label: "Clear — eligible", icon: "ti-check" },
  clear_ineligible: { cls: "ineligible", label: "Clear — ineligible", icon: "ti-minus" },
  needs_human_review: { cls: "review", label: "Needs human review", icon: "ti-user-search" },
};
const FIN = [
  { key: "earned", name: "Monthly earned income", field: "monthly_earned_income", doc: "Pay stub" },
  { key: "rent", name: "Monthly rent", field: "monthly_rent", doc: "Lease" },
  { key: "utilities", name: "Monthly utilities", field: "monthly_utilities", doc: "Utility bill" },
];
const FLOW = ["ingest", "extract", "validate", "screen", "route"];

let visionAvailable = false;

async function init() {
  const status = await (await fetch("/api/status")).json();
  visionAvailable = status.vision_available;
  const v = $("#vision");
  v.disabled = !visionAvailable;
  v.parentElement.title = visionAvailable
    ? "Use Claude vision extraction"
    : "Set ANTHROPIC_API_KEY in .env to enable vision";

  const cases = await (await fetch("/api/cases")).json();
  const ul = $("#cases");
  ul.innerHTML = cases.map(rowHtml).join("");
  ul.querySelectorAll(".case-row").forEach((el) =>
    el.addEventListener("click", () => select(el, el.dataset.id))
  );
}

function scenarioDot(s) {
  if (s.includes("ineligible")) return "ineligible";
  if (s.includes("missing") || s.includes("conflict")) return "review";
  return "eligible";
}
function rowHtml(c) {
  const tag = c.scenario.replace(/_/g, " ");
  return `<li class="case-row" data-id="${c.id}">
    <span style="display:flex;align-items:center;gap:9px;min-width:0">
      <span class="dot ${scenarioDot(c.scenario)}"></span>
      <span class="case-id">${esc(c.id.replace(/-(clearly_|missing_|conflicting_|near_).*/, ""))}</span>
    </span>
    <span class="case-tag">${esc(tag.replace("clearly ", "").replace(" document", ""))}</span>
  </li>`;
}

async function select(el, id) {
  document.querySelectorAll(".case-row").forEach((r) => r.classList.remove("active"));
  el.classList.add("active");
  $("#stage").innerHTML = `<div class="loading">Running the agent graph<span id="ell">…</span></div>`;
  const vision = $("#vision").checked;
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: id, vision }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "run failed");
    render(await res.json());
  } catch (e) {
    $("#stage").innerHTML = `<div class="loading">${esc(e.message)}</div>`;
  }
}

function extractedField(spec, data) {
  const found = (data.extracted || []).find((e) => e.name === spec.field);
  if (found && typeof found.value === "number") {
    const pct = Math.round(found.confidence * 100);
    return `<div class="field">
      <div class="field-top"><span class="field-name">${spec.name}</span><span class="field-val">${money(found.value)}</span></div>
      <div class="meter">
        <span class="bar"><i style="width:${pct}%"></i></span>
        <span class="conf">${found.confidence.toFixed(2)}</span>
        <span class="chip"><i class="ti ti-file-text"></i> ${spec.doc}</span>
      </div></div>`;
  }
  const stated = data.validated && data.validated[spec.key];
  if (stated) {
    return `<div class="field">
      <div class="field-top"><span class="field-name">${spec.name}</span><span class="field-val warn">unverified</span></div>
      <div class="meter"><span class="chip warn"><i class="ti ti-alert-triangle"></i> No ${spec.doc.toLowerCase()} — stated ${money(stated)} not confirmed</span></div>
    </div>`;
  }
  return "";
}

function render(d) {
  const r = ROUTE[d.route] || ROUTE.needs_human_review;
  const sc = d.screen || {};
  const comp = sc.computed || {};
  const eligible = sc.snap_decision === "eligible";
  const cites = (sc.snap_citations || []).map((c) => `<span class="chip mono">${esc(c.label)}</span>`).join("");
  const verdictLabel = eligible ? "Eligible, on stated income" : "Ineligible";

  const reviewItems = [];
  (d.conflicts || []).forEach((c) =>
    reviewItems.push(`<i class="ti ti-arrows-diff ic"></i> Conflict on ${esc(c.field)}: stated ${money(c.stated_value)} vs document ${money(c.extracted_value)}`)
  );
  (d.missing_documents || []).forEach((m) =>
    reviewItems.push(`<i class="ti ti-file-alert ic"></i> Verify ${esc(m)}`)
  );
  (d.flags || []).forEach((f) =>
    reviewItems.push(`<i class="ti ti-flag ic"></i> ${esc(f)}`)
  );

  const flow = FLOW.map((n, i) => {
    const boundary = n === "screen" ? " boundary" : "";
    const seg = i < FLOW.length - 1 ? '<span class="seg"></span>' : "";
    return `<span class="node${boundary}"><b>${i + 1}</b><span>${n}</span></span>${seg}`;
  }).join("");

  const claims = (d.claims || []).map((c) => {
    const b = c.basis.startsWith("rule") ? "rule" : c.basis.startsWith("document") ? "document" : "stated";
    return `<div class="claim"><span class="claim-text">${esc(c.claim)}</span><span class="basis ${b}">${esc(c.basis)}</span></div>`;
  }).join("");

  $("#stage").innerHTML = `
    <div class="r-head">
      <div>
        <div class="r-eyebrow">Caseworker recommendation · household of ${d.household_size} · ${esc(d.extractor)} extraction</div>
        <div class="r-case">${esc(d.case_id)}</div>
      </div>
      <span class="pill ${r.cls}"><i class="ti ${r.icon}"></i> ${r.label}</span>
    </div>
    <p class="r-summary">${esc(d.summary)}</p>

    <hr class="rule" />
    <div class="flow">${flow}</div>
    <hr class="rule" />

    <div class="tracks">
      <div>
        <div class="track-head"><i class="ti ti-eye" style="color:var(--muted)"></i><h3>What the model read</h3><span class="kind">extraction</span></div>
        ${FIN.map((s) => extractedField(s, d)).join("")}
      </div>
      <div>
        <div class="track-head"><i class="ti ti-gavel" style="color:var(--muted)"></i><h3>What the rules decided</h3><span class="kind">deterministic</span></div>
        <span class="verdict ${eligible ? "" : "ineligible"}"><i class="ti ${eligible ? "ti-check" : "ti-minus"}"></i> ${verdictLabel}</span>
        <p class="calc">Net monthly income <b>${money(comp.net_income || 0)}</b> ${eligible ? "is at or below" : "exceeds"} the <b>${money(comp.net_income_limit || 0)}</b> limit for a household of ${d.household_size}.</p>
        <div class="cites">${cites}</div>
        <div class="ruleset">ruleset <b>${esc((sc.ruleset_version || {}).version || "")}</b></div>
      </div>
    </div>

    ${reviewItems.length ? `<hr class="rule" /><div class="section-head"><i class="ti ti-clipboard-check" style="color:var(--muted)"></i><h3>Before a decision</h3></div>${reviewItems.map((t) => `<div class="review-item">${t}</div>`).join("")}` : ""}

    <hr class="rule" />
    <div class="section-head"><i class="ti ti-list-search" style="color:var(--muted)"></i><h3>Provenance — every claim traces to a source</h3></div>
    <div class="ledger">${claims}</div>

    <div class="foot"><span>determination via rules-as-code-mcp</span><span>Synthetic data · no PII · never auto-denies</span></div>
  `;
}

init();
