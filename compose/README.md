Compose env usage

This repository uses two compose files under `compose/`:

- `compose.dev.yaml` - development stack (uses `../.env.local` for environment values)
- `compose.prod.yaml` - production-like stack (uses `../.env` for secrets)

Notes:
- Do NOT commit `.env` or `.env.local`. Keep `.env.example` in the repo with placeholders.
- To run development compose with explicit env file:

```bash
# from repository root
docker compose --env-file .env.local -f compose/compose.dev.yaml up -d --build
```

- To run production compose (root .env must exist and contain production secrets):

```bash
docker compose --env-file .env -f compose/compose.prod.yaml up -d --build
```

If you prefer the compose files to reference different filenames, edit the `env_file` entries in `compose/*.yaml` accordingly.
