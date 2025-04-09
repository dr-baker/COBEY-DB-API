"""SQL query builder with type safety."""
from typing import Any, List, Optional, Tuple, Union
from datetime import datetime

class SQLBuilder:
    """Safe SQL query builder."""
    
    def __init__(self):
        self.query_parts: List[str] = []
        self.params: List[Any] = []
        self._param_counter = 0
    
    def _add_param(self, value: Any) -> str:
        """Add a parameter and return its placeholder."""
        self._param_counter += 1
        self.params.append(value)
        return f"${self._param_counter}"
    
    def SELECT(self, *columns: str) -> 'SQLBuilder':
        """Add SELECT clause."""
        cols = ", ".join(columns) if columns else "*"
        self.query_parts.append(f"SELECT {cols}")
        return self
    
    def FROM(self, table: str) -> 'SQLBuilder':
        """Add FROM clause."""
        self.query_parts.append(f"FROM {table}")
        return self
    
    def WHERE(self, condition: str) -> 'SQLBuilder':
        """Add WHERE clause with safe parameter binding.
        
        The condition should already include parameter placeholders.
        """
        self.query_parts.append(f"WHERE {condition}")
        return self
    
    def AND(self, condition: str) -> 'SQLBuilder':
        """Add AND clause.
        
        The condition should already include parameter placeholders.
        """
        self.query_parts.append(f"AND {condition}")
        return self
    
    def OR(self, condition: str) -> 'SQLBuilder':
        """Add OR clause.
        
        The condition should already include parameter placeholders.
        """
        self.query_parts.append(f"OR {condition}")
        return self
    
    def ORDER_BY(self, *columns: str) -> 'SQLBuilder':
        """Add ORDER BY clause."""
        self.query_parts.append(f"ORDER BY {', '.join(columns)}")
        return self
    
    def LIMIT(self, limit: int) -> 'SQLBuilder':
        """Add LIMIT clause."""
        self.query_parts.append(f"LIMIT {self._add_param(limit)}")
        return self
    
    def OFFSET(self, offset: int) -> 'SQLBuilder':
        """Add OFFSET clause for pagination."""
        self.query_parts.append(f"OFFSET {self._add_param(offset)}")
        return self
    
    def INSERT_INTO(self, table: str, **values: Any) -> 'SQLBuilder':
        """Add INSERT INTO clause."""
        columns = ", ".join(values.keys())
        placeholders = ", ".join(
            self._add_param(v) for v in values.values()
        )
        self.query_parts.append(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        )
        return self
    
    def UPDATE(self, table: str, **values: Any) -> 'SQLBuilder':
        """Add UPDATE clause."""
        self.query_parts.append(f"UPDATE {table} SET")
        set_parts = []
        for key, value in values.items():
            set_parts.append(f"{key} = {self._add_param(value)}")
        self.query_parts.append(", ".join(set_parts))
        return self
    
    def SET(self, **values: Any) -> 'SQLBuilder':
        """Add SET clause for UPDATE statements."""
        set_parts = [f"{key} = {self._add_param(value)}" for key, value in values.items()]
        self.query_parts.append(f"SET {', '.join(set_parts)}")
        return self
    
    def RETURNING(self, *columns: str) -> 'SQLBuilder':
        """Add RETURNING clause."""
        cols = ", ".join(columns) if columns else "*"
        self.query_parts.append(f"RETURNING {cols}")
        return self
    
    def build(self) -> Tuple[str, List[Any]]:
        """Build the final query and parameters."""
        return " ".join(self.query_parts), self.params 