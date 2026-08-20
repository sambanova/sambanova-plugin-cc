# Public mirror sync (Copybara)

This directory configures the one-way mirror of this plugin to its **public** repo:

```
internal:  sambanova/sambanova-marketplace : plugins/sambanova-plugin-cc/**   (source of truth)
public:    sambanova/sambanova-plugin-cc   : plugins/samba-plugin/**          (mirror, via PR)
```

- [`copy.bara.sky`](./copy.bara.sky) — *what* to sync (the Copybara recipe).
- [`../../../.github/workflows/sync-public.yml`](../../../.github/workflows/sync-public.yml) — *when* to sync:
  on push to `main` touching this plugin, a daily cron safety net, and a manual button.

The sync only ever **opens/updates a review PR** (`copybara/sync-main`) on the public repo.
**Publishing requires a human to merge that PR** — automation never publishes directly.

> Source of truth is internal. Do **not** hand-edit `plugins/samba-plugin/**` in the public
> repo; the next sync would revert it. Make changes here and let them flow out.

---

## One-time setup (before the first automated run)

1. **Token.** Create a fine-grained PAT (or GitHub App token) with:
   - read access to `sambanova/sambanova-marketplace` (origin), and
   - `contents: write` + `pull_requests: write` on `sambanova/sambanova-plugin-cc` (destination).

   Store it as an Actions secret named **`OSS_SYNC_TOKEN`** on this repo (or the org).

2. **Collaborator.** The public repo's `.github/workflows/close-prs.yml` auto-closes PRs from
   non-members. Add the token's identity (the sync bot/maintainer) as a **collaborator/member** of
   `sambanova/sambanova-plugin-cc`, or its sync PR will be auto-closed.

3. **Bootstrap the baseline (manual, once).** The public repo already has content and there is no
   `GitOrigin-RevId` baseline yet, so the very first sync needs `--force`. Run it by hand:

   ```bash
   export GH_TOKEN=<token-with-access-to-both-repos>
   printf 'https://x-access-token:%s@github.com\n' "$GH_TOKEN" > "$HOME/.git-credentials"

   # Dry run first — inspect the (large) first-time reconciliation diff:
   docker run --rm -it -e HOME=/root \
     -v "$HOME/.git-credentials":/root/.git-credentials:ro \
     -v "$PWD":/usr/src/app \
     google/copybara copybara \
       plugins/sambanova-plugin-cc/copybara/copy.bara.sky push_to_public --force --dry-run

   # Then for real (opens the first PR):
   docker run --rm -it -e HOME=/root \
     -v "$HOME/.git-credentials":/root/.git-credentials:ro \
     -v "$PWD":/usr/src/app \
     google/copybara copybara \
       plugins/sambanova-plugin-cc/copybara/copy.bara.sky push_to_public --force \
       --git-committer-name="SambaNova Sync Bot" \
       --git-committer-email="oss-bot@sambanovasystems.com"
   ```

   Review and **merge** that first PR. After it merges, the `GitOrigin-RevId` baseline lives on the
   public `main`, and all subsequent syncs are incremental and fully automated by the workflow
   (no `--force`).

> Expect the **first** PR to be large: the public mirror currently lags behind (script-based,
> v1.0.10) while internal is MCP-server based (v1.1.0). The first sync adds `mcp_server/`,
> `.mcp.json`, rewrites the skills, and removes the stale `cn/` / `scripts/` / `tools/` dirs.
> Also update the public-only `README.md` / `CONTRIBUTING.md` (which describe the old flow) when
> merging that first PR — Copybara does not touch files outside `plugins/samba-plugin/`.

---

## Day-to-day

Nothing to do. Merging a change into internal `main` under `plugins/sambanova-plugin-cc/**` triggers
the workflow, which refreshes the public sync PR. A maintainer reviews and merges it to publish.

Validate the config after editing it:

```bash
docker run --rm -v "$PWD":/usr/src/app google/copybara \
  copybara validate plugins/sambanova-plugin-cc/copybara/copy.bara.sky
```

When the internal and public copies legitimately differ in text (e.g. an internal URL that must
become public), encode each difference as a `core.replace` in `copy.bara.sky` so the sync re-applies
it every run instead of reverting it.
