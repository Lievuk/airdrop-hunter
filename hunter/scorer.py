"""LLM-based scoring. Backend-agnostic: works with Anthropic, OpenAI, or local MiMo."""
import json
import os
from typing import Optional

from .models import Candidate, Score, Step


SCORER_SYSTEM = """You are an expert airdrop farmer scoring opportunities for ROI and risk.

For each candidate, output strict JSON with fields:
- roi_estimate_usd: float, expected dollar value if everything works
- effort_minutes: int, total minutes to complete all steps
- risk_score: float 0..10, where 10 = high chance of loss (rugpull, scam, illegal, KYC trap)
- sybil_resistance: float 0..10, where 10 = very hard to sybil (good signal that early users will be valued)
- confidence: float 0..1, how sure are you of these numbers
- rationale: string, 2-3 sentences explaining the score
- steps: array of {order, action, target, params, estimated_seconds}

Rules:
- If the project requires deposit > $50, reduce ROI by deposit and bump risk_score by 1.
- If KYC is required, mark risk_score >= 7 unless the operator is well-known (Coinbase, Kraken, Stripe).
- If the chain is unknown or not in [ethereum, base, arbitrum, optimism, polygon, solana, bsc], cap confidence at 0.4.
- Prefer concrete numbers over hedge words.
"""


class Scorer:
    def __init__(self, backend: str = "mimo"):
        self.backend = backend
        if backend == "mimo":
            from openai import OpenAI
            self.client = OpenAI(
                base_url=os.getenv("MIMO_API_BASE", "http://localhost:19911/v1"),
                api_key=os.getenv("MIMO_API_KEY", "no-auth"),
            )
            self.model = "mimo-v2.5-pro"
        elif backend == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
            self.model = "claude-sonnet-4"
        else:
            raise ValueError(f"unknown backend: {backend}")

    def score(self, c: Candidate) -> Optional[Score]:
        user = (
            f"Project: {c.project_name}\n"
            f"Title: {c.title}\n"
            f"Source: {c.source}\n"
            f"Chain: {c.chain or 'unknown'}\n"
            f"Summary: {c.summary}\n"
            f"Deposit: ${c.requires_deposit_usd}\n"
            f"KYC: {c.requires_kyc}\n"
            f"URL: {c.url}\n"
        )
        if self.backend == "mimo":
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCORER_SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            payload = resp.choices[0].message.content
        else:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=SCORER_SYSTEM,
                messages=[{"role": "user", "content": user}],
            )
            payload = resp.content[0].text

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None

        return Score(
            candidate=c,
            roi_estimate_usd=float(data.get("roi_estimate_usd", 0)),
            effort_minutes=int(data.get("effort_minutes", 0)),
            risk_score=float(data.get("risk_score", 5)),
            sybil_resistance=float(data.get("sybil_resistance", 5)),
            confidence=float(data.get("confidence", 0.5)),
            rationale=data.get("rationale", ""),
            steps=[Step(**s) for s in data.get("steps", [])],
        )
