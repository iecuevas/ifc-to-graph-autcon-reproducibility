# Experimental protocol and timing boundary

This document distinguishes the study protocol reported by the manuscript from behavior that can be verified directly in the audited source snapshot. Where the archive cannot establish a historical detail, the repository does not infer or reconstruct it.

## Reported benchmark procedure

For each of the eight benchmark models, the manuscript records:

- five non-consecutive, non-parallel conversion runs;
- controlled cold-start preparation;
- graph data cleared before each run;
- operating-system cache clearing;
- machine restart;
- fixed node and relationship batch size of 10,000;
- reporting of mean, standard deviation (SD), and coefficient of variation (CV).

The earlier revision wording stated that indexes and constraints were also purged before each run. The audited source snapshot does not support that specific statement, so the manuscript was narrowed: it no longer claims that schema objects were dropped between runs.

## Source-supported pre-run clearing behavior

The supplied snapshot contains two relevant clearing mechanisms:

1. `IfcGraphBuilder.clear_ifc(...)` deletes `IfcEntity` and `IfcFile` nodes for a specified project/IFC namespace using `DETACH DELETE`.
2. `Neo4jDriver.clear_database()` deletes all graph nodes/relationships and calls `db.clearQueryCaches()`.

Neither preserved function drops indexes or constraints. Therefore, this repository documents graph-data/query-cache clearing behavior but does not represent schema-object removal as part of the verified historical implementation.

`scripts/reset_database.py` is a **revision-added** helper for future reproduction attempts. Its optional `--drop-schema` mode can remove user constraints and non-lookup indexes, but that option must not be described as part of the original benchmark protocol.

## Timing boundary verifiable in `graph_builder.py`

`IfcGraphBuilder.build_graph()` records the following timed stages:

1. `indexes_creation` - `_create_indexes_and_constraints()`;
2. `file_opening` - `ifcopenshell.open()`;
3. `schema_node_creation` - schema, project, and IFC-file node setup;
4. `entities_processing` - entity preprocessing plus node persistence;
5. `relationships_processing` - relationship extraction plus relationship persistence.

The returned `total_time` is the sum of those five floating-point stage times. It therefore begins **before IFC file opening**, with index/constraint preparation, and ends after relationship persistence.

Pre-run graph-data clearing, operating-system cache clearing, and machine restart are outside `total_time`.

## Index and constraint behavior during the timed routine

At the beginning of every `build_graph()` call, the preserved implementation executes `CREATE ... IF NOT EXISTS` for its required uniqueness constraint and indexes. The timing of that check/creation step is included in `indexes_creation`. The source does not establish that existing schema objects were dropped between benchmark runs.

## Batch behavior verifiable in source

- `IfcGraphBuilder.batch_size = 10000`.
- Node persistence uses parameterized `UNWIND $batch` and processes chunks of `self.batch_size`.
- Relationship persistence calls `apoc.periodic.iterate` with `batchSize: 10000` and `parallel: false`.
- No batch-size sensitivity analysis is implemented in the supplied snapshot.

## Raw timing data

The supplied repository snapshot contains no recoverable file with the 40 individual timing observations implied by 8 models x 5 runs. Consequently, this package includes the manuscript-reported aggregate statistics only. Raw runs are not reconstructed from mean/SD/CV.
