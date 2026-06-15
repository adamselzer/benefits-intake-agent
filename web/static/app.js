const money = (n) => "$" + Math.round(Number(n)).toLocaleString();
const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

const ROUTE = {
  clear_eligible: { cls: "eligible", label: "Clear — eligible", icon: "ti-circle-check" },
  clear_ineligible: { cls: "ineligible", label: "Clear — ineligible", icon: "ti-circle-minus" },
  needs_human_review: { cls: "review", label: "Needs your review", icon: "ti-user-search" },
};
const FIN = [
  { key: "earned", name: "Monthly earned income", field: "monthly_earned_income", doc: "Pay stub" },
  { key: "rent", name: "Monthly rent", field: "monthly_rent", doc: "Lease" },
  { key: "utilities", name: "Monthly utilities", field: "monthly_utilities", doc: "Utility bill" },
];

let visionAvailable = false;
let current = null; // last rendered result, for the copy action

async function init() {
  const status = await (await fetch("/api/status")).json();
  visionAvailable = status.vision_available;
  const v = document.getElementById("vision");
  v.disabled = !visionAvailable;
  v.parentElement.title = visionAvailable
    ? "Use Claude vision extraction"
    : "Set ANTHROPIC_API_KEY in .env to enable vision";

  const cases = await (await fetch("/api/cases")).json();
  const review = cases.filter((c) => c.route === "needs_human_review");
  const cleared = cases.filter((c) => c.route !== "needs_human_review");
  const ul = document.getElementById("cases");
  ul.innerHTML = group("Needs review", review) + group("Cleared", cleared);
  ul.querySelectorAll(".case-row").forEach((el) =>
    el.addEventListener("click", () => select(el, el.dataset.id))
  );
}

function group(title, arr) {
  if (!arr.length) return "";
  const head = `<li class="q-group">${title}<span class="q-count">${arr.length}</span></li>`;
  return head + arr.map(rowHtml).join("");
}

function routeDot(route) {
  if (route === "needs_human_review") return "review";
  if (route === "clear_ineligible") return "ineligible";
  return "eligible";
}
function rowHtml(c) {
  const num = c.id.replace(/-(clearly_|missing_|conflicting_|near_).*/, "");
  const tag = c.scenario.replace(/_/g, " ").replace("clearly ", "").replace(" document", "");
  return `<li class="case-row" data-id="${c.id}">
    <span style="display:flex;align-items:center;gap:9px;min-width:0">
      <span class="dot ${routeDot(c.route)}"></span><span class="case-id">${esc(num)}</span>
    </span>
    <span class="case-tag">${esc(tag)}</span>
  </li>`;
}

async function select(el, id) {
  document.querySelectorAll(".case-row").forEach((r) => r.classList.remove("active"));
  el.classList.add("active");
  document.getElementById("stage").innerHTML = `<div class="loading">Running the agent graph…</div>`;
  const vision = document.getElementById("vision").checked;
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: id, vision }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "run failed");
    render(await res.json());
  } catch (e) {
    document.getElementById("stage").innerHTML = `<div class="loading">${esc(e.message)}</div>`;
  }
}

function actionItems(d) {
  const items = [];
  (d.conflicts || []).forEach((c) =>
    items.push({ icon: "ti-arrows-diff", text: `Reconcile ${esc(c.field.replace(/_/g, " "))}: the application says ${money(c.stated_value)}, the document shows ${money(c.extracted_value)}.` })
  );
  (d.missing_documents || []).forEach((m) => {
    const m2 = m.replace(/^(\w+)\s*\((.*)\)$/, (_, doc, why) => `Request a ${doc.replace(/_/g, " ")} — ${why}.`);
    items.push({ icon: "ti-file-alert", text: esc(m2) });
  });
  (d.flags || []).filter((f) => f.startsWith("low_confidence")).forEach((f) =>
    items.push({ icon: "ti-eye-exclamation", text: `Re-check ${esc(f.replace("low_confidence:", "").trim())} — low extraction confidence.` })
  );
  return items;
}

function evidenceField(spec, d) {
  const found = (d.extracted || []).find((e) => e.name === spec.field);
  if (found && typeof found.value === "number") {
    return `<div class="ev-row"><span class="ev-name">${spec.name}</span><span class="ev-val">${money(found.value)}</span><span class="chip"><i class="ti ti-file-text"></i> ${spec.doc}</span></div>`;
  }
  const stated = d.validated && d.validated[spec.key];
  if (stated) {
    return `<div class="ev-row"><span class="ev-name">${spec.name}</span><span class="ev-val warn">unverified</span><span class="chip warn"><i class="ti ti-alert-triangle"></i> stated ${money(stated)}, no ${spec.doc.toLowerCase()}</span></div>`;
  }
  return "";
}

function render(d) {
  current = d;
  const r = ROUTE[d.route] || ROUTE.needs_human_review;
  const sc = d.screen || {};
  const comp = sc.computed || {};
  const eligible = sc.snap_decision === "eligible";
  const items = actionItems(d);
  const cites = (sc.snap_citations || []).map((c) => `<span class="chip mono">${esc(c.label)}</span>`).join("");

  const claims = d.claims || [];
  const fromDoc = claims.filter((c) => c.basis.startsWith("document")).length;
  const fromRule = claims.filter((c) => c.basis.startsWith("rule")).length;
  const unverified = claims.filter((c) => c.basis.startsWith("application")).length;
  const provSummary = [fromDoc && `${fromDoc} from documents`, fromRule && `${fromRule} from rules`, unverified && `${unverified} unverified`]
    .filter(Boolean).join(" · ");

  const action = d.route === "needs_human_review"
    ? `<section class="action review">
        <div class="action-head"><i class="ti ti-clipboard-check"></i><h3>What you need to resolve</h3><span class="count">${items.length}</span></div>
        ${items.map((it) => `<div class="action-item"><i class="ti ${it.icon}"></i><span>${it.text}</span></div>`).join("")}
        <div class="action-bar"><button class="btn btn-primary" id="copyNote"><i class="ti ti-copy"></i> Copy case note</button><span class="hint">Paste into the case record</span></div>
      </section>`
    : `<section class="action clear">
        <div class="action-head"><i class="ti ti-circle-check"></i><h3>Nothing to resolve</h3></div>
        <p class="action-note">Every fact is document-verified and consistent. Recommended: <b>${eligible ? "clear-eligible" : "clear-ineligible"}</b>. Confirm to proceed.</p>
        <div class="action-bar"><button class="btn btn-primary" id="copyNote"><i class="ti ti-copy"></i> Copy case note</button><span class="hint">Paste into the case record</span></div>
      </section>`;

  document.getElementById("stage").innerHTML = `
    <div class="r-head">
      <div>
        <div class="r-eyebrow">Caseworker recommendation · household of ${d.household_size} · ${esc(d.extractor)} extraction</div>
        <div class="route-headline ${r.cls}"><i class="ti ${r.icon}"></i> ${r.label}</div>
      </div>
      <div class="r-case">${esc(d.case_id)}</div>
    </div>
    <p class="route-rationale">${esc(d.summary)}</p>

    ${action}

    <section class="determination">
      <h3>Determination <span class="det-sub">the basis a caseworker, auditor, or court can inspect</span></h3>
      <div class="det-row">
        <span class="verdict ${eligible ? "" : "ineligible"}"><i class="ti ${eligible ? "ti-check" : "ti-minus"}"></i> ${eligible ? "Eligible" : "Ineligible"}${d.route === "needs_human_review" ? ", on stated income" : ""}</span>
        <span class="det-calc">net <b>${money(comp.net_income || 0)}</b> ${eligible ? "≤" : ">"} <b>${money(comp.net_income_limit || 0)}</b> limit · household of ${d.household_size}</span>
      </div>
      <div class="cites">${cites}</div>
      <div class="ruleset">ruleset <b>${esc((sc.ruleset_version || {}).version || "")}</b> · via rules-as-code-mcp</div>
    </section>

    <details class="evidence">
      <summary><i class="ti ti-chevron-right ev-chevron"></i> Evidence &amp; sourcing<span class="ev-sum">${provSummary}</span></summary>
      <div class="evidence-body">
        <h4>What the model read</h4>
        ${FIN.map((s) => evidenceField(s, d)).join("")}
        <h4>Provenance — every claim traces to a source</h4>
        <div class="ledger">${claims.map((c) => {
          const b = c.basis.startsWith("rule") ? "rule" : c.basis.startsWith("document") ? "document" : "stated";
          return `<div class="claim"><span class="claim-text">${esc(c.claim)}</span><span class="basis ${b}">${esc(c.basis)}</span></div>`;
        }).join("")}</div>
      </div>
    </details>

    <div class="foot"><span>determination via rules-as-code-mcp</span><span>Synthetic data · no PII · never auto-denies</span></div>
  `;

  const copy = document.getElementById("copyNote");
  if (copy) copy.addEventListener("click", copyNote);
}

function copyNote() {
  const d = current;
  if (!d) return;
  const lines = [
    `Case ${d.case_id} — household of ${d.household_size}`,
    `Recommendation: ${(ROUTE[d.route] || {}).label}`,
    d.summary,
    "",
    "Facts:",
    ...(d.claims || []).map((c) => `  - ${c.claim} (${c.basis})`),
  ];
  const items = actionItems(d).map((i) => i.text.replace(/<[^>]+>/g, ""));
  if (items.length) lines.push("", "To resolve:", ...items.map((t) => `  - ${t}`));
  navigator.clipboard.writeText(lines.join("\n")).then(() => {
    const b = document.getElementById("copyNote");
    b.innerHTML = '<i class="ti ti-check"></i> Copied';
    setTimeout(() => (b.innerHTML = '<i class="ti ti-copy"></i> Copy case note'), 1600);
  });
}

document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
    document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.id !== "panel-" + t.dataset.tab));
  })
);

init();
