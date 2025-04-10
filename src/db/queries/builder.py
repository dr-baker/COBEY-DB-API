"""SQL query builder for safe and efficient query construction.

This module provides a SQLBuilder class that helps construct SQL queries safely
with proper parameter binding to prevent SQL injection.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

class SQLBuilder:
    """Builds SQL queries with proper parameter binding."""
    
    def __init__(self):
        self.sql = ""
        self.params: List[Any] = []
        self._has_where = False
    
    @classmethod
    def select(cls, table: str) -> 'SQLBuilder':
        """Create a SELECT query builder."""
        builder = cls()
        builder.sql = f"SELECT * FROM {table}"
        return builder
    
    @classmethod
    def insert(cls, table: str, data: Dict[str, Any]) -> 'SQLBuilder':
        """Create an INSERT query builder."""
        builder = cls()
        if not data:
            raise ValueError("No data provided for INSERT")
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(data))])
        builder.sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"
        builder.params = list(data.values())
        return builder
    
    @classmethod
    def update(cls, table: str, data: Dict[str, Any]) -> 'SQLBuilder':
        """Create an UPDATE query builder."""
        builder = cls()
        if not data:
            raise ValueError("No data provided for UPDATE")
            
        sets = ", ".join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
        builder.sql = f"UPDATE {table} SET {sets}"
        builder.params = list(data.values())
        return builder
    
    @classmethod
    def delete(cls, table: str) -> 'SQLBuilder':
        """Create a DELETE query builder."""
        builder = cls()
        builder.sql = f"DELETE FROM {table}"
        return builder
    
    def where(self, condition: str) -> 'SQLBuilder':
        """
        Add a WHERE clause.
        
        Args:
            condition: SQL condition (e.g., "column = $1")
        """
        if not self._has_where:
            self.sql += f" WHERE {condition}"
            self._has_where = True
        else:
            self.sql += f" AND {condition}"
        return self
    
    def and_where(self, condition: str) -> 'SQLBuilder':
        """Add an AND condition to the WHERE clause."""
        if not self._has_where:
            return self.where(condition)
        self.sql += f" AND {condition}"
        return self
        
    def or_where(self, condition: str) -> 'SQLBuilder':
        """Add an OR condition to the WHERE clause."""
        if not self._has_where:
            return self.where(condition)
        self.sql += f" OR {condition}"
        return self
    
    def order_by(self, column: str, direction: str = "ASC") -> 'SQLBuilder':
        """Add an ORDER BY clause."""
        direction = direction.upper()
        if direction not in ("ASC", "DESC"):
            direction = "ASC"
        self.sql += f" ORDER BY {column} {direction}"
        return self
    
    def limit(self, limit: int) -> 'SQLBuilder':
        """Add a LIMIT clause."""
        self.sql += f" LIMIT {limit}"
        return self
    
    def offset(self, offset: int) -> 'SQLBuilder':
        """Add an OFFSET clause."""
        self.sql += f" OFFSET {offset}"
        return self
        
    def returning(self, columns: str = "*") -> 'SQLBuilder':
        """Add a RETURNING clause."""
        if " RETURNING " not in self.sql:
            self.sql += f" RETURNING {columns}"
        return self
        
    def build(self) -> Tuple[str, List[Any]]:
        """Build the final query and parameters."""
        return self.sql, self.params 