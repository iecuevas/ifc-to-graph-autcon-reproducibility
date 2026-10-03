# Audited parser / graph-builder behavior

The statements below are based on direct inspection of the preserved `src/ingest/ifc_graph/graph_builder.py` file from source snapshot `b7c821ec50f8be67e3cd82ca08dd67c707701e55`.

## Entity labels and inheritance

For each runtime IFC entity, the builder starts with `entity.is_a()` and traverses successive schema supertypes through `declaration.supertype()`. Those class names are added as Neo4j labels.

## Literal properties

For every argument, the builder checks IfcOpenShell's runtime `get_argument_type(i)`. Arguments classified as `ENTITY INSTANCE`, `AGGREGATE OF ENTITY INSTANCE`, or `DERIVED` are excluded from literal node properties. Other arguments are stored using the IFC argument name as the property key.

## Direct entity references

Arguments classified at runtime as `ENTITY INSTANCE` become graph relationships named after the IFC argument. Referenced non-resource entities are resolved through the node cache.

## Aggregate entity references

Arguments classified as `AGGREGATE OF ENTITY INSTANCE` are iterated and converted into separate relationships. Repeated relationship instances can therefore be emitted separately.

The relationship record contains only `source_id`, `target_id`, and `rel_type`. No ordinal/index position is stored. Consequently, repeated-reference multiplicity does **not** demonstrate preservation of the original ordering of an IFC aggregate.

## Anonymous/resource instances

Referenced instances with `id() == 0` are assigned generated UUID strings, converted to graph nodes, and connected through the corresponding IFC argument relationship.

## Inverse relationships

The builder iterates `get_inverse_attribute_names()` and resolves each inverse reference through `get_inverse(rel_name)`, creating relationships using the inverse attribute name.

## DERIVED arguments

`DERIVED` is excluded from literal properties. There is no separate relationship-processing branch for arguments classified as `DERIVED`.

## EXPRESS SELECT

The audited builder contains **no dedicated schema-level SELECT resolver**. Handling depends on the runtime argument classification exposed by IfcOpenShell. The source therefore does not support a broader claim that every EXPRESS SELECT alternative is explicitly resolved by custom parser logic.

## TrueNorth

There is no special-case branch for `TrueNorth`. Any such value follows the same IfcOpenShell runtime-type handling as other arguments.

## IfcOwnerHistory

Direct relationships to `IfcOwnerHistory` are skipped unless the source entity is `IfcProject`, matching the simplification implemented in the published IFC-Graph pathway.

## Validation boundary

This code audit establishes implementation behavior; it does not constitute canonical semantic/property/topological equivalence testing across all IFC constructs and schema versions.
