# Da Vinci DTR Payer Server (FastAPI)

FHIR R4 payer server targeting [HL7 Da Vinci DTR v2.2.0](https://hl7.org/fhir/us/davinci-dtr/2.2.0/) conformance validation with the [Inferno DTR Payer Server v2.2.0 test kit](https://github.com/inferno-framework/davinci-dtr-test-kit).

**Phase 1** — Discovery **1.01** (`GET /fhir/metadata`).

**Phase 2** — Backend Services **2.1** (SMART well-known) and **2.2** (SMART backend services token).

## Requirements

- Python 3.11+
- Official DTR Payer Service CapabilityStatement (vendored from HL7):
  https://hl7.org/fhir/us/davinci-dtr/2.2.0/CapabilityStatement-dtr-payer-service.json

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
cd /path/to/dtr_server
uv sync
```

Dev dependencies are in `[dependency-groups]`; `uv sync` installs them by default.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_FHIR_BASE_URL` | `http://localhost:8000/fhir` | FHIR base URL advertised in `CapabilityStatement.implementation.url` (must match Inferno input) |
| `SMART_TRUSTED_JWKS_JSON` | _(empty)_ | Optional extra JSON JWKS (merged with fetched keys) |
| `SMART_TRUSTED_JWKS_PATH` | `trusted_jwks.json` (if present) | File path alternative to `SMART_TRUSTED_JWKS_JSON` |
| `SMART_JWKS_URLS` | Inferno SMART STU2 JWKS URL | Comma-separated JWKS URLs to fetch and trust (default includes [Inferno's JWKS](https://inferno.healthit.gov/suites/custom/smart_stu2/.well-known/jwks.json)) |
| `SMART_ALLOW_UNVERIFIED_CLIENT_ASSERTION` | `false` | If `true`, skip signature verification (claims only; local testing only) |
| `SMART_EXTRA_TOKEN_AUDIENCES` | _(empty)_ | Comma-separated extra accepted JWT `aud` values if Inferno's `aud` differs slightly from your `token_endpoint` |
| `SMART_DEFAULT_SCOPE` | `system/*.rs` | Scope returned when the token request omits `scope` |
| `SMART_ACCESS_TOKEN_LIFETIME_SECONDS` | `300` | `expires_in` for issued access tokens |

## Run

```bash
uv run uvicorn dtr_server.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify metadata:

```bash
curl -sS http://localhost:8000/fhir/metadata | jq '.kind, .instantiates, .rest[0].resource[].type'
```

Verify SMART discovery:

```bash
curl -sS http://localhost:8000/fhir/.well-known/smart-configuration | jq .
```

## Tests

```bash
uv run pytest
```

## Inferno v2.2.0 — Discovery 1.01

1. Start this server (reachable from the Inferno host).
2. Open the **Da Vinci DTR Payer Server Test Suite v2.2.0** in Inferno.
3. Set **Payer FHIR Server Base Url** to your FHIR base, e.g. `http://localhost:8000/fhir`.
4. Run the **Discovery** group only.

Test 1.01 checks that the CapabilityStatement returned from `{base}/metadata` declares:

- `Questionnaire`: `$questionnaire-package`, `$next-question`, `$log-questionnaire-errors`
- `ValueSet`: `$expand`

under a `rest` entry with `mode: server`.

## Inferno v2.2.0 — Backend Services (2.1 & 2.2)

### Prerequisites

1. **JWKS** — By default the server fetches Inferno's public keys from `SMART_JWKS_URLS`. You can still add local keys via `SMART_TRUSTED_JWKS_JSON` / `SMART_TRUSTED_JWKS_PATH`. For quick local debugging only, set `SMART_ALLOW_UNVERIFIED_CLIENT_ASSERTION=true` (does not validate the signature).

2. **TLS (test 2.2.01)** — Inferno checks that the **token endpoint** uses TLS 1.2+. Local `http://localhost` will not pass 2.2.01. Use HTTPS (reverse proxy, tunnel, or deployment with TLS) and set `PUBLIC_FHIR_BASE_URL` to the HTTPS FHIR base so `token_endpoint` and JWT `aud` align.

### Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET {base}/.well-known/smart-configuration` | SMART discovery (2.1.01–2.1.02) |
| `POST {base}/auth/token` | Backend services client credentials + JWT assertion (2.2.02–2.2.06) |

In Inferno **Backend Services Credentials**, enable **use discovery** so `token_url` and `auth_url` are read from well-known.

### What the tests check

- **2.1.01** — `200` + `application/json` from well-known URL under the FHIR base.
- **2.1.02** — Required fields: `authorization_endpoint`, `token_endpoint`, `capabilities`, `grant_types_supported` (includes `authorization_code`), `code_challenge_methods_supported` (`S256`, not `plain`). No `issuer` unless `sso-openid-connect` is listed.
- **2.2.02** — Invalid `grant_type` → HTTP `400`.
- **2.2.03 / 2.2.04** — Invalid `client_assertion_type` or JWT → HTTP `400` or `401`.
- **2.2.05 / 2.2.06** — Valid assertion → `200` JSON with `access_token`, `token_type`=`bearer`, `expires_in`, `scope`.

## Architecture

- `domain` — ports (protocols)
- `application` — use cases
- `infrastructure` — HL7 artifacts, SMART JWKS validation, token issuance
- `presentation` — FastAPI routers (`/fhir`, `/fhir/auth`, well-known)

DTR FHIR operations (`$questionnaire-package`, etc.) remain stubbed with `501 OperationOutcome` until later phases.
