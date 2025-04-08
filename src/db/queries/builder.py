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
    
    def WHERE(self, condition: str, *values: Any) -> 'SQLBuilder':
        """Add WHERE clause with safe parameter binding."""
        placeholders = [self._add_param(v) for v in values]
        self.query_parts.append(
            f"WHERE {condition.format(*placeholders)}"
        )
        return self
    
    def AND(self, condition: str, *values: Any) -> 'SQLBuilder':
        """Add AND clause."""
        placeholders = [self._add_param(v) for v in values]
        self.query_parts.append(
            f"AND {condition.format(*placeholders)}"
        )
        return self
    
    def OR(self, condition: str, *values: Any) -> 'SQLBuilder':
        """Add OR clause."""
        placeholders = [self._add_param(v) for v in values]
        self.query_parts.append(
            f"OR {condition.format(*placeholders)}"
        )
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
    
    def RETURNING(self, *columns: str) -> 'SQLBuilder':
        """Add RETURNING clause."""
        cols = ", ".join(columns) if columns else "*"
        self.query_parts.append(f"RETURNING {cols}")
        return self
    
    def build(self) -> Tuple[str, List[Any]]:
        """Build the final query and parameters."""
        return " ".join(self.query_parts), self.params 