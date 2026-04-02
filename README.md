# airdrop-hunter

Multi-source airdrop discovery and scoring agent. Scrapes Galxe, Layer3, Zealy, and curated Twitter/X handles. Scores each opportunity by expected ROI, effort, and risk using an LLM. Drafts a step-by-step walkthrough so you can execute or feed it into a Playwright runner.

## Why

Airdrop farming is a research problem disguised as a clicking problem. The clicking is mechanical; the research — which campaigns are real, which are sybil-trapped, which already had their snapshot — is what wastes time. This agent collapses that research into a daily 10-minute review.

## What it does

```
[Scrapers] ──► [Normalizer] ──► [LLM scorer] ──► [Walkthrough drafter] ──► [Telegram digest]
   │
   ├── Galxe campaigns (REST)
   ├── Layer3 quests (REST)
   ├── Zealy communities (REST)
   ├── Twitter/X list (Nitter mirror or X API)
   └── Curated source list (CryptoRank, AirdropAlert, DeFiLlama)
```

Each candidate gets a score:

| Field | Description |
|---|---|
| `roi_estimate_usd` | LLM estimate based on similar past airdrops, project funding, partner list |
| `effort_minutes` | Sum of estimated time for each step |
| `risk_score` | 0–10. Considers contract approval scope, KYC requirement, deposit amount |
| `sybil_resistance` | Signals: address-bound, captcha, hardware-attested |
| `deadline_utc` | Scraped or inferred |
| `confidence` | Calibration score from the scoring LLM |

The walkthrough drafter then produces a numbered playbook a human can follow or a Playwright agent can execute.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
python -m hunter.cli scan --output digest.md
python -m hunter.cli digest --to-telegram
```

## Config

`.env`:

```ini
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
ANTHROPIC_API_KEY=xxx     # or set MIMO_API_KEY for the MiMo backend
MIMO_API_BASE=http://localhost:19911/v1
SCRAPER_USER_AGENT=Mozilla/5.0 ...
```

## Why MiMo

The scoring step runs hundreds of candidates per scan. At Anthropic prices, a daily scan costs roughly USD 4–8 just on triage. MiMo's reported reasoning quality at lower per-token cost would let me drop that to under USD 0.50 per day, which makes the agent economical to run for community shared deployments rather than just my own machine.

## License

MIT.
