"""
Global hotkey manager for the "create screenshot" shortcut.

Tries to install a real system-wide hook via the `keyboard` package, so the
shortcut fires even while Dota 2 (not this app) has focus -- which is the
whole point of a draft-screenshot hotkey. If `keyboard` isn't installed, or
it fails to hook into the OS (missing permissions, unsupported platform,
headless environment, ...), `register()` returns False so the caller can
fall back to an in-app QShortcut instead.

`keyboard`'s callbacks fire on its own background thread, never on the Qt
GUI thread -- callers must pass a callback that is safe to invoke off the
GUI thread (e.g. a Qt signal's `.emit`, which Qt automatically queues back
onto the receiver's thread).
"""

try:
    import keyboard as _kb
    _HAVE_KEYBOARD = True
except Exception:
    _kb = None
    _HAVE_KEYBOARD = False

_active_hotkey = None


def available() -> bool:
    return _HAVE_KEYBOARD


# Qt spells some keys differently than the `keyboard` package expects.
# Without this, binding the hotkey to Print Screen (Qt: "Print"/"Print
# Screen") silently failed to register, because `keyboard` only recognises
# the canonical name "print screen" (with the space kept).
_KEY_ALIASES = {
    "print": "print screen",
    "printscreen": "print screen",
    "print screen": "print screen",
    "prtsc": "print screen",
    "prtscr": "print screen",
    "prtscn": "print screen",
    "sysreq": "print screen",
}


def _normalize(hotkey: str) -> str:
    """Normalizes a Qt-style key sequence (e.g. 'Ctrl+Print Screen') into
    the format the `keyboard` package expects. Only the '+' combo
    separators have surrounding whitespace stripped -- key *names* that
    contain their own space (like "Print Screen") must keep it, or
    `keyboard` won't recognize them."""
    parts = [p.strip().lower() for p in hotkey.strip().split("+") if p.strip()]
    parts = [_KEY_ALIASES.get(p, p) for p in parts]
    return "+".join(parts)


def register(hotkey: str, callback) -> bool:
    """Registers `hotkey` (e.g. 'F8', 'ctrl+f8') to call `callback()`.
    Returns True on success (system-wide hook installed)."""
    unregister()
    if not hotkey or not _HAVE_KEYBOARD:
        return False
    global _active_hotkey
    try:
        _kb.add_hotkey(_normalize(hotkey), callback)
        _active_hotkey = _normalize(hotkey)
        return True
    except Exception:
        _active_hotkey = None
        return False


def unregister():
    global _active_hotkey
    if _HAVE_KEYBOARD and _active_hotkey is not None:
        try:
            _kb.remove_hotkey(_active_hotkey)
        except Exception:
            pass
    _active_hotkey = None
