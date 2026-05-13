"""CLI entry point: hunter scan|digest|score"""
import asyncio
import os
from pathlib import Path

import typer
from rich.console import Console
from dotenv import load_dotenv

from .models import Source
from .scrapers import scan_all
from .scorer import Scorer
from .digest import format_markdown


load_dotenv()
app = typer.Typer()
console = Console()


@app.command()
def scan(output: Path = Path("digest.md"), backend: str = "mimo", top_n: int = 10):
    """Run full scan: scrape + score + write markdown digest."""
    candidates = asyncio.run(scan_all([Source.GALXE, Source.LAYER3]))
    console.print(f"[green]Scraped {len(candidates)} candidates[/green]")

    scorer = Scorer(backend=backend)
    scores = []
    for c in candidates:
        s = scorer.score(c)
        if s is not None:
            scores.append(s)
    console.print(f"[green]Scored {len(scores)} candidates[/green]")

    md = format_markdown(scores, top_n=top_n)
    output.write_text(md)
    console.print(f"[bold green]Digest written to {output}[/bold green]")


@app.command()
def digest(input: Path = Path("digest.md"), to_telegram: bool = False):
    """Re-emit the digest, optionally pushing to Telegram."""
    md = input.read_text()
    console.print(md)
    if to_telegram:
        import httpx
        token = os.environ["TELEGRAM_BOT_TOKEN"]
        chat = os.environ["TELEGRAM_CHAT_ID"]
        for chunk_start in range(0, len(md), 3500):
            chunk = md[chunk_start : chunk_start + 3500]
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat, "text": chunk, "parse_mode": "Markdown"},
                timeout=30,
            )


if __name__ == "__main__":
    app()
