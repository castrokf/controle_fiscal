from functools import wraps
import re
import time
from urllib.parse import urljoin, urlsplit

from flask import abort, current_app, request
from flask_login import current_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOGIN_FAILURES = {}


def normalize_email(email):
    return (email or "").strip().lower()


def is_valid_email_format(email):
    return bool(EMAIL_RE.fullmatch(normalize_email(email)))


def password_policy_errors(password):
    errors = []
    password = password or ""
    if len(password) < 12:
        errors.append("use pelo menos 12 caracteres")
    if len(password.encode("utf-8")) > 72:
        errors.append("use no maximo 72 bytes por compatibilidade com bcrypt")
    if not re.search(r"[a-z]", password):
        errors.append("inclua letra minuscula")
    if not re.search(r"[A-Z]", password):
        errors.append("inclua letra maiuscula")
    if not re.search(r"\d", password):
        errors.append("inclua numero")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("inclua caractere especial")
    return errors


def is_safe_redirect_url(target):
    if not target:
        return False

    host_url = request.host_url
    ref_url = urlsplit(host_url)
    test_url = urlsplit(urljoin(host_url, target))
    return test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc


def get_login_lock_remaining(email):
    key = _login_key(email)
    _prune_login_failures()
    state = LOGIN_FAILURES.get(key)
    if not state:
        return 0

    locked_until = state.get("locked_until", 0)
    if not locked_until:
        return 0

    remaining = int(locked_until - time.time())
    if remaining <= 0:
        LOGIN_FAILURES.pop(key, None)
        return 0
    return remaining


def register_login_failure(email):
    key = _login_key(email)
    now = time.time()
    window = current_app.config.get("LOGIN_ATTEMPT_WINDOW_SECONDS", 300)
    max_attempts = current_app.config.get("LOGIN_MAX_ATTEMPTS", 5)
    lockout = current_app.config.get("LOGIN_LOCKOUT_SECONDS", 900)
    state = LOGIN_FAILURES.get(key, {"attempts": [], "locked_until": 0})

    attempts = [attempt for attempt in state["attempts"] if now - attempt <= window]
    attempts.append(now)
    state["attempts"] = attempts

    if len(attempts) >= max_attempts:
        state["attempts"] = []
        state["locked_until"] = now + lockout

    LOGIN_FAILURES[key] = state
    _prune_login_failures()


def clear_login_failures(email):
    LOGIN_FAILURES.pop(_login_key(email), None)


def reset_login_failures():
    LOGIN_FAILURES.clear()


def apply_security_headers(response):
    if not current_app.config.get("SECURITY_HEADERS_ENABLED", True):
        return response

    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "img-src 'self' data:; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net;",
    )

    if request.endpoint != "static":
        response.headers.setdefault("Cache-Control", "no-store, max-age=0")
        response.headers.setdefault("Pragma", "no-cache")

    if current_app.config.get("SECURITY_HSTS_ENABLED"):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

    return response


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def _login_key(email):
    client_ip = request.remote_addr or "unknown"
    return f"{client_ip}:{normalize_email(email)}"


def _prune_login_failures():
    now = time.time()
    window = current_app.config.get("LOGIN_ATTEMPT_WINDOW_SECONDS", 300)
    expired = []
    for key, state in LOGIN_FAILURES.items():
        if state.get("locked_until", 0) > now:
            continue
        state["attempts"] = [attempt for attempt in state.get("attempts", []) if now - attempt <= window]
        if not state["attempts"]:
            expired.append(key)

    for key in expired:
        LOGIN_FAILURES.pop(key, None)
