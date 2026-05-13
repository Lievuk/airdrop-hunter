"""Format scored candidates into a digest (markdown or Telegram)."""
from typing import List
from .models import Score


def format_markdown(scores: List[Score], top_n: int = 10) -> str:
    ranked = sorted(scores, key=lambda s: s.roi_estimate_usd / max(s.effort_minutes, 1), reverse=True)[:top_n]
    out = ["# Daily Airdrop Digest\n"]
    for i, s in enumerate(ranked, 1):
        out.append(
            f"## {i}. {s.candidate.project_name} — ${s.roi_estimate_usd:.0f} / {s.effort_minutes}min\n"
            f"- **Risk**: {s.risk_score:.1f}/10 | **Sybil resistance**: {s.sybil_resistance:.1f}/10 | "
            f"**Confidence**: {s.confidence:.0%}\n"
            f"- {s.rationale}\n"
            f"- [Open]({s.candidate.url})\n"
            f"- Steps:\n"
            + "\n".join(f"  {st.order}. {st.action} → {st.target} ({st.estimated_seconds}s)" for st in s.steps)
            + "\n"
        )
    return "\n".join(out)
