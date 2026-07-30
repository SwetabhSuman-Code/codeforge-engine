from slowapi import Limiter


def get_safe_remote_address(request) -> str:
    if hasattr(request, "client") and request.client and getattr(request.client, "host", None):
        return request.client.host
    return "127.0.0.1"


limiter = Limiter(key_func=get_safe_remote_address, default_limits=["100/minute"])
