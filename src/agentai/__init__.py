"""Cross-Industry Voice DataGuard Python package.

This package is organized using clean architecture principles.
- `core`: domain entities, use cases, and abstract ports.
- `adapters`: inbound and outbound adapters that implement the core ports.
- `config`: centralized configuration and environment loading.
- `shared`: reusable utilities, exceptions, and value objects.
"""

__all__ = [
    "core",
    "adapters",
    "config",
    "shared",
]
