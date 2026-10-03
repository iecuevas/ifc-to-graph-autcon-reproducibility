#!/usr/bin/env python3
"""Revision-added CLI helper for running the preserved IFC-to-Graph builder.

This helper was created for the AUTCON reproducibility release and is not claimed
as part of the original experimental implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.neo4j_driver import Neo4jDriver
from ingest.ifc_graph.graph_builder import IfcGraphBuilder


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert one IFC file to the preserved IFC-to-Graph Neo4j representation.")
    p.add_argument("ifc_file", type=Path, help="Path to an IFC-SPF .ifc file")
    p.add_argument("--uri", default=os.getenv("NEO4J_URI", "bolt://localhost:7687"), help="Neo4j URI (default: NEO4J_URI or bolt://localhost:7687)")
    p.add_argument("--user", default=os.getenv("NEO4J_USER", "neo4j"), help="Neo4j user (default: NEO4J_USER or neo4j)")
    p.add_argument("--project-id", default="", help="Optional project namespace")
    p.add_argument("--ifc-name", default="", help="Optional IFC namespace; defaults to filename stem")
    p.add_argument("--clear-ifc", action="store_true", help="Delete an existing graph for the same project/IFC namespace before conversion")
    p.add_argument("--json-out", type=Path, default=None, help="Optional JSON file for returned timing/count metrics")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.ifc_file.exists() or not args.ifc_file.is_file():
        raise FileNotFoundError(args.ifc_file)
    if args.ifc_file.suffix.lower() != ".ifc":
        raise ValueError(f"Expected a .ifc file, got: {args.ifc_file}")

    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("NEO4J_PASSWORD is not set. Supply it through the environment; do not commit credentials.")

    resolved_name = args.ifc_name or args.ifc_file.stem
    driver = Neo4jDriver(args.uri, args.user, password)
    try:
        if args.clear_ifc:
            IfcGraphBuilder.clear_ifc(driver, args.project_id, resolved_name)
        builder = IfcGraphBuilder(driver)
        metrics = builder.build_graph(str(args.ifc_file), project_id=args.project_id, ifc_name=resolved_name) or {}
    finally:
        driver.close()

    print(json.dumps(metrics, indent=2, sort_keys=True))
    if args.json_out:
        args.json_out.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
