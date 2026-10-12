# AUDIT_REPORT: предварительная версия (этап 0 и частично этапы 1–2)

Дата: 2026-10-12. Среда: облачный Linux-контейнер, JDK 21, Gradle есть. **Minecraft, лаунчер, папка экземпляра пользователя и лог в среде отсутствуют.**

Метки статуса:
- **[FILES]**: подтверждено файлами.
- **[WEB]**: подтверждено веб-источником.
- **[HYP]**: гипотеза, нужна проверка.

---

## 1. Что удалось и что не удалось получить

| Вход из ТЗ | Статус | Комментарий |
|---|---|---|
| `latest(1).log`, ~11 608 строк | **НЕ НАЙДЕН** | Загружен только текст ТЗ. Репозиторий `blackhellvelz-prog/LiminalCraft` был пуст. Поиск по файловой системе контейнера ничего не нашёл. |
| Реальная папка `mods/` | **НЕ НАЙДЕНА** | Версии 23 модов из ТЗ пока **не подтверждены**. |
| `config/` экземпляра | **НЕ НАЙДЕН** | |
| Сейвы / резервные копии | **НЕ ПРИМЕНИМО** | Мира пользователя в среде нет. Резервное копирование нужно делать на машине пользователя (см. MODDING_PLAN.md). |
| `Liminal-Space-Project-Overhaul.jar` | **Публичная копия** | Скачана с CurseForge (file ID 9059696, 2026-10-04) в scratchpad только для локального анализа. **В репозиторий не добавлена.** SHA-256: `c18af864724c90f9be9a7e47e97a4c77608081c4f6bd25ae5ee0f494e8d24e12`. Нужно сравнить с хешем JAR пользователя. |

Поэтому разделы о логе, о версиях модов (MOD_INVENTORY), о матрице совместимости и о производительности **не выполнены** и помечены как NOT TESTED. Остальные выводы ниже относятся к публичной копии основного мода.

## 2. Основной мод [FILES, WEB]

- Страница: https://www.curseforge.com/minecraft/mc-mods/liminal-space-project (проверено 2026-10-12). Автор VoidStriker404, project ID 1675817. Лицензия **All Rights Reserved** [WEB]. То же в `META-INF/mods.toml`: `license="All Rights Reserved"` [FILES].
- `mods.toml` [FILES]: `modId="liminalspaces"`, `version="2.1.2"`, `displayName="Liminal Spaces: Dream Overhaul"`. Зависимости: forge `[47.4.10,48)`, minecraft `[1.20.1]`. Других обязательных зависимостей нет (GeckoLib не требуется).
- Внутри JAR 84 класса в пакете `com.liminalspaces.mod.*` [FILES]. Исходного кода нет.
- Coremod `coremods/vertical_visibility.js` [FILES] патчит **Embeddium** (`me.jellysquid.mods.sodium...OcclusionCuller.isWithinRenderDistance`) и `net.minecraft.client.renderer.GameRenderer`. Патч расширяет вертикальную видимость в «гигантских» сценах. Значит, часть предупреждений рендерера в логе может исходить от этого coremod, а не от конфликта Oculus/Embeddium [HYP]. В логе нужно найти строку `LIMINAL_EMBEDDIUM_VERTICAL_PATCH applied`.

## 3. Измерения: 175 штук, подтверждено [FILES]

Ниже сводка, полный список в `DIMENSION_MANIFEST.csv`. Его генерирует `tools/extract_manifest.py` только из data-файлов JAR.

- В `data/liminalspaces/dimension/`, `dimension_type/` и `worldgen/biome/` по **175** файлов.
- Распределение по группам:

| Группа | Количество | Генератор |
|---|---|---|
| `original_31` | 31 | `liminalspaces:liminal` |
| `prior_added_61` | 61 | `liminalspaces:dream_overhaul` |
| `new_video_83` | 83 | `liminalspaces:dream_overhaul` |

- Это совпадает с `Validation-Notes.json`: `original 31 / prior_added 61 / new_video 83 / total 175`.
- Раскладка генерации из документации JAR (`COMMANDS.txt`):

| Раскладка | Количество | Что это значит для модулей |
|---|---|---|
| `previous repeating layout` | 47 | Предположение пользователя о повторяющемся паттерне здесь подтверждается документацией |
| `1000 x 1000 horizontal tile; height 512` | 35 | Тайл 1000×1000 |
| `10000 x 10000 horizontal tile; height 2032` | 32 | «Мега»-сцены |
| `single reference composition; void outside` | 30 | **Конечные** сцены, снаружи пустота. Вставлять в них модули через паттерн нельзя. |
| Не указано для оригинальных 31 | 31 | Генератор `LiminalChunkBuilder`. Нужен разбор байткода. |

- Вывод: **не все 175 измерений устроены одинаково**. Есть минимум 4–5 разных типов генерации, и система модулей должна учитывать тип.
- Где генерация реализована [FILES]: классы `DreamGenerator`, `DreamBuilder`, `ExpansionBuilder`, `NewSceneBuilder`, `IsolatedScenes`, `LiminalChunkBuilder`/`LiminalChunkGenerator`.
- Есть миграция блоков старых версий: `SceneUpgrade212`, `LegacyDreamBuilder211`. При загрузке чанка она **перезаписывает сгенерированные блоки**, а блоки, отличающиеся от исходной раскладки, сохраняет (`UPDATE-README.md`).
  - Это риск для вставных модулей: блоки аддона в затронутых сценах могут быть удалены или приняты за «чужие» [HYP].
- Команды: `/liminalspaces enter <id>`, `/liminalspaces home`, `/new <id|list|random|next>`. Клавиша G открывает атлас. Команды доступны только с правами оператора [FILES: COMMANDS.txt]. Для debug-меню это готовый безопасный путь телепортации.

## 4. Конфликт с требованием A: мод сам переносит игрока из Верхнего мира [FILES]

В `ModConfig` (COMMON-конфиг Forge) найдены механики, которые переносят игрока в лиминальное измерение **вне** лиминальных измерений:

| Ключ | По умолчанию | Диапазон | Можно отключить конфигом? |
|---|---|---|---|
| `doorways.openingChance`: «Chance per successful hand-opening of a wooden door» | 0.30 | 0–1 | **Да, значение 0.0** |
| `encounters.sleepChance`: «Chance of entering a dream when waking outside liminal dimensions» | 0.40 | 0–1 | **Да, значение 0.0** |
| `encounters.floorAverageMinutes`: «Average minutes of eligible Survival play between floor falls» | 15 | **1–1440** | **Нет.** Минимум частоты — в среднем раз в 1440 мин игры. Полное отключение требует аддона [HYP: нужно найти обработчик]. |

Как ведёт себя одноразовая миграция [FILES: байткод `ModConfig.onLoading`]:
- Она срабатывает, только пока `migration.encounterVersion < 1`, и сбрасывает шанс двери на 0.3.
- После первого запуска выставленный пользователем 0.0 сохраняется.
- Поэтому `encounterVersion` трогать не нужно.

Отдельный конфиг `liminalspaces-overhaul.toml` (COMMON, `DreamConfig`) [FILES]:
- `nightmares.enabled` (true): «Enable rare survival encounters in all liminal dimensions».
- `screams` (true).
- `entryGraceSeconds` (120).
- `averageEncounterSeconds` (420).

Об именах файлов:
- `liminalspaces-client.toml` и `liminalspaces-common.toml` — это стандартные имена Forge для `registerConfig` без явного имени файла [HYP]. Сверить с реальной папкой `config/`.

**Самое дешёвое исправление для требования A** (только конфиг, без кода) — в common-конфиге основного мода:

```toml
[doorways]
    openingChance = 0.0
[encounters]
    sleepChance = 0.0
    floorAverageMinutes = 1440
```

Последствие: вход в лиминальные пространства останется через команды и атлас, а позже через сюжетный вход аддона. Решение за пользователем.

## 5. Существа: 10 штук [FILES]

Полный список в `ENTITY_AUDIT.csv`. Registry ID:

`springtrap`, `smiley`, `smiler`, `horror_m`, `plague_doctor`, `bacteria`, `needlelimbs`, `library_entity`, `aranea_membri`, `partygoer`

Все с префиксом `liminalspaces:`.

В `ExpansionEvents` также встречаются строки `coilback`, `hollow_bell`, `velvet_guest`, `glassling`, `latchjaw`, `paper_widow`, `drain_mother`, `surveyor`, `threshold`, `unfinished`.
- Судя по `COMMANDS.txt` («ALL TEN PRIOR OVERHAUL CREATURES REPLACED»), это ID **прежних, заменённых** существ, вероятно для миграции старых сейвов [HYP].

### Почему существа не вписываются в стиль Minecraft

Это прямые факты из `creature-optimization.json` и `MODEL-CREDITS.txt`, а не вкусовщина:

1. **Источник моделей.** Все 10 моделей — сторонние модели Sketchfab (CC-BY-4.0). Изначально это высокополигональные меши: до 5,27 млн треугольников у Springtrap, 1,9 млн у Plague Doctor, 1,2 млн у Horror M.
2. **Рендер.** Существа рисуются кастомным `ImportedCreatureRenderer` из `.mesh.gz` с LOD. Даже ближний LOD — 7–25 тыс. треугольников. Это не кубоидная модель Minecraft.
3. **Текстуры.** Атласы 512–2560 px против привычных для Minecraft 64×64 и 128×128. Сам автор признаёт «texture speckling» у Smiler и Horror M.
4. **Анимация.** «Lightweight rigid parts», то есть жёсткие части без воксельной анатомии.
5. **Тематика.** `springtrap` — модель персонажа FNaF, `horror_m` — фан-ремоделинг. Это **не** сущности Backrooms. Кроме того, Springtrap — чужая франшиза: CC-BY лицензия фан-модели не снимает вопроса о правах на персонажа [HYP по правовому статусу].

Вывод: исправлять нужно **через новые кубоидные модели в аддоне**, а не перекрашиванием. Старые сущности остаются в реестре; аддон может ограничить их спавн, если это позволит событийная модель (требует исследования `Encounters`/`Nightmare`).

## 6. Что ещё не сделано и почему

- **LOG_FINDINGS, MOD_INVENTORY, COMPATIBILITY_MATRIX, графический стек, задержки тиков.** Нет лога и папки mods. Веб-проверка 23 модов имеет смысл только после подтверждения их точных версий по реальным файлам.
- **Сборка и тест аддона и debug-меню.** В среде нет Minecraft и GPU. Можно собрать JAR через Forge MDK, но GUI-тесты, скриншоты и проверка в реальном профиле здесь невозможны: по ТЗ это NOT TESTED, пока их не выполнит пользователь.
- **Этап 3 (дизайн-документы).** По ТЗ идёт после завершения аудита этапов 1–2.
