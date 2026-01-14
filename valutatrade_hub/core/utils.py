import json
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


def load_json(path, default: Callable[[], T] = list) -> T:
    """Загружает JSON-данные из файла.

    Args:
        path: Путь к файлу.
        default (Callable): Функция, возвращающая значение по умолчанию.

    Returns:
        T: Загруженные данные или значение по умолчанию.
    """
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default()


def save_json(path, data):
    """Сохраняет данные в JSON-файл.

    Args:
        path: Путь к файлу.
        data: Данные для сохранения.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
