# Composition transcript — intake agent calling the rules core over MCP

The intake agent's screen step delegates to the `rules-as-code-mcp` server over stdio. Below: a household sent to that server and the cited determination it returns.

Connected to **rules-as-code-mcp** (caseworker scope).

## screen_programs
```json
{
  "disclaimer": "Screening only: a coarse signal of likely eligibility, not a determination. No personal information is collected or stored. Run check_program_eligibility for a full, cited determination.",
  "household_size": 3,
  "screens": [
    {
      "program": "SNAP",
      "likely_eligible": true,
      "basis": "Household of 3 is financially eligible for SNAP under snap-mi-fy2026.1: net income $1007 is at or below the $2221 limit.",
      "citation": {
        "authority": "7 CFR",
        "section": "273.9(a)(2)",
        "title": "Net income eligibility standard: monthly net income at or below 100% of the federal poverty guidelines.",
        "url": "https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-C/part-273/subpart-D/section-273.9",
        "label": "7 CFR 273.9(a)(2)"
      }
    },
    {
      "program": "Medicaid (adult expansion, income screen only)",
      "likely_eligible": true,
      "basis": "Gross monthly income $2100 is at or below the 138% FPL screen of $3065 for a household of 3. Income screen only; not a MAGI determination.",
      "citation": {
        "authority": "42 CFR",
        "section": "435.119",
        "title": "Medicaid eligibility for the adult expansion group at or below 138% of the federal poverty level (MAGI-based, simplified income screen only).",
        "url": "https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-C/part-435",
        "label": "42 CFR 435.119"
      }
    }
  ]
}
```

## check_program_eligibility (determination + rule trace + citation)
```json
{
  "determination_id": "snap-f6d7aff7586fa76e",
  "program": "SNAP",
  "decision": "eligible",
  "summary": "Household of 3 is financially eligible for SNAP under snap-mi-fy2026.1: net income $1007 is at or below the $2221 limit.",
  "household_size": 3,
  "computed": {
    "gross_income": 2100.0,
    "earned_income": 2100.0,
    "unearned_income": 0.0,
    "earned_income_deduction": 420.0,
    "standard_deduction": 209.0,
    "dependent_care_deduction": 0.0,
    "child_support_deduction": 0.0,
    "medical_deduction": 0.0,
    "adjusted_income": 1471.0,
    "excess_shelter_deduction": 464.5,
    "net_income": 1006.5,
    "gross_income_limit": 4442.0,
    "net_income_limit": 2221.0
  },
  "rule_trace": [
    {
      "rule_id": "snap.bbce",
      "description": "Broad-based categorical eligibility in effect: asset test waived; gross income limit raised to 200% of poverty.",
      "inputs": {
        "bbce_enabled": true,
        "bbce_gross_percent": 200
      },
      "result": "asset_test=waived",
      "passed": null,
      "citation": {
        "authority": "Michigan BEM",
        "section": "213",
        "title": "FAP categorical eligibility: broad-based categorical eligibility raises the gross income limit to 200% of poverty and waives the asset test for most food assistance groups.",
        "url": "https://dhhs.michigan.gov/OLMWEB/EX/BP/Public/BEM/213.pdf",
        "label": "Michigan BEM 213"
      }
    },
    {
      "rule_id": "snap.gross_income_test",
      "description": "Gross monthly income must be at or below the 200% of poverty limit for the household size.",
      "inputs": {
        "gross_income": 2100,
        "limit": 4442,
        "household_size": 3
      },
      "result": "gross $2100 <= $4442",
      "passed": true,
      "citation": {
      
```

**Decision:** eligible — every rule in the trace carries a policy citation, so the agent's recommendation is auditable.
