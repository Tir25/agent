"""
Sovereign Desktop - App Package

This is the refactored modular architecture following SOLID principles:

- app/interfaces/  : Abstract Base Classes (Contracts)
- app/services/    : Concrete implementations
- app/core/        : Central logic (Dispatcher, State)
- app/utils/       : Shared helpers (Result, Logging)
"""

__version__ = "2.0.0"
__all__ = ["interfaces", "services", "core", "utils"]
