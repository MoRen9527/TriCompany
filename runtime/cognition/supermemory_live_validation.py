from __future__ import annotations

import json
import os
import sys
import time
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.cognition.contracts.provider_contract import RecallQuery, RecallResult
from runtime.cognition.kernel.meta_cognition_kernel import MetaCognitionKernel
from runtime.cognition.providers.external_adapter import ExternalCognitionAdapter
from runtime.cognition.providers.supermemory_backend import (
    SupermemoryBackendConfig,
    SupermemoryExternalBackend,
)


CHIEF_OF_STAFF_ID = "ceo-chief-of-staff"
ENABLE_LIVE_VALIDATION_ENV = "TRICOMPANY_ENABLE_SUPERMEMORY_LIVE_VALIDATION"
API_KEY_ENV = "SUPERMEMORY_API_KEY"
BASE_URL_ENV = "SUPERMEMORY_BASE_URL"
USE_BEARER_ENV = "SUPERMEMORY_USE_BEARER_AUTH"
TIMEOUT_SECONDS_ENV = "SUPERMEMORY_TIMEOUT_SECONDS"
SEARCH_ATTEMPTS_ENV = "SUPERMEMORY_LIVE_SEARCH_ATTEMPTS"
SEARCH_DELAY_SECONDS_ENV = "SUPERMEMORY_LIVE_SEARCH_DELAY_SECONDS"
REPORT_PATH_ENV = "TRICOMPANY_SUPERMEMORY_LIVE_REPORT_PATH"
PRIVATE_CONTEXT_MARKER = f"[external-supermemory-live::employee/{CHIEF_OF_STAFF_ID}]"
ORG_SHARED_CONTEXT_MARKER = "[external-supermemory-live::org/shared]"


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return float(raw)


def _load_live_backend_config() -> SupermemoryBackendConfig:
    if not _env_flag(ENABLE_LIVE_VALIDATION_ENV):
        raise unittest.SkipTest(
            f"Set {ENABLE_LIVE_VALIDATION_ENV}=1 to enable Supermemory live validation."
        )

    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        raise unittest.SkipTest(
            f"Set {API_KEY_ENV} before enabling Supermemory live validation."
        )

    return SupermemoryBackendConfig(
        api_key=api_key,
        base_url=os.environ.get(BASE_URL_ENV, "https://api.supermemory.ai"),
        timeout_seconds=_env_float(TIMEOUT_SECONDS_ENV, 10.0),
        max_retries=2,
        backoff_seconds=(0.5, 1.0, 2.0),
        limit=8,
        threshold=0.2,
        metadata={
            "workspace": "tricompany",
            "validationMode": "live-smoke",
        },
        use_bearer_auth=_env_flag(USE_BEARER_ENV, default=True),
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _report_path() -> Path:
    configured = os.environ.get(REPORT_PATH_ENV, "").strip()
    if configured:
        return Path(configured)
    return (
        _repo_root()
        / "docs"
        / "execution"
        / "hermes-copilot-host"
        / "phase-1"
        / "SUPERMEMORY-LIVE-VALIDATION.latest.json"
    )


def _build_kernel(backend: SupermemoryExternalBackend) -> MetaCognitionKernel:
    kernel = MetaCognitionKernel()
    kernel.register_actor(
        actor_id=CHIEF_OF_STAFF_ID,
        role_name="ChiefOfStaff",
        display_name="小贾",
    )
    kernel.register_provider(ExternalCognitionAdapter("supermemory-live", backend))
    return kernel


def _has_recalled_namespaces(
    results: list[RecallResult],
    expected_namespaces: tuple[str, ...],
    token: str,
) -> bool:
    recalled_namespaces = {
        result.namespace
        for result in results
        if token in result.content
    }
    return all(namespace in recalled_namespaces for namespace in expected_namespaces)


def _poll_backend_results(
    backend: SupermemoryExternalBackend,
    *,
    actor_id: str,
    query_text: str,
    namespaces: tuple[str, ...],
    attempts: int,
    delay_seconds: float,
) -> list[RecallResult]:
    last_results: list[RecallResult] = []
    for attempt in range(attempts):
        last_results = list(
            backend.prefetch(
                RecallQuery(
                    actor_id=actor_id,
                    text=query_text,
                    namespaces=namespaces,
                )
            )
        )
        if _has_recalled_namespaces(last_results, namespaces, query_text):
            return last_results
        if attempt + 1 < attempts:
            time.sleep(delay_seconds)
    return last_results


def _poll_kernel_context(
    kernel: MetaCognitionKernel,
    *,
    actor_id: str,
    query_text: str,
    attempts: int,
    delay_seconds: float,
) -> str:
    last_context = ""
    expected_markers = (
        PRIVATE_CONTEXT_MARKER,
        ORG_SHARED_CONTEXT_MARKER,
    )
    for attempt in range(attempts):
        last_context = kernel.prefetch_context(actor_id, query_text)
        if query_text in last_context and all(marker in last_context for marker in expected_markers):
            return last_context
        if attempt + 1 < attempts:
            time.sleep(delay_seconds)
    return last_context


def _write_live_report(
    *,
    actor_id: str,
    query_text: str,
    context: str,
    results: list[RecallResult],
    config: SupermemoryBackendConfig,
    attempts: int,
    delay_seconds: float,
) -> Path:
    report_path = _report_path()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    matching_results = [result for result in results if query_text in result.content]
    recalled_namespaces = sorted({result.namespace for result in matching_results})
    results_by_namespace: dict[str, int] = {}
    for result in matching_results:
        results_by_namespace[result.namespace] = results_by_namespace.get(result.namespace, 0) + 1

    payload = {
        "status": "passed",
        "validatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "actorId": actor_id,
        "queryText": query_text,
        "baseUrl": config.base_url,
        "authMode": "bearer" if config.use_bearer_auth else "x-supermemory-api-key",
        "attempts": attempts,
        "delaySeconds": delay_seconds,
        "contextMarkers": {
            "private": PRIVATE_CONTEXT_MARKER in context,
            "orgShared": ORG_SHARED_CONTEXT_MARKER in context,
        },
        "matchingResultCount": len(matching_results),
        "recalledNamespaces": recalled_namespaces,
        "resultsByNamespace": results_by_namespace,
    }

    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report_path


class SupermemoryLiveValidationTest(unittest.TestCase):
    def test_supermemory_live_validation_recalls_private_shared_and_audit(self) -> None:
        backend = SupermemoryExternalBackend(_load_live_backend_config())
        kernel = _build_kernel(backend)
        bundle = kernel.namespaces_for(CHIEF_OF_STAFF_ID)

        run_token = f"tricompany-live-{uuid.uuid4().hex[:12]}"
        user_content = f"live validation user token {run_token}"
        assistant_content = f"live validation assistant token {run_token}"
        attempts = _env_int(SEARCH_ATTEMPTS_ENV, 6)
        delay_seconds = _env_float(SEARCH_DELAY_SECONDS_ENV, 2.0)

        kernel.sync_turn(CHIEF_OF_STAFF_ID, user_content, assistant_content)
        kernel.session_end(
            CHIEF_OF_STAFF_ID,
            [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
            ],
        )

        context = _poll_kernel_context(
            kernel,
            actor_id=CHIEF_OF_STAFF_ID,
            query_text=run_token,
            attempts=attempts,
            delay_seconds=delay_seconds,
        )
        self.assertIn(run_token, context)
        self.assertIn(PRIVATE_CONTEXT_MARKER, context)
        self.assertIn(ORG_SHARED_CONTEXT_MARKER, context)

        live_results = _poll_backend_results(
            backend,
            actor_id=CHIEF_OF_STAFF_ID,
            query_text=run_token,
            namespaces=(
                bundle.private_namespace.key,
                bundle.org_shared_namespace.key,
                bundle.audit_namespace.key,
            ),
            attempts=attempts,
            delay_seconds=delay_seconds,
        )

        for namespace in (
            bundle.private_namespace.key,
            bundle.org_shared_namespace.key,
            bundle.audit_namespace.key,
        ):
            self.assertTrue(
                any(result.namespace == namespace and run_token in result.content for result in live_results),
                f"Missing live recall for namespace {namespace}. Results: {live_results}",
            )

        report_path = _write_live_report(
            actor_id=CHIEF_OF_STAFF_ID,
            query_text=run_token,
            context=context,
            results=live_results,
            config=backend._config,
            attempts=attempts,
            delay_seconds=delay_seconds,
        )
        self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)