#!/usr/bin/env python3
"""
Backfill canonical scores for all users with health_metric_summaries data.

Usage:
    python scripts/backfill_canonical_scores.py                # all users
    python scripts/backfill_canonical_scores.py --user UUID     # single user
    python scripts/backfill_canonical_scores.py --dry-run       # preview only
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv("apps/mvp_api/.env")

from apps.mvp_api.dependencies.usage_gate import _supabase_get, _supabase_patch
from common.metrics.canonical_scores import compute_canonical_scores


async def backfill_user(user_id: str, dry_run: bool = False) -> int:
    """Compute and store canonical scores for a single user. Returns count."""
    rows = await _supabase_get(
        "health_metric_summaries",
        f"user_id=eq.{user_id}&select=metric_type,latest_value,personal_baseline,baseline_stddev",
    )
    if not rows:
        return 0

    updates = compute_canonical_scores(rows)
    if dry_run:
        for u in updates:
            print(f"  [DRY RUN] {u['metric_type']} → {u['canonical_metric']} = {u['canonical_score']}")
        return len(updates)

    for u in updates:
        await _supabase_patch(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&metric_type=eq.{u['metric_type']}",
            {"canonical_metric": u["canonical_metric"], "canonical_score": u["canonical_score"]},
        )
    return len(updates)


async def main():
    parser = argparse.ArgumentParser(description="Backfill canonical scores")
    parser.add_argument("--user", help="Single user UUID")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    if args.user:
        print(f"Backfilling user {args.user}...")
        count = await backfill_user(args.user, args.dry_run)
        print(f"  → {count} canonical scores {'would be ' if args.dry_run else ''}updated")
    else:
        # Get all distinct user_ids from summaries
        rows = await _supabase_get(
            "health_metric_summaries",
            "select=user_id&limit=1000",
        )
        user_ids = list({r["user_id"] for r in (rows or [])})
        print(f"Found {len(user_ids)} users with summaries")

        total = 0
        for uid in user_ids:
            count = await backfill_user(uid, args.dry_run)
            if count > 0:
                action = "would update" if args.dry_run else "updated"
                print(f"  {uid}: {count} scores {action}")
                total += count

        print(f"\nTotal: {total} canonical scores {'would be ' if args.dry_run else ''}updated across {len(user_ids)} users")


if __name__ == "__main__":
    asyncio.run(main())
