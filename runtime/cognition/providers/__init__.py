"""Providers for the TriCompany metacognition prototype."""

from runtime.cognition.providers.builtin_markdown import BuiltinMarkdownProvider
from runtime.cognition.providers.external_adapter import ExternalCognitionAdapter
from runtime.cognition.providers.external_http_backend import (
    HttpExternalBackendConfig,
    HttpExternalCognitionBackend,
)
from runtime.cognition.providers.supermemory_backend import (
    SupermemoryBackendConfig,
    SupermemoryExternalBackend,
)
from runtime.cognition.providers.supermemory_sdk_backend import (
    SupermemorySdkBackendConfig,
    SupermemorySdkExternalBackend,
)
from runtime.cognition.providers.org_shared import OrgSharedProvider

__all__ = [
    "BuiltinMarkdownProvider",
    "ExternalCognitionAdapter",
    "HttpExternalBackendConfig",
    "HttpExternalCognitionBackend",
    "OrgSharedProvider",
    "SupermemoryBackendConfig",
    "SupermemoryExternalBackend",
    "SupermemorySdkBackendConfig",
    "SupermemorySdkExternalBackend",
]
