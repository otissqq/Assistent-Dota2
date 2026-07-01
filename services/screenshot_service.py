import os
import time


def capture_fullscreen(save_dir: str) -> str:
    """
    Lazily imports pyautogui so the rest of the app (and any headless/test
    environment) can start up without pyautogui's import-time side effects
    (it spawns a mouseinfo listener thread on import).
    """
    os.makedirs(save_dir, exist_ok=True)
    fname = f"draft_{time.strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(save_dir, fname)
    try:
        import pyautogui
        img = pyautogui.screenshot()
        img.save(path)
        return path
    except Exception as e:
        raise RuntimeError(f"Не вдалося створити скриншот: {e}")
