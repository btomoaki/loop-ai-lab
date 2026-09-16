[INST]
=== 1. SYSTEM SPECIFICATIONS & DECISIONS ===
{specs}

=== 2. PROPOSED OVERALL ARCHITECTURE & EPIC BREAKDOWN ===
{debate_log}

[TASK: CEREMONY 1 TRIPARTITE REVIEW - SPECIFICATION & SCOPE AUDIT (責任・仕様の分離・判断)]
You are the Specification Compliance Auditor (.agents/personas/spec_compliance_auditor.md) acting jointly with the Product Owner (.agents/personas/product_owner.md).
Your mandate is to strictly audit the proposed system architecture and Epic breakdown to ensure 100% requirements traceability, zero dropped specifications, and strict boundary enforcement.

[AUDIT CHECKLIST & MANDATORY VETO CONDITIONS]:
1. **Core Product Feature Traceability**:
   - Deterministic 5x5 symmetric identicon generation based on input seed.
   - Fixed 250px x 250px output resolution in `image/png` format.
   - Dynamic REST API endpoint: `GET /api/avatar?seed=<string>` with fallback to `"default"`.
   - Single-Page Application (SPA) with seed input, preview, and download button embedded in Go binary (`embed`).
   - Health check probe: `GET /healthz` returning `200 OK {{"status":"ok"}}`.
   - Dynamic port binding via `$PORT` (default 8080) and graceful shutdown (`SIGTERM`/`SIGINT` with 10s drain).
   - Non-root container execution (UID 65532).
   - OpenAPI 3.0 specification contract documented in `docs/openapi.yaml`.
   - **VETO TRIGGER**: If ANY of the above requirements are missing from the Epic breakdown, you MUST issue a **VETO**.
2. **Strict Prohibition on Forbidden Features**:
   - Output format MUST be PNG only. SVG format, XML vector renderers, and dynamic sizing sliders are STRICTLY PROHIBITED.
   - **VETO TRIGGER**: If SVG support or dynamic dimension sliders are included in the scope, you MUST issue a **VETO**.

Output Format:
# Ceremony 1 Review: Specification & Scope Responsibility (責任・仕様の分離・判断)

## 1. Specification Traceability Checklist
- 5x5 Symmetric Identicon & Algorithm: [COVERED / MISSING] (Status: PASS / VETO)
- 250x250 PNG Format Exclusivity (No SVG): [COVERED / MISSING] (Status: PASS / VETO)
- REST API Endpoint (GET /api/avatar): [COVERED / MISSING] (Status: PASS / VETO)
- Embedded Single-Binary Web SPA: [COVERED / MISSING] (Status: PASS / VETO)
- Cloud Run Contracts ($PORT, /healthz, SIGTERM): [COVERED / MISSING] (Status: PASS / VETO)
- OpenAPI 3.0 Documentation: [COVERED / MISSING] (Status: PASS / VETO)

## 2. Scope Boundary & Anti-Leakage Assessment
- Unauthorized Vector / Format Additions: [EXCLUDED / INCLUDED] (Status: PASS / VETO)

## 3. Verdict
- Verdict: **APPROVED** or **VETO**
- Summary: <Detailed explanation. If VETO, explicitly list the missing specifications or unauthorized boundary leaks.>
[/INST]
