# gemini-web2api — Render deployment

This repository wraps the upstream Gemini Web to OpenAI-compatible proxy for Render.

## Render settings

- Runtime: Docker
- Dockerfile: `./Dockerfile`
- Health check path: `/health`
- Start command: provided by the Dockerfile

## Environment variables

Set these in Render → Environment. Never commit cookies or config files.

| Variable | Required | Purpose |
|---|---:|---|
| `API_KEY` | Yes | Render-generated client API key |
| `GEMINI_COOKIE` | For signed-in account routing | Cookie header exported from your own signed-in Gemini Web session |
| `GEMINI_DEFAULT_MODEL` | No | Defaults to `gemini-flash-lite` |
| `GEMINI_AUTH_USER` | No | Account index when the Gemini URL uses `/u/N/` |
| `GEMINI_XSRF_TOKEN` | No | Optional page XSRF token if required by your account/session |
| `GEMINI_BL` | No | Optional Gemini frontend build label override |
| `GEMINI_PROXY` | No | Optional outbound HTTP(S) proxy |
| `GEMINI_TEMPORARY_CHATS` | No | Set `true` to use temporary chats |

`GEMINI_COOKIE` accepts a single-line Cookie header, a JSON object with a `cookie` property, or a Netscape cookie export. Newlines are normalized before the value is sent upstream. The cookie is read from the environment at request time and is never written to the repository.

The wrapper advertises `gemini-flash-lite` and the compatibility alias `gemini-2.5-flash-lite`. Both select the upstream Flash-Lite mode/category; the alias does not guarantee a particular versioned backend model. Other model IDs are those defined by the upstream project's model mapping. Actual availability and routing remain controlled by Gemini Web and the signed-in account.

## API

Base URL: `https://YOUR-SERVICE.onrender.com/v1`

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

Example:

```bash
curl https://YOUR-SERVICE.onrender.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-flash-lite","messages":[{"role":"user","content":"Reply: Proxy working"}]}'
```

## Security

The repository previously tracked local cookie/config files. They are removed from the current branch and ignored going forward. Removing a file from the latest commit does not erase prior Git history or logs; revoke any previously exposed Google session and use a fresh cookie. Never send cookies or API keys in chat or commit them to Git.
