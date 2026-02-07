# Python Version Isolation Decision - Device Data Service

## Decision Made: 2024-12-XX

### Problem
The device-data service encountered SQLAlchemy schema configuration errors when running with Python 3.13. The error was:
```
sqlalchemy.exc.ArgumentError: 'SchemaItem' object, such as a 'Column' or a 'Constraint' expected, got {'schema': 'device_data'}
```

### Root Cause
- Python 3.13 is not yet fully compatible with many scientific Python packages (pandas, numpy, scipy)
- SQLAlchemy 1.4.51 works correctly with Python 3.11 but has compatibility issues with Python 3.13
- The `__table_args__` tuple format with schema configuration requires specific SQLAlchemy version compatibility

### Solution: Isolated Python Version Downgrade
Instead of downgrading Python for all services, we isolated the change to only the device-data service:

1. **Container Isolation**: The device-data service Dockerfile already uses `FROM python:3.11-slim`
2. **Dependency Pinning**: SQLAlchemy is pinned to version 1.4.51 in `requirements.txt`
3. **No Impact on Other Services**: Other services continue to use Python 3.13

### Benefits
- ✅ Minimal impact on the overall system
- ✅ Device-data service works correctly with SQLAlchemy 1.4.51
- ✅ Other services maintain Python 3.13 compatibility
- ✅ Easy to upgrade individual services when Python 3.13 compatibility improves

### Technical Details
- **Device Data Service**: Python 3.11 + SQLAlchemy 1.4.51
- **Other Services**: Python 3.13 + Latest compatible SQLAlchemy versions
- **Container**: Isolated via Docker containerization

### Future Considerations
- Monitor Python 3.13 compatibility with scientific packages
- Consider upgrading device-data service to Python 3.13 when pandas/numpy/scipy support is stable
- Document any other services that may need similar isolation

### Files Modified
- `apps/device_data/requirements.txt` - Pinned SQLAlchemy to 1.4.51
- `apps/device_data/PYTHON_VERSION_DECISION.md` - This documentation file
- `apps/device_data/Dockerfile` - Already using Python 3.11 (no changes needed)
