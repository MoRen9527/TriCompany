from __future__ import annotations

from dataclasses import dataclass

from runtime.cognition.contracts.provider_contract import (
    CognitionNamespace,
    MemoryScope,
    NamespaceBundle,
)


@dataclass(frozen=True)
class NamespacePolicy:
    kernel_id: str = "tricompany-meta-kernel"
    private_prefix: str = "employee"
    org_shared_key: str = "org/shared"
    audit_key: str = "org/audit"

    def resolve(self, actor_id: str, role_name: str) -> NamespaceBundle:
        private_key = f"{self.private_prefix}/{actor_id}"
        return NamespaceBundle(
            actor_id=actor_id,
            private_namespace=CognitionNamespace(
                key=private_key,
                scope=MemoryScope.EMPLOYEE_PRIVATE,
                owner=actor_id,
                description=f"{role_name} 的私域记忆空间",
            ),
            org_shared_namespace=CognitionNamespace(
                key=self.org_shared_key,
                scope=MemoryScope.ORG_SHARED,
                owner=self.kernel_id,
                description="虚拟公司跨角色共享记忆空间",
            ),
            audit_namespace=CognitionNamespace(
                key=self.audit_key,
                scope=MemoryScope.AUDIT,
                owner=self.kernel_id,
                description="虚拟公司元认知审计空间",
            ),
        )


DEFAULT_NAMESPACE_POLICY = NamespacePolicy()
