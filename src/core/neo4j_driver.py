from neo4j import GraphDatabase
from typing import Any, Dict, List, Optional

from core.logger import configure_logger


class Neo4jDriver:
    def __init__(self, uri: str, user: str, password: str, max_connection: int = 50):
        self._driver = GraphDatabase.driver(
            uri, 
            auth=(user, password), 
            max_connection_pool_size=max_connection,
            connection_acquisition_timeout=60
            )
        self._logger = configure_logger(self.__class__.__name__)
        self._verify_connection()
        
    def close(self) -> None:
        """Cierra las conexiones del driver de forma segura"""
        if self._driver:
            self._driver.close()
            self._logger.info("Neo4j driver closed")
            
    def _verify_connection(self) -> None:
        """Verifica la conexión con la base de datos"""
        try:
            self._driver.verify_connectivity()
            self._logger.info("Connection verified")      
        except Exception as e:
            self._logger.error(f"Connection failed: {str(e)}")
            raise
        
    def clear_database(self) -> None:
        """Elimina todos los nodos y relaciones de la base de datos, además de limpiar la caché"""
        queries = [
            "MATCH (n) DETACH DELETE n",
            "CALL db.clearQueryCaches()"
        ]
        try:
            with self._driver.session(database="neo4j") as session:
                for query in queries:
                    session.execute_write(lambda tx: tx.run(query))
            self._logger.warning("Database cleared and caches reset")
        except Exception as e:
            self._logger.error(f"Database clear failed: {str(e)}")
            raise
        
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        database: str = "neo4j"
    ) -> Any:
        """
        Ejecuta una consulta Cypher con parámetros
        Args:
            query: Consulta Cypher
            parameters: Parámetros de la consulta
            database: Base de datos objetivo
        Returns:
            Lista de resultados como diccionarios
        """
        try:
            with self._driver.session(database=database) as session:
                result = session.execute_write(
                    lambda tx: tx.run(query, parameters).data()
                )
                # self._logger.debug(f"Query executed: {query}")
                return result
        except Exception as e:
            self._logger.error(
                f"Query failed: {query}\nParameters: {parameters}",
                exc_info=True
            )
            raise
    def test_connection(self) -> bool:
        """Realiza una prueba de conexión con la base de datos"""
        try:
            with self._driver.session() as session:
                result = session.run("RETURN 1 AS test")
                return result.single()["test"] == 1
        except Exception as e:
            self._logger.error(f"Connection test failed: {str(e)}")
            return False
        
    def check_server_config(self) -> Dict[str, Any]:
        """Verifica la configuración del servidor Neo4j relacionada con la concurrencia"""
        query = """
        CALL dbms.listConfig() YIELD name, value 
        WHERE name CONTAINS 'thread' OR name CONTAINS 'connection' OR name CONTAINS 'pool'
        RETURN name, value
        """
        try:
            with self._driver.session() as session:
                result = session.run(query).data()
                return {item['name']: item['value'] for item in result}
        except Exception as e:
            self._logger.error(f"Server config check failed: {str(e)}")
            return {}
