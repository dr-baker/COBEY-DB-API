"""JSON utilities for serialization/deserialization."""
from datetime import datetime
import json

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def dumps(obj, **kwargs):
    """Wrapper around json.dumps that uses our custom encoder."""
    return json.dumps(obj, cls=DateTimeEncoder, **kwargs) 