# Infrastructure and Credentials

## What you need

| Item | Needed from | Phase | Notes |
|---|---|---|---|
| GitHub repository | You / team org | 0 | Private to start. Prefer a team/organization account so it outlives any one person. |
| Python 3.11+ | Local / HiPerGator | 0 | `pip install -e ".[dev]"` |
| **NaviGator Toolkit API key** | UF IT, self-service | 2 | Create at `https://api.ai.it.ufl.edu/ui` with GatorLink. Personal keys last 1 year. |
| PubApps instance + port | UF Research Computing | 3 | Team already deploys here. |
| Service-style API key for the deployed app | UF IT (Help Portal) | 3 | Ask whether a team/service key is available so production doesn't depend on a personal key. |
| Facility price/requirement tables | ICBR (or other cores) | 1 | Current prices, input requirements, sample-sheet format, turnaround. |
| pandoc | Container image | 1 | For DOCX/PDF export. |

No other paid APIs are required. ENCODE standards are encoded into the rulebook by hand (they change rarely); no ENCODE API key is needed.

## NaviGator Toolkit notes

- OpenAI-compatible base URL: `https://api.ai.it.ufl.edu/v1/`. Use the `openai` Python SDK with `base_url` set.
- Use `chat/completions` with tools/function calling. Do not rely on the Responses API being fully supported for every model.
- List models available to your key: `GET /v1/models`. Model access is set per key.
- Test function-calling reliability per model before choosing one (Phase 2, step 13).
- Model access errors may come back as HTTP 401 rather than 404; handle both.

## Secrets handling

- Never commit keys. Copy `.env.example` to `.env` (git-ignored).
- In PubApps, inject secrets as environment variables at container start.
- The backend is the only component that talks to the LLM; the browser never sees the key.

## Deployment shape (Phase 3)

```
Browser ──HTTPS──▶ PubApps (container)
                    ├── FastAPI (uvicorn)  ── serves API + built frontend
                    ├── SQLite volume      ── saved designs, logs (no PHI)
                    └── outbound ──▶ NaviGator Toolkit API
```

One container is enough at Cancer Institute scale.

## Logging

Log conversations (minus anything user-flagged as sensitive) and final design states. These drive rulebook improvement and beta metrics. State the logging in the UI.
