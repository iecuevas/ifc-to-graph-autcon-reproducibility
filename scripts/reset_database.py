#!/usr/bin/env python3
"""Revision-added Neo4j reset helper.

The preserved source snapshot's Neo4jDriver.clear_database() deletes nodes and
relationships and clears query caches, but does not drop indexes/constraints.
This helper optionally drops user schema objects so the documented cold-start
protocol can be enacted explicitly during future reproduction attempts.

It was NOT part of the preserved experimental source snapshot.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.neo4j_driver import Neo4jDriver


def qname(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Destructively reset the Neo4j database used for IFC-to-Graph reproduction.")
    p.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    p.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"))
    p.add_argument("--drop-schema", action="store_true", help="Also drop user constraints and non-lookup indexes")
    p.add_argument("--confirm", required=True, help="Must be exactly DELETE_ALL_DATA")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.confirm != "DELETE_ALL_DATA":
        raise RuntimeError("Refusing destructive reset: --confirm must equal DELETE_ALL_DATA")
    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("NEO4J_PASSWORD is not set")

    driver = Neo4jDriver(args.uri, args.user, password)
    try:
        driver.clear_database()
        if args.drop_schema:
            constraints = driver.execute_query("SHOW CONSTRAINTS YIELD name RETURN name") or []
            for row in constraints:
                driver.execute_query(f"DROP CONSTRAINT {qname(row['name'])} IF EXISTS")

            indexes = driver.execute_query(
                "SHOW INDEXES YIELD name, type, owningConstraint "
                "WHERE owningConstraint IS NULL AND type <> 'LOOKUP' RETURN name"
            ) or []
            for row in indexes:
                driver.execute_query(f"DROP INDEX {qname(row['name'])} IF EXISTS")
        print("Database reset completed.")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
