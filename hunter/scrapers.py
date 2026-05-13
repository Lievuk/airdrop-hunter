"""Source scrapers. Each yields Candidates."""
import asyncio
from typing import AsyncIterator, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import Candidate, Source


GALXE_API = "https://graphigo.prd.galaxy.eco/query"
LAYER3_API = "https://api.layer3.xyz/v1/quests"
ZEALY_API = "https://api.zealy.io/communities"


class ScraperError(RuntimeError):
    pass


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_galxe(client: httpx.AsyncClient, limit: int = 50) -> List[Candidate]:
    query = """
    query Campaigns($limit: Int!) {
      campaigns(input: {first: $limit, listType: Newest}) {
        list { id name description thumbnail status startTime endTime
               space { name } }
      }
    }
    """
    r = await client.post(GALXE_API, json={"query": query, "variables": {"limit": limit}}, timeout=30)
    r.raise_for_status()
    items = r.json().get("data", {}).get("campaigns", {}).get("list", []) or []
    out = []
    for it in items:
        out.append(Candidate(
            source=Source.GALXE,
            project_name=(it.get("space") or {}).get("name", "Unknown"),
            campaign_id=it["id"],
            title=it.get("name", ""),
            summary=(it.get("description") or "")[:500],
            url=f"https://app.galxe.com/quest/{it['id']}",
            raw=it,
        ))
    return out


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def fetch_layer3(client: httpx.AsyncClient, limit: int = 50) -> List[Candidate]:
    r = await client.get(f"{LAYER3_API}?status=active&limit={limit}", timeout=30)
    r.raise_for_status()
    out = []
    for q in r.json().get("data", []):
        out.append(Candidate(
            source=Source.LAYER3,
            project_name=q.get("project", {}).get("name", "Unknown"),
            campaign_id=q["id"],
            title=q.get("title", ""),
            summary=(q.get("description") or "")[:500],
            url=f"https://layer3.xyz/quests/{q['id']}",
            chain=q.get("chain"),
            raw=q,
        ))
    return out


async def scan_all(sources: List[Source]) -> List[Candidate]:
    async with httpx.AsyncClient(headers={"User-Agent": "airdrop-hunter/0.1"}) as client:
        tasks = []
        if Source.GALXE in sources:
            tasks.append(fetch_galxe(client))
        if Source.LAYER3 in sources:
            tasks.append(fetch_layer3(client))
        results = await asyncio.gather(*tasks, return_exceptions=True)
    out: List[Candidate] = []
    for r in results:
        if isinstance(r, Exception):
            continue
        out.extend(r)
    return out
