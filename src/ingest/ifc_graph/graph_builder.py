import ifcopenshell

from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, List, TypedDict, Set

from core.timer import stopwatch
from core.logger import configure_logger
from core.neo4j_driver import Neo4jDriver

import time 

ATTRIBUTES_TYPE = ["ENTITY INSTANCE", "AGGREGATE OF ENTITY INSTANCE", "DERIVED"]


# Estructura de un 'resource'.
class ResourceDict(TypedDict):
    uuid: str
    entity: int

# Estructura de una entidad que tiene 'resources'.
class EntityDict(TypedDict):
    id: str
    resources: Dict[str, ResourceDict]
    
class IfcGraphBuilder:
    def __init__(self, driver: Neo4jDriver):
        self.driver = driver
        self.count_nodes = 0
        self.count_relationships = 0
        self.node_cache: Dict[str, str] = {}
        self.node_cache_with_resources: Dict[int, EntityDict] = {}
        self.batch_buffer: List[Dict[str, Any]] = []
        self.relationship_buffer: List[Dict[str, Any]] = []
        self.batch_size = 10000
        self._logger = configure_logger(self.__class__.__name__)
        self.project_id: str = ""
        self.ifc_name: str = ""
        self._ns: str = ""

    @staticmethod
    def clear_ifc(driver: Neo4jDriver, project_id: str, ifc_name: str) -> None:
        """Elimina todos los nodos de un IFC específico dentro de un proyecto."""
        driver.execute_query(
            "MATCH (n:IfcEntity {project_id: $p, ifc_name: $i}) DETACH DELETE n",
            {"p": project_id, "i": ifc_name}
        )
        driver.execute_query(
            "MATCH (f:IfcFile {project_id: $p, ifc_name: $i}) DETACH DELETE f",
            {"p": project_id, "i": ifc_name}
        )
    
    @stopwatch
    def build_graph(self, ifc_file_path: str, project_id: str = "", ifc_name: str = "") -> None:
        """Construye un grafo a partir de un archivo IFC"""
        self.project_id = project_id
        self.ifc_name = ifc_name or Path(ifc_file_path).stem
        self._ns = f"{self.project_id}::{self.ifc_name}::" if self.project_id else f"{self.ifc_name}::"
        self._logger.info(f"Building graph from {ifc_file_path} [project={self.project_id}, ifc={self.ifc_name}]")
        times = {}
        
        try:
            start = time.time()
            self._create_indexes_and_constraints()
            times["indexes_creation"] = time.time() - start
            
            start = time.time()
            ifc_file = ifcopenshell.open(ifc_file_path)
            times["file_opening"] = time.time() - start
            
            start = time.time()
            schema_version = ifc_file.schema
            self._add_schema_node(schema_version)
            self._add_project_and_ifc_nodes(schema_version)
            times["schema_node_creation"] = time.time() - start
            
            start = time.time()
            self._preprocess_entities(ifc_file)
            self._insert_and_flush_batch_nodes()
            times["entities_processing"] = time.time() - start
            
            start = time.time()
            self._process_all_relationships(ifc_file)
            self._insert_and_flush_batch_relationships()
            times["relationships_processing"] = time.time() - start
            
            times["total_nodes"] = self.count_nodes
            times["total_relationships"] = self.count_relationships
            times["total_time"] = sum([v for k, v in times.items() if isinstance(v, float)])
            
            self._logger.info(f"Graph built times: {times}")
            return times
            
        except Exception as e:
            self._logger.error(f"Error building graph: {str(e)}", exc_info=True)
            raise
        
    def _create_indexes_and_constraints(self) -> None:
        """Crea los índices necesarios en la base de datos, mejorando la velocidad de las consultas"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:IfcEntity) REQUIRE n.id IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:IfcRoot) ON (n.GlobalId)",
            "CREATE INDEX IF NOT EXISTS FOR (n:IfcProduct) ON (n.Name)",
            "CREATE INDEX IF NOT EXISTS FOR (m:IfcMaterial) ON (m.Name)",
        ]

        # Indices compuestos (project_id, ifc_name): TODA consulta del pipeline filtra
        # por estos dos. Sin ellos, en una BD multi-proyecto cada query hace un scan
        # completo de la base (medido: 4.7M nodos -> query ancla IfcElement 1348ms;
        # con indice 84ms, 16x). Se indexan los labels ancla del SchemaRetriever y los
        # tipos de elemento mas consultados.
        _FILTER_INDEX_LABELS = [
            "IfcEntity", "IfcElement", "IfcSpatialStructureElement",
            "IfcBuildingStorey", "IfcPropertySet", "IfcWall", "IfcDoor",
            "IfcWindow", "IfcSlab", "IfcBeam", "IfcColumn", "IfcSpace",
            "IfcPipeSegment", "IfcPipeFitting",
        ]
        indexes += [
            f"CREATE INDEX idx_{lb}_pid_ifc IF NOT EXISTS FOR (n:{lb}) ON (n.project_id, n.ifc_name)"
            for lb in _FILTER_INDEX_LABELS
        ]

        for constraint in constraints:
            self.driver.execute_query(constraint)

        for index in indexes:
            self.driver.execute_query(index)

        self._logger.info("Indexes created")
        
    def _add_schema_node(self, schema_version: ifcopenshell.file.schema) -> None:
        schema_node_id = f"{self._ns}FILE_SCHEMA"
        self.node_cache[schema_node_id] = schema_node_id
        self.batch_buffer.append({
            "id": schema_node_id,
            "name": "FILE_SCHEMA",
            "labels": ["IfcSchema"],
            "properties": {"version": schema_version, "project_id": self.project_id, "ifc_name": self.ifc_name}
        })

    def _add_project_and_ifc_nodes(self, schema_version: str) -> None:
        """Crea nodos Project e IfcFile para indexar proyectos y modelos."""
        if self.project_id:
            self.driver.execute_query(
                "MERGE (p:Project {id: $id}) SET p.name = $id",
                {"id": self.project_id}
            )
        ifc_file_id = f"{self.project_id}::{self.ifc_name}" if self.project_id else self.ifc_name
        self.driver.execute_query("""
            MERGE (f:IfcFile {id: $id})
            SET f.ifc_name = $ifc_name, f.project_id = $project_id, f.schema = $schema
            WITH f
            MATCH (p:Project {id: $project_id})
            MERGE (p)-[:HAS_IFC]->(f)
        """ if self.project_id else """
            MERGE (f:IfcFile {id: $id})
            SET f.ifc_name = $ifc_name, f.project_id = $project_id, f.schema = $schema
        """, {"id": ifc_file_id, "ifc_name": self.ifc_name, "project_id": self.project_id, "schema": schema_version}
        )
        
    def _preprocess_entities(self, ifc_file: ifcopenshell.file) -> None:
        """
        Preprocesa todas las entidades para el cache de nodos.
        Además, crea los nodos en lotes, obteniendo las propiedades literales de las entidades.
        """

        entities = list(ifc_file.wrapped_data.entity_names())

        for idx, entity_id in enumerate(entities, 1):
            self.count_nodes += 1
            entity = ifc_file.by_id(entity_id)

            namespaced_id = f"{self._ns}{entity.id()}"
            self.node_cache[str(entity.id())] = namespaced_id
            self.node_cache_with_resources[entity.id()] = {
                'id': namespaced_id,
                'resources': {}
                }
            
            self._process_entity_nodes(str(entity_id), entity)
            self._preprocess_resource_entities(entity)
            
            if idx % self.batch_size == 0:
                self._insert_and_flush_batch_nodes()
                
    def _generate_uuid(self) -> str:
        """Genera un UUID único para cada nodo"""
        while True:
            resource_uuid = str(uuid4())
            if resource_uuid not in self.node_cache:
                break
        return resource_uuid
            
    def _preprocess_resource_entities(self, entity: ifcopenshell.entity_instance) -> None:
        """Preprocesa los recursos de una entidad para el cache"""
        for i in range(entity.__len__()):
            arg_value = entity.wrapped_data.get_argument(i)
            
            if arg_value is not None and entity[i]:
                arg_type = entity.wrapped_data.get_argument_type(i)
                
                if arg_type == "ENTITY INSTANCE":
                    if arg_value.id() == 0:
                        resource_uuid = self._generate_uuid()     
                        new_resource: ResourceDict = { 'uuid': resource_uuid, 'entity': entity[i] }
                        self.count_nodes += 1
                        self.node_cache[resource_uuid] = resource_uuid
                        self.node_cache_with_resources[entity.id()]['resources'][str(i)] = [new_resource]
                        self._process_entity_nodes(resource_uuid, entity[i])
                elif arg_type == "AGGREGATE OF ENTITY INSTANCE":
                    for sub_entity in entity[i]:
                        if sub_entity.id() == 0:
                            self.count_nodes += 1
                            resource_uuid = self._generate_uuid()     
                            new_resource: ResourceDict = { 'uuid': resource_uuid, 'entity': sub_entity }
                            self.node_cache[resource_uuid] = resource_uuid
                            
                            if str(i) not in self.node_cache_with_resources[entity.id()]['resources']:
                                self.node_cache_with_resources[entity.id()]['resources'][str(i)] = [new_resource]
                            else:
                                self.node_cache_with_resources[entity.id()]['resources'][str(i)].append(new_resource)
                                
                            self._process_entity_nodes(resource_uuid, sub_entity)

    def _process_entity_nodes(self, entity_id: str, entity: ifcopenshell.entity_instance) -> None:
        """Procesa una entidad individual para nodos"""
        node_data = self._create_node_data(entity_id, entity)
        self.batch_buffer.append(node_data)
        
    def _create_node_data(self, entity_id: str, entity: ifcopenshell.entity_instance) -> Dict[str, Any]:
        """Crea la estructura de datos para un nodo"""
        node_id = self.node_cache[entity_id]
        labels = list(self._get_entity_labels(entity))
        properties = self._get_entity_properties(entity)
        
        return {
            "id": node_id,
            "labels": labels,
            "properties": properties
        }

    def _get_entity_labels(self, entity: ifcopenshell.entity_instance) -> Set[str]:
        """Obtiene las labels jerárquicas de la entidad"""
        try:
            labels = {entity.is_a()}     
            
            declaration = entity.wrapped_data.declaration()
            if declaration is None:
                return labels
            
            declaration = declaration.as_entity()
            
            # supertypes
            results = []
            while declaration is not None:
                declaration = declaration.supertype()
                if declaration:
                    results.append(declaration)
                
            labels.update(map(lambda st: st.name(), results))
            return labels
        except Exception as e:
            entity_id = getattr(entity, 'id', 'Unknown ID')
            self._logger.error(f"Error getting labels for entity {entity_id} | {entity}: {str(e)}", exc_info=True)
            return {entity.is_a()} if hasattr(entity, 'is_a') else set()

    def _get_entity_properties(self, entity: ifcopenshell.entity_instance) -> Dict[str, Any]:
        """Extrae propiedades literales de la entidad"""
        try:
            properties = {"ifc_type": entity.is_a(), "project_id": self.project_id, "ifc_name": self.ifc_name}
            for i in range(entity.__len__()):
                try:
                    arg_type = entity.wrapped_data.get_argument_type(i)
                    if arg_type not in ATTRIBUTES_TYPE:
                        key = entity.wrapped_data.get_argument_name(i)
                        properties[key] = entity.wrapped_data.get_argument(i)
                except Exception as attr_error:
                    self._logger.warning(f"Error getting {i} properties for entity {entity}: {str(attr_error)}", exc_info=True)
            return properties
        except Exception as e:
            self._logger.error(f"General error getting properties for entity {entity}: {str(e)}", exc_info=True)
            return {}

    def _insert_and_flush_batch_nodes(self) -> None:
        """Inserta nodos en lotes para mejorar rendimiento"""
        if self.batch_buffer:
            # Verificamos duplicados en el lote antes de enviar
            # ids = [node["id"] for node in self.batch_buffer]
            # duplicate_ids = set([id for id in ids if ids.count(id) > 1])
            # nodes_duplicates = [node for node in self.batch_buffer if node["id"] in duplicate_ids]
            
            # if duplicate_ids:
            #     self._logger.warning(f"Detected {len(duplicate_ids)} duplicate IDs in batch: {list(duplicate_ids)}")
            #     self._logger.warning(f"Duplicate nodes: {nodes_duplicates}")
                
            # query = """
            # CALL apoc.periodic.iterate(
            #     "UNWIND $batch AS node RETURN node",
            #     "MERGE (n:IfcEntity {id: node.id})
            #     SET n += node.properties
            #     WITH n, node.labels AS labels
            #     CALL apoc.create.addLabels(n, labels) 
            #     YIELD node
            #     RETURN count(node)",
            #     {batchSize: 10000, parallel: true, concurrency: 4, retries: 3, iterateList: true, params: {batch: $batch}}
            # ) 
            # """
            # self.driver.execute_query(query, {"batch": self.batch_buffer})
            # if result and len(result) > 0:
            #     self.monitor_execution_progress(result[0])
            #     print(f"Results: {result[0]}")
            
            query = """
                UNWIND $batch AS node
                MERGE (n:IfcEntity {id: node.id})
                SET n += node.properties
                WITH n, node.labels AS labels
                CALL apoc.create.addLabels(n, labels) 
                YIELD node
                RETURN count(node)
            """
            for i in range(0, len(self.batch_buffer), self.batch_size):
                batch = self.batch_buffer[i:i + self.batch_size]
                self.driver.execute_query(query, {"batch": batch}) 
            
            self.batch_buffer.clear()
            self._logger.info(f"Processed {self.count_nodes} nodes")    

    def _process_all_relationships(self, ifc_file: ifcopenshell.file) -> None:
        """Procesa todas las relaciones en lotes"""
        entities = list(ifc_file.wrapped_data.entity_names())
        
        for idx, entity_id in enumerate(entities, 1):
            entity = ifc_file.by_id(entity_id)
            self._process_entity_relationships(entity, ifc_file)
            
            if idx % self.batch_size == 0:
                self._insert_and_flush_batch_relationships()

    def _process_entity_relationships(self, entity: ifcopenshell.entity_instance, ifc_file: ifcopenshell.file) -> None:
        """Procesa las relaciones de una entidad"""
        try:
            source_id = self.node_cache_with_resources[entity.id()]["id"]
            
            # Relaciones directas
            for i in range(entity.__len__()):
                try:
                    if entity[i]:
                        arg_type = entity.wrapped_data.get_argument_type(i)
                        rel_name = entity.wrapped_data.get_argument_name(i)
                        
                        if arg_type == "ENTITY INSTANCE":
                            target = entity[i]
                            target_id = str(target.id())
                            if self.node_cache_with_resources[entity.id()]["resources"].get(str(i)):
                                target_id = self.node_cache_with_resources[entity.id()]["resources"][str(i)][0]["uuid"]                           
                            
                            if self._should_skip_relationship(entity, target, target_id):
                                continue
                            else:
                                self._add_relationship(source_id, rel_name, target_id)
                            
                        elif arg_type == "AGGREGATE OF ENTITY INSTANCE":
                            if self.node_cache_with_resources[entity.id()]["resources"].get(str(i)):
                                for res in self.node_cache_with_resources[entity.id()]["resources"][str(i)]:
                                    self._add_relationship(source_id, rel_name, res["uuid"])
                            for sub_entity in entity[i]:
                                target_id = str(sub_entity.id())
                                
                                if target_id != "0":
                                    self._add_relationship(source_id, rel_name, target_id)
                                
                except Exception as rel_error:
                    self._logger.error(f"Error processing relationship {i} for entity {entity}: {str(rel_error)}", exc_info=True)
            
            # Relaciones inversas
            for rel_name in entity.wrapped_data.get_inverse_attribute_names():
                try:
                    if entity.wrapped_data.get_inverse(rel_name):
                        inverse_relations = entity.wrapped_data.get_inverse(rel_name)       
                        for wrapped_rel_entity in inverse_relations:
                            rel_entity = ifc_file.by_id(wrapped_rel_entity.id())
                            self._add_relationship(source_id, rel_name, str(rel_entity.id()))
                except Exception as inv_error:
                    self._logger.error(f"Error processing inverse relationship {rel_name} for entity {entity}: {str(inv_error)}", exc_info=True)
                    
        except Exception as e:
            self._logger.error(f"Critic error processing relationships for entity {entity}: {str(e)}", exc_info=True)

    def _add_relationship(self, source_id: str, rel_type: str, target_id: str) -> None:
        """Agrega una relación al buffer"""
        relationship = {
            "source_id": source_id,
            "target_id": self.node_cache.get(target_id, target_id),
            "rel_type": rel_type.upper()
        }
        self.relationship_buffer.append(relationship)
        self.count_relationships += 1
        
    def monitor_execution_progress(self, stats):
        """Monitoriza y registra el progreso de ejecución de los lotes"""
        if stats.get('failedBatches', 0) > 0:
            self._logger.warning(f"Failed batches: {stats['failedBatches']}")
            self._logger.warning(f"Failed operations: {stats.get('failedOperations', 0)}")
            self._logger.warning(f"Retries performed: {stats.get('retries', 0)}")
        
        success_rate = (stats.get('batches', 0) - stats.get('failedBatches', 0)) / max(stats.get('batches', 1), 1) * 100
        self._logger.info(f"Success rate: {success_rate:.2f}%")
        self._logger.info(f"Operations: {stats.get('committedOperations', 0)}")
        self._logger.info(f"Time taken: {stats.get('timeTaken', 0)} ms")
        
        return stats

    def _insert_and_flush_batch_relationships(self) -> None:
        """Envía un lote de relaciones a Neo4j"""
        if self.relationship_buffer:
            # Verificamos duplicados en el lote antes de enviar, ignorar si son rel_type: POINTS
            
            # ids = [rel["source_id"] + rel["target_id"] for rel in self.relationship_buffer]
            # duplicate_ids = set([id for id in ids if ids.count(id) > 1])
            # relationships_duplicates = [rel for rel in self.relationship_buffer if rel["source_id"] + rel["target_id"] in duplicate_ids]
            
            # # quitar los POINTS de la lista de duplicados
            # relationships_duplicates = [rel for rel in relationships_duplicates if rel["rel_type"] != "POINTS"]
            
            # if duplicate_ids:
            #     self._logger.warning(f"Detected {len(duplicate_ids)} duplicate IDs in batch: {list(duplicate_ids)}")
            #     self._logger.warning(f"Duplicate relationships: {relationships_duplicates}")
            
            # query = """
            # CALL apoc.periodic.iterate(
            #     "UNWIND $batch AS rel_data RETURN rel_data",
            #     "MATCH (a:IfcEntity {id: rel_data.source_id}), (b:IfcEntity {id: rel_data.target_id})
            #     CALL apoc.create.relationship(a, rel_data.rel_type, {}, b) YIELD rel
            #     RETURN count(rel)",
            #     {batchSize: 10000, parallel: true, concurrency: 8, retries: 5, iterateList: true, params: {batch: $batch}}
            # ) 
            # """
            query = """
            CALL apoc.periodic.iterate(
                "UNWIND $batch AS rel_data RETURN rel_data",
                "MATCH (a:IfcEntity {id: rel_data.source_id}), (b:IfcEntity {id: rel_data.target_id})
                CALL apoc.create.relationship(a, rel_data.rel_type, {}, b) YIELD rel
                RETURN count(rel)",
                {batchSize: 10000, parallel: false, params: {batch: $batch}}
            ) 
            """
            self.driver.execute_query(query, {"batch": self.relationship_buffer})
            # if result and len(result) > 0:
            #     self.monitor_execution_progress(result[0])
            self.relationship_buffer.clear()
            self._logger.info(f"Processed {self.count_relationships} relationships")

    def _should_skip_relationship(self, entity: ifcopenshell.entity_instance, target: ifcopenshell.entity_instance, target_id: str) -> bool:
        """Determina si una relación debe ser omitida"""
        try:
            if target.is_a() in ["IfcOwnerHistory"] and entity.is_a() != "IfcProject":
                return True
            if target_id not in self.node_cache:
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error checking relationship for entity {entity}: {str(e)}", exc_info=True)
            return True
