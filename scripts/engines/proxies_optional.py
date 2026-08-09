#!/usr/bin/env python3
"""Optional proxies facade.

Provides a single import point for platform adapters. When engines.proxies
is available the real implementations are used; otherwise safe no-op
fallbacks are returned. This makes the soft-dependency explicit and
prevents silent behavioural drift across renderers.
"""

from __future__ import annotations

from typing import Any, List

_HAS_PROXIES = False

try:
    from engines.proxies import (  # noqa: F401
        EXTERNAL_RESOURCE_INTERVAL,
        clash_inline_proxies,
        clash_proxy_providers,
        enabled_nodes,
        enabled_subscriptions,
        load_providers,
        provider_names,
    )
    _HAS_PROXIES = True
except Exception:  # pragma: no cover - defensive fallback
    EXTERNAL_RESOURCE_INTERVAL = 7 * 24 * 60 * 60

    def load_providers() -> dict:
        return {}

    def clash_proxy_providers(data: Any = None) -> dict:
        return {}

    def clash_inline_proxies(data: Any = None) -> List[dict]:
        return []

    def provider_names(data: Any = None) -> List[str]:
        return []

    def enabled_subscriptions(data: Any = None) -> List[dict]:
        return []

    def enabled_nodes(data: Any = None) -> List[dict]:
        return []


def proxies_available() -> bool:
    """Return True when the real engines.proxies module was loaded."""
    return _HAS_PROXIES
