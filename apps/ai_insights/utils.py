import uuid
from sqlalchemy.inspection import inspect


def ensure_python_uuids(obj):
    """
    Convert all SQLAlchemy UUID fields on an object to Python uuid.UUID objects.
    This is needed for Pydantic's from_orm to work without schema errors.
    """
    if obj is None:
        return None
    mapper = inspect(obj.__class__)
    for column in mapper.columns:
        if hasattr(obj, column.name):
            value = getattr(obj, column.name)
            if str(column.type).lower().startswith("uuid") and value is not None and not isinstance(value, uuid.UUID):
                try:
                    setattr(obj, column.name, uuid.UUID(str(value)))
                except Exception:
                    pass  # If conversion fails, leave as is
    return obj 