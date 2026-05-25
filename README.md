# АСКАБР-Л

**Автоматизированная система компьютерного анализа болезней растений по изображениям листьев**  
Версия **1.0.0**

## Установка

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
cd plant-disease-resistance
uv sync
uv run askabr-gui
```

Пошагово для каждой ОС — в `docs/INSTRUKCIYA.txt` (разделы 2–4).

### Сборка ASKABR-L.exe (только Windows)

```powershell
.\packaging\build_windows.ps1
```

Результат: `dist\ASKABR-L.exe` — см. раздел 5 в `docs/INSTRUKCIYA.txt`.

---

## Структура проекта

| Каталог | Назначение |
|---------|------------|
| `askabr/` | Ядро: классификация, обучение, расчёт показателей |
| `gui/` | Десктопное приложение |
| `models/` | Модели для анализа (томат, груша) |
| `docs/` | Инструкция пользователя (`INSTRUKCIYA.txt`) |
