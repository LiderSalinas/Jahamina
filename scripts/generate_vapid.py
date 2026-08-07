"""Genera un par VAPID y lo imprime una sola vez; no escribe archivos."""

import base64

from py_vapid import Vapid


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def main() -> None:
    vapid = Vapid()
    vapid.generate_keys()
    private_key = vapid.private_key
    private_value = private_key.private_numbers().private_value.to_bytes(32, "big")
    public_numbers = private_key.public_key().public_numbers()
    public_value = b"\x04" + public_numbers.x.to_bytes(32, "big") + public_numbers.y.to_bytes(32, "big")
    print("WEB_PUSH_VAPID_PUBLIC_KEY=" + base64url(public_value))
    print("WEB_PUSH_VAPID_PRIVATE_KEY=" + base64url(private_value))
    print("Guardá ambos valores directamente en los gestores de secretos; no los escribas en archivos del repositorio.")


if __name__ == "__main__":
    main()
