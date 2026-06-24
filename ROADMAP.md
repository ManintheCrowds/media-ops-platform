# Roadmap — media-ops-platform (CaptionPipeline + Platform API)

## Near term

- [x] Public repo visibility after security review ([GH-PF-04](https://github.com/ManintheCrowds/MiscRepos/blob/main/docs/portfolio/GITHUB_PUBLIC_AUDIT_2026-06.md)) — done 2026-06-04; verified 2026-06-23
- [ ] CaptionPipeline portfolio Grafana reliability screenshot under `portfolio/assets/diagrams/grafana-reliability.png` (PF-REPO-2; homelab stack or archived capture — see [docs/portfolio/README.md](docs/portfolio/README.md))
- [ ] Platform API OpenAPI published with stable `/docs` URL in production compose

## Medium term

- [x] Coverage gate back to 70% on platform-api tests (78.98% local, 457 passed — 2026-06-24 Session A)
- [ ] Dependabot + branch protection on `main`
- [ ] Case-study export sync with Ghost canonical hub (PUB-9)

## Non-goals (this repo)

- Client identifiers or production credentials in git
- Private operator harness dumps (MiscRepos / local-only workspaces)
