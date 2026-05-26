# АСКАБР-Л

**Автоматизированная система компьютерного анализа болезней растений по изображениям листьев**  
Версия **1.0.0**

## Запуск (рекомендуется)

Нужна папка проекта целиком (с `models/`, `askabr/`, `gui/`). Python ставить отдельно не обязательно — его подтянет **uv**.

### Windows

1. Установите [uv](https://docs.astral.sh/uv/getting-started/installation/) (в PowerShell одна команда — в [инструкции](docs/INSTRUKCIYA.txt), раздел 3.2).
2. Откройте PowerShell, перейдите в каталог проекта: `cd <путь_к_каталогу_проекта>`
3. Первый раз (10–25 мин, нужен интернет):

```powershell
uv sync
```

4. Запуск программы:

```powershell
uv run askabr-gui
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
cd <каталог_проекта>
uv sync
uv run askabr-gui
```

Полная инструкция по установке и эксплуатации: **[docs/INSTRUKCIYA.txt](docs/INSTRUKCIYA.txt)**  
В программе: меню **Справка → Инструкция**.

## Требования

- **Python 3.14** (устанавливается автоматически через `uv sync`, см. `.python-version`)
- Модели в `models/tomato/` и `models/pear/` (`model_v1.0.0.pt` или `best.pt`)
- ~5–8 ГБ свободного места при первой установке

## Альтернатива без uv

```bash
pip install -r requirements.txt        # GUI и инференс
pip install -r requirements-train.txt  # + обучение и демо
pip install -r requirements-dev.txt      # как uv sync
askabr-gui
```

Файлы `requirements*.txt` генерируются из `uv.lock` — см. [requirements.in](requirements.in).

## Структура проекта

| Каталог | Назначение |
|---------|------------|
| `askabr/` | Ядро: классификация, обучение, расчёт показателей |
| `gui/` | Десктопное приложение |
| `models/` | Модели для анализа (томат, груша) |
| `docs/` | Инструкция пользователя (`INSTRUKCIYA.txt`) |
