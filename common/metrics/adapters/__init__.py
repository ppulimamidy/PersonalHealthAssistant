"""
Device adapters — map raw device data to canonical health metrics.

Each adapter handles one data source (e.g. Oura, Apple Health, Dexcom).
All adapters are auto-registered on import via the module-level
``AdapterRegistry.register(...)`` call at the bottom of each adapter file.

To add a new device:
    1. Create ``common/metrics/adapters/my_device_adapter.py``
    2. Subclass ``DeviceAdapter``, set ``source_name = "my_device"``
    3. Implement ``to_canonical(raw_day, date, user_baseline) -> list[NormalizedMetric]``
    4. Decorate the class with ``@AdapterRegistry.register``
    5. Import the module here so it registers at startup.
"""

from common.metrics.adapters.base import (
    AdapterRegistry,
    DeviceAdapter,
    NormalizedMetric,
)

# Import all adapters to trigger registration
from common.metrics.adapters import (  # noqa: F401
    oura_adapter,
    apple_health_adapter,
    health_connect_adapter,
    dexcom_adapter,
    whoop_adapter,
    garmin_adapter,
    fitbit_adapter,
)

__all__ = ["AdapterRegistry", "DeviceAdapter", "NormalizedMetric"]
