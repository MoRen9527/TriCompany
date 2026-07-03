from __future__ import annotations

import hashlib
import re
from typing import Any

from ecdsa import BadSignatureError, SECP256k1, SigningKey, VerifyingKey, util


_SIMULATED_MNEMONIC_WORDS: tuple[str, ...] = (
    "abandon",
    "ability",
    "able",
    "about",
    "above",
    "absent",
    "absorb",
    "abstract",
    "absurd",
    "abuse",
    "access",
    "accident",
    "account",
    "accuse",
    "achieve",
    "acid",
    "acoustic",
    "acquire",
    "across",
    "act",
    "action",
    "actor",
    "actress",
    "actual",
    "adapt",
    "add",
    "addict",
    "address",
    "adjust",
    "admit",
    "adult",
    "advance",
    "advice",
    "aerobic",
    "affair",
    "afford",
    "afraid",
    "again",
    "age",
    "agent",
    "agree",
    "ahead",
    "aim",
    "air",
    "airport",
    "aisle",
    "alarm",
    "album",
    "alcohol",
    "alert",
    "alien",
    "all",
    "alley",
    "allow",
    "almost",
    "alone",
    "alpha",
    "already",
    "also",
    "alter",
    "always",
    "amateur",
    "amazing",
    "among",
)


def sign_web3_package_hash(
    package_hash: str,
    *,
    signing_key: str = "",
    mnemonic: str = "",
    default_seed: str = "",
) -> dict[str, str]:
    signer, wallet = _resolve_signing_material(
        signing_key=signing_key,
        mnemonic=mnemonic,
        default_seed=default_seed,
    )
    package_hash_bytes = _normalize_hash_bytes(package_hash)
    signature_bytes = signer.sign_deterministic(
        package_hash_bytes,
        hashfunc=hashlib.sha256,
        sigencode=util.sigencode_string_canonize,
    )
    return {
        "packageHash": _normalize_hash_text(package_hash),
        "signature": "0x" + signature_bytes.hex(),
        "signerAddress": wallet["address"],
        "publicKey": wallet["publicKey"],
        "credentialType": wallet["credentialType"],
        "credentialHint": wallet["credentialHint"],
        "curve": "secp256k1",
        "signatureAlgorithm": "ecdsa",
        "hashAlgorithm": "sha3_256-simulated",
    }


def verify_web3_signature(package_hash: str, signature: str, public_key: str) -> bool:
    package_hash_bytes = _normalize_hash_bytes(package_hash)
    signature_bytes = _normalize_hex_bytes(signature, expected_length=64, field_name="signature")
    public_key_bytes = _normalize_public_key_bytes(public_key)
    verifier = VerifyingKey.from_string(public_key_bytes[1:], curve=SECP256k1, hashfunc=hashlib.sha256)
    try:
        return verifier.verify(
            signature_bytes,
            package_hash_bytes,
            hashfunc=hashlib.sha256,
            sigdecode=util.sigdecode_string,
        )
    except BadSignatureError:
        return False


def build_simulated_web3_wallet(*, default_seed: str) -> dict[str, str]:
    _, wallet = _resolve_signing_material(signing_key="", mnemonic="", default_seed=default_seed)
    return wallet


def _resolve_signing_material(
    *,
    signing_key: str,
    mnemonic: str,
    default_seed: str,
) -> tuple[SigningKey, dict[str, str]]:
    if signing_key.strip() and mnemonic.strip():
        raise ValueError("provide either signing_key or mnemonic, not both")
    if signing_key.strip():
        private_key_bytes = _normalize_hex_bytes(signing_key, expected_length=32, field_name="signing_key")
        credential_type = "private-key"
        credential_hint = _normalize_hash_text(signing_key)[:10] + "..."
    elif mnemonic.strip():
        mnemonic_text = _normalize_mnemonic(mnemonic)
        private_key_bytes = hashlib.sha256(("mnemonic::" + mnemonic_text).encode("utf-8")).digest()
        credential_type = "mnemonic"
        credential_hint = _mnemonic_hint(mnemonic_text)
    else:
        seed = str(default_seed or "simulated-web3-wallet").strip() or "simulated-web3-wallet"
        mnemonic_text = _simulate_mnemonic(seed)
        private_key_bytes = hashlib.sha256(("simulated::" + seed + "::" + mnemonic_text).encode("utf-8")).digest()
        credential_type = "simulated-mnemonic"
        credential_hint = _mnemonic_hint(mnemonic_text)
    signer = SigningKey.from_string(private_key_bytes, curve=SECP256k1, hashfunc=hashlib.sha256)
    verifier = signer.verifying_key
    public_key_bytes = b"\x04" + verifier.to_string()
    address = "0x" + hashlib.sha3_256(verifier.to_string()).digest()[-20:].hex()
    wallet = {
        "address": address,
        "publicKey": "0x" + public_key_bytes.hex(),
        "credentialType": credential_type,
        "credentialHint": credential_hint,
    }
    return signer, wallet


def _simulate_mnemonic(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    words: list[str] = []
    for index in range(12):
        offset = (index * 2) % len(digest)
        word_index = int.from_bytes(digest[offset : offset + 2], "big") % len(_SIMULATED_MNEMONIC_WORDS)
        words.append(_SIMULATED_MNEMONIC_WORDS[word_index])
    return " ".join(words)


def _mnemonic_hint(mnemonic: str) -> str:
    words = mnemonic.split()
    if len(words) < 4:
        return mnemonic
    return f"{words[0]} {words[1]} ... {words[-2]} {words[-1]}"


def _normalize_mnemonic(value: str) -> str:
    words = [item.strip().lower() for item in re.split(r"\s+", str(value or "").strip()) if item.strip()]
    if len(words) not in {12, 24}:
        raise ValueError("mnemonic must contain 12 or 24 words")
    if any(not re.fullmatch(r"[a-z]+", word) for word in words):
        raise ValueError("mnemonic words must be lowercase alphabetic tokens")
    return " ".join(words)


def _normalize_hash_text(value: str) -> str:
    return "0x" + _normalize_hex_bytes(value, expected_length=32, field_name="package_hash").hex()


def _normalize_hash_bytes(value: str) -> bytes:
    return _normalize_hex_bytes(value, expected_length=32, field_name="package_hash")


def _normalize_public_key_bytes(value: str) -> bytes:
    public_key_bytes = _normalize_hex_bytes(value, expected_length=65, field_name="public_key")
    if public_key_bytes[:1] != b"\x04":
        raise ValueError("public_key must use uncompressed 0x04-prefixed format")
    return public_key_bytes


def _normalize_hex_bytes(value: str, *, expected_length: int, field_name: str) -> bytes:
    text = str(value or "").strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    if not re.fullmatch(r"[0-9a-f]+", text or ""):
        raise ValueError(f"{field_name} must be hex-encoded")
    raw = bytes.fromhex(text)
    if len(raw) != expected_length:
        raise ValueError(f"{field_name} must be {expected_length} bytes")
    return raw
