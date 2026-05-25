# АСКАБР-Л

**Автоматизированная система компьютерного анализа болезней растений по изображениям листьев**  
Версия **1.0.0**

## Установка

Requires **Python 3.14** (see `.python-version`).

```bash
uv sync          # рекомендуется: полное окружение разработки
uv run askabr-gui
```

Без uv (только pip):

```bash
pip install -r requirements.txt        # GUI и инференс
pip install -r requirements-train.txt  # + обучение и демо
pip install -r requirements-dev.txt    # как uv sync
```

Файлы `requirements*.txt` генерируются из `uv.lock` — см. комментарии в [`requirements.in`](requirements.in).

## Документация

Полная инструкция: **[docs/INSTRUKCIYA.txt](docs/INSTRUKCIYA.txt)**

В программе: меню **Справка → Инструкция**.

---

## Быстрый старт

### Windows — готовая программа (без Python)

1. Скопируйте `ASKABR-L.exe` и `INSTRUKCIYA.txt` в одну папку.
2. Запустите `ASKABR-L.exe` двойным щелчком.
3. При предупреждении Windows: **Подробнее** → **Выполнить**.

Подробнее — в `docs/INSTRUKCIYA.txt`, раздел 1.

### Установка из исходников (Windows / macOS / Linux)

```bash
# Установите uv: https://docs.astral.sh/uv/getting-started/installation/
cd askabr-l
uv sync
uv run askabr-gui
```

Пошагово для каждой ОС — в `docs/INSTRUKCIYA.txt` (разделы 2–4).

### Сборка ASKABR-L.exe (только Windows)

```cmd
packaging\build_windows.cmd
```

Or in PowerShell: `.\packaging\build_windows.ps1` (also `packaging\build_windows.bat`).

Requires **Python 3.14** (`py -3.14 --version`). Works with Cyrillic Windows usernames (build uses `C:\ProgramData\ASKABR-L\`).

Output: `dist\ASKABR-L.exe` plus `dist\build.log` and `dist\smoke.log`. Debug build: `py -3.14 packaging\build_windows.py --debug`.

See section 5 in `docs/INSTRUKCIYA.txt`.

---

## Структура проекта

| Каталог | Назначение |
|---------|------------|
| `askabr/` | Ядро: классификация, обучение, расчёт показателей |
| `gui/` | Десктопное приложение |
| `models/` | Модели для анализа (томат, груша) |
| `docs/` | Инструкция пользователя (`INSTRUKCIYA.txt`) |
