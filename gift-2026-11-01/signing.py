# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""signing.py: Ed25519 signatures for receipts, standard library only (RFC 8032, section 5.1).

A receipt digest proves a receipt was not edited after publication; it does not prove who
published it. A signature does: the side that ran the call signs the receipt digest with its
private key, publishes the public key once, and anyone can verify with this file alone.

    sk, pk = keypair()                         # 32-byte seed (keep secret), 32-byte public key
    sig = sign(sk, digest_hex.encode())        # 64 bytes
    verify(pk, digest_hex.encode(), sig)       # True / False
    block = signature_block(sk, digest_hex)    # {"alg": "Ed25519", "public_key": hex, "value": hex,
                                               #  "signed": "receipt digest"}
    check_block(block, digest_hex)             # True / False

This is a straightforward transcription of the RFC's reference algorithm. It is correct but not
constant-time: use it to sign and verify receipts, not to hold keys on a shared machine. The RFC
test vector 1 is in the tests.
"""
from __future__ import annotations

import hashlib
import os

_p = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, _p - 2, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _h(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % _p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % _p
    C = 2 * P[3] * Q[3] * _d % _p
    D = 2 * P[2] * Q[2] % _p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % _p, G * H % _p, F * G % _p, E * H % _p)


def _mul(s: int, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _equal(P, Q) -> bool:
    return (P[0] * Q[2] - Q[0] * P[2]) % _p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % _p == 0


def _recover_x(y: int, sign: int):
    if y >= _p:
        return None
    x2 = (y * y - 1) * pow(_d * y * y + 1, _p - 2, _p)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_p + 3) // 8, _p)
    if (x * x - x2) % _p != 0:
        x = x * _I % _p
    if (x * x - x2) % _p != 0:
        return None
    if (x & 1) != sign:
        x = _p - x
    return x


_gy = 4 * pow(5, _p - 2, _p) % _p
_gx = _recover_x(_gy, 0)
_G = (_gx, _gy, 1, _gx * _gy % _p)


def _compress(P) -> bytes:
    zinv = pow(P[2], _p - 2, _p)
    x, y = P[0] * zinv % _p, P[1] * zinv % _p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(s: bytes):
    if len(s) != 32:
        raise ValueError("invalid point length")
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % _p)


def _secret_expand(secret: bytes):
    if len(secret) != 32:
        raise ValueError("secret key must be 32 bytes")
    h = _h(secret)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_key(secret: bytes) -> bytes:
    a, _ = _secret_expand(secret)
    return _compress(_mul(a, _G))


def keypair(seed: bytes | None = None) -> tuple[bytes, bytes]:
    sk = seed if seed is not None else os.urandom(32)
    return sk, public_key(sk)


def sign(secret: bytes, msg: bytes) -> bytes:
    a, prefix = _secret_expand(secret)
    A = _compress(_mul(a, _G))
    r = int.from_bytes(_h(prefix + msg), "little") % _L
    Rs = _compress(_mul(r, _G))
    h = int.from_bytes(_h(Rs + A + msg), "little") % _L
    s = (r + h * a) % _L
    return Rs + int.to_bytes(s, 32, "little")


def verify(public: bytes, msg: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _decompress(public)
    R = _decompress(signature[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= _L:
        return False
    h = int.from_bytes(_h(signature[:32] + public + msg), "little") % _L
    return _equal(_mul(s, _G), _add(R, _mul(h, A)))


def signature_block(secret: bytes, digest_hex: str) -> dict:
    return {"alg": "Ed25519", "signed": "receipt digest", "public_key": public_key(secret).hex(),
            "value": sign(secret, digest_hex.encode("ascii")).hex()}


def check_block(block: dict, digest_hex: str) -> bool:
    try:
        return block.get("alg") == "Ed25519" and verify(bytes.fromhex(block["public_key"]),
                                                        digest_hex.encode("ascii"), bytes.fromhex(block["value"]))
    except (KeyError, ValueError):
        return False
