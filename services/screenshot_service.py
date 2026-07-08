import os
import time


def _default_folder():
    return os.path.join(os.path.expanduser("~"), "DotaDraftAssistant", "Screenshots")


def capture_fullscreen(save_dir: str) -> str:
    """
    Lazily imports pyautogui so the rest of the app (and any headless/test
    environment) can start up without pyautogui's import-time side effects
    (it spawns a mouseinfo listener thread on import).

    Falls back to Qt's own screen grab if pyautogui can't take the shot
    (not installed, or missing an OS-level screenshot backend like `scrot`
    on Linux) -- this needs no extra dependencies since PyQt is already
    required, so the "Створити скриншот" button still works out of the box.
    """
    if not save_dir or not str(save_dir).strip():
        save_dir = _default_folder()
    os.makedirs(save_dir, exist_ok=True)
    fname = f"draft_{time.strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(save_dir, fname)

    errors = []

    try:
        import pyautogui
        img = pyautogui.screenshot()
        img.save(path)
        return path
    except Exception as e:
        errors.append(str(e))

    try:
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("Немає доступного екрана.")
        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            raise RuntimeError("Не вдалося захопити зображення екрана.")
        if not pixmap.save(path, "PNG"):
            raise RuntimeError("Не вдалося зберегти файл скриншота.")
        return path
    except Exception as e:
        errors.append(str(e))

    raise RuntimeError("Не вдалося створити скриншот: " + "; ".join(errors))
