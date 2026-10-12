# HANDOFF: передача проекта LiminalCraft локальному клиенту

Дата остановки: 2026-10-12.

Работа шла в облачной сессии Claude Code: Linux-контейнер, JDK 21 и отдельно Temurin 17, без Minecraft и без GPU. Пользователь попросил остановиться и передать работу локальному клиенту. Исходное ТЗ лежит в `repo-snapshot/docs/ORIGINAL_PROMPT_RU.txt`. Его требования по-прежнему в силе.

## 0. С чего начать (порядок чтения)

1. Этот файл.
2. `repo-snapshot/AUDIT_REPORT.md`: первичный аудит.
   - **Внимание:** часть его выводов уточнена в §3 ниже, раздел «Поправки».
3. `RESEARCH_SUMMARY_UNVERIFIED.md`: сводная таблица по 23 модам.
4. `research/stage2/sub_*.json`: разбор подсистем основного мода по байткоду. Это главная база для проектирования аддона.
5. `research/stage1/research_*.json`: подробные карточки модов с источниками и статусами утверждений.
6. `research/stage2/api_*.json`: проверенные API Forge 1.20.1 и отчёт о пробной сборке аддона.
7. `research/stage2/bestiary_index.json`: список кандидатов в бестиарий. В `research/stage2_partial/` лежит одна черновая карточка.

**Важно: ни один JSON из `research/` не прошёл состязательную перепроверку.** Перепроверку не успели запустить. Внутри карточек у каждого утверждения есть свой статус: `VERIFIED FROM FILES`, `VERIFIED FROM WEB SOURCE` или `HYPOTHESIS`. Независимой проверки не было, поэтому ключевые выводы стоит перепроверить перед тем, как на них опираться.

## 1. Репозиторий и git

- GitHub: `blackhellvelz-prog/LiminalCraft`. **Репозиторий ПУБЛИЧНЫЙ**: всё, что в него попадает, публикуется.
- Рабочая ветка: `claude/stage1-audit`. На GitHub она стоит как default. Pull request не создавался.
- В ветке два коммита: первичный аудит (stage 0) и `tools/log_scan.py` + `LOG_INDEX.csv`.
- `repo-snapshot/` — точная копия содержимого ветки на момент остановки.
- В репозиторий **не попадают**: JAR основного мода, его дизассемблированный код, сырой лог пользователя, ключ Meshy. Сам `handoff/` тоже в `.gitignore`.

## 2. Решения и пожелания пользователя (зафиксировано в переписке)

- **Изучен первый лог.** Это `latest(1).log`, 11 607 строк. Его анонимизированная копия: `log/latest_anonymised.log`, ник и UUID заменены. Других логов, папки `mods/`, `config/` и сейвов пользователь пока не присылал («Пока только так»).
- **Meshy.** Пользователь дал API-ключ Meshy, чтобы создавать картинки, иконки, 3D-модели и анимации по необходимости.
  - Ключ рабочий: на 2026-10-12 баланс 1955 кредитов (monthly 1784 + permanent 171).
  - **Ключа в архиве нет.** Возьмите его у пользователя и передавайте через переменную окружения `MESHY_API_KEY`.
  - Пользователю рекомендовано перевыпустить ключ: он был отправлен в чате.
  - Проверка ключа: `GET https://api.meshy.ai/openapi/v1/balance` с заголовком `Authorization: Bearer $MESHY_API_KEY`. Запрос бесплатный.
- **Открытые ресурсы предпочтительнее.** Пожелание пользователя: «Если есть что-то в открытом доступе, то лучше позаимствовать». Значит, сначала ищем CC0 или CC-BY с указанием автора.
- **Картинки из Wiki можно использовать для атласа существ и пространств.** Пользователь это разрешил. Согласованная схема:
  - скрипт скачивает картинки на машине пользователя в локальный ресурспак, который не коммитится;
  - для каждой картинки записываются URL источника, автор и лицензия (блок «Image Attribution» на Wikidot);
  - в публичный репозиторий кладём только картинки со свободной лицензией и с указанием автора.

  Скрипт ещё **не написан**.
- **Модели существ.** Выявлено, что высокополигональные импортированные меши — главная причина «не-майнкрафтового» вида. Поэтому Meshy используем для концептов, иконок и референсов. Сами существа делаем кубоидными моделями Minecraft (ModelPart/LayerDefinition или Blockbench) с пиксельными текстурами 64×64 или 128×128.
- **Оркестрация.** Пользователь просил работать в режиме Ultracode: параллельные агенты плюс состязательная перепроверка.

### Решение, которое ждёт ответа пользователя

Чтобы выполнить требование A, нужно ли убрать переносы из Верхнего мира? Ниже — что именно включать и чего это стоит.
- `openingChance = 0.0` и `sleepChance = 0.0` в common-конфиге основного мода.
- Плюс полное подавление провалов сквозь пол кодом аддона (см. §3). Конфигом их можно только сделать редкими: минимальная частота — раз в 1440 мин игры.
- Последствие: в лиминальные пространства игрок будет попадать только командами, атласом и будущим сюжетным входом аддона.

## 3. Ключевые факты на момент остановки

### Основной мод: подтверждено по файлам

`liminalspaces` 2.1.2, «Liminal Spaces: Dream Overhaul», All Rights Reserved.

**Измерения: 175.** Совпадение с логом пользователя полное.
- Группы: `original_31` (генератор `liminalspaces:liminal`), `prior_added_61` и `new_video_83` (генератор `liminalspaces:dream_overhaul`).
- Полный список: `repo-snapshot/DIMENSION_MANIFEST.csv`. Его создаёт `tools/extract_manifest.py`.

**Генерация** (`sub_sub_dream_generator.json`, `sub_sub_original_generator.json`, `sub_sub_expansion_generator.json`):
- Блоки ставятся как детерминированная функция от (scene, x, y, z), без сида и RNG.
- В DreamBuilder (47 сцен) клетка 64×64, у семейства city — 96×96. Halls/maze/hotel имеют сверхпериод 3 клетки.
- Оригинальные 31 — строгая тайловая сетка с периодами от 10 до 144. Предположение о бесконечном повторяющемся паттерне подтверждено для большинства сцен.
- 30 «isolated» сцен — конечные композиции с пустотой снаружи. Их при загрузке переписывает миграция `SceneUpgrade212`:
  - событие `ChunkEvent.Load`;
  - сравнение с Legacy-раскладкой;
  - отметка обработанных чанков в SavedData `dream_scenes212`.
- В этих 30 сценах модули **не ставить**.

**Рекомендованная точка вставки модулей:**
- `ChunkEvent.Load` с приоритетом LOWEST, только сервер, только `isNewChunk()`;
- генератор `DreamGenerator`, сцены не isolated;
- `setBlockState(..., false)` строго внутри своего чанка;
- свет, BlockEntity и сущности — отложенно, на `ServerTickEvent`;
- маркер обработки — в NBT чанка или в своём SavedData.

Placed features через biome modifier **не сработают**: во всех dimension JSON стоит `features=false`.

**Встречи** (`sub_sub_encounters_entities.json`):
- Единственный путь спавна — `Encounters.tick`: `PlayerTickEvent`, проверка раз в 5 с.
- Работает во **всех 175** измерениях, без пулов по сценам. Не в creative/spectator и не на PEACEFUL.
- Grace 120 с после входа, в среднем одна встреча за 420 с, кап — 2 существа в радиусе 96 блоков.
- Аддон может фильтровать или заменять спавны по измерению через отменяемый `EntityJoinLevelEvent`.
- `MobSpawnEvent.FinalizeSpawn` **не** вызывается.

**Переносы из нелиминальных измерений** (`sub_sub_travel_overworld.json`). **Поправка к AUDIT_REPORT §4:**
- **Двери** срабатывают в **любом** измерении, включая сами лиминальные. Условия:
  - `RightClickBlock`, основная рука, без shift, не спектатор;
  - деревянная или иная «ручная» дверь, в закрытом состоянии;
  - кулдаун 60 тиков.
- **Сон:** при **любом** пробуждении вне лиминального измерения, `PlayerWakeUpEvent`. `sleepChance = 0.0` отключает его полностью.
- **Провалы сквозь пол** работают в любом нелиминальном измерении, для Survival и Adventure, раз в 40 тиков.
  - Конфигом их не отключить. Значения ниже 1 Forge приводит к 1, и это худший вариант.
  - Способ без mixin: свой обработчик `PlayerTickEvent` END с приоритетом LOWEST. Если `persistentData.LiminalSpacesNoclipTicks == 24` и игрок вне лиминального измерения — снять ключ, эффект Darkness мода и надпись в action bar. Подробности в отчёте.
- **«Дом»** — это точка возрождения, а не место входа.
- Инвентарь между измерениями не меняется. `LiminalSpacesInventory` используется только при смерти в лиминальном измерении (аналог keepInventory).

**Клиент** (`sub_sub_client_effects.json`):
- `DimensionSpecialEffects` зарегистрированы только для 144 измерений `dream_overhaul`. 31 оригинальное измерение использует ванильные эффекты `minecraft:overworld`.
- Музыка мода никогда не играет в Overworld.
- Клавиша G открывает атлас. Есть `CreatureGalleryScreen`: в 01:14:50 в логе одновременно загрузились все ближние LOD.

### Моды: карточки этапа 1, без перепроверки

**Влияние на 175 лиминальных измерений:**

| Мод | Где действует | Можно ли ограничить |
|---|---|---|
| Biomes O' Plenty, TerraBlender | Только Overworld и Nether, в лиминальных не действуют | Не нужно |
| Enhanced Celestials 2 | Только в измерениях, у которых есть запись `enhancedcelestials2core:lunar/dimension_settings` | Да, настраивается датапаком |
| Falling Leaves | Глобально, в том числе в лиминальных | Фильтра по измерениям нет, есть только глобальный `leafSpawnRate` |
| FallingTree | Глобально | Фильтра по измерениям нет |
| Oculus, Embeddium, Sodium Dynamic Lights | Глобально на клиенте | Шейдерпак выбирает программы по измерению через `dimension.properties`; детали в карточке oculus |
| Xaero (миникарта и карта мира) | Пишут данные для каждого посещённого измерения | См. карточки xaero* |

**Явных несовместимостей не найдено.** Embeddium 0.3.31 и Oculus 1.8.0 — последние версии для Forge 1.20.1 по данным карточек.

### Лог: подтверждено (`repo-snapshot/LOG_INDEX.csv`, `tools/log_scan.py`)

- **Состав:** 11 607 строк, 236 WARN, 4 ERROR. Отдельно 2 ошибки OpenGL `GL_INVALID_ENUM`: строки 575–576, в 00:29:33–34, в Overworld.
- **ERROR:**
  - строка 95: 401 от авторизации (лаунчер);
  - строка 127: Embeddium «tainted»;
  - строка 217: Xaero «Online mod data expired»;
  - строка 259: «GET request failed 301».
- **«Can't keep up»:** 4 случая, 40–44 тика (около 2,0–2,2 с), строки 395 / 2076 / 8450 / 10516. Связь с переходами между измерениями — гипотеза.
- **Сохранения:** при каждой паузе пишутся все 178 ServerLevel, всего 58 сохранений. Это 10 680 строк лога. По логу каждое сохранение занимает не больше 1–2 с (разрешение лога — секунда).
- **Дальность** подтверждена: прорисовка 19 (было 10), симуляция 12 (было 0). Шейдерпак BSL_v10.1.8, профиль ULTRA.
- **Смерти в лиминальных измерениях:**
  - падение в пустоту в конечных сценах `weather_forecast_room` и `daisy_living_room` (2 раза);
  - «разбился насмерть» в `unbroken_green_plain` и `cloud_desert_window`;
  - убит Partygoer и Plague Doctor;
  - утонул.

  Это материал для дизайна честных встреч.
- **Метрик в логе нет:** ни FPS, ни TPS/MSPT, ни RAM. Утверждать что-либо о производительности нельзя.

### Пробная сборка аддона: УСПЕШНО (`addon-proto/`)

- Использованы Forge MDK `1.20.1-47.4.10`, Gradle 8.8 и Temurin JDK 17. Mappings `official 1.20.1`.
- modId `liminalcraft`, пакет `dev.liminalcraft`. Мод выводит в лог `LIMINALCRAFT_ADDON_LOADED`.
- Зависимость в `mods.toml`: `liminalspaces` mandatory, `[2.1.2,)`, ordering AFTER, side BOTH. С JAR основного мода при сборке **не** компилировались.
- **Ошибка 429 от Maven Central.** Лечится зеркалом `https://maven-central.storage-download.googleapis.com/maven2/` в `settings.gradle`; это уже сделано.
- **Время сборки:** около 3 мин на холодный кеш, около 22 с на тёплый. Gradle-кеш занимает примерно 720 МБ.
- **Перед сборкой у себя** укажите путь к JDK 17 в `gradle.properties`. Пути из облака закомментированы.
- `liminalcraft-0.1.0-built-in-cloud.jar` — собранный в облаке JAR. **В игре не проверялся.**

## 4. Что не доделано (продолжать отсюда)

### Незавершённые задачи исследования

Скрипты лежат в `workflows/`. Пути внутри указывают на облачный scratchpad, их нужно поправить.

**Этап 1** (`liminal-stage1-audit-*.js`):
- Не завершена карточка `nested_libraries`: xaerolib, kuma-api (по карточке balm — внутри Balm), fabric-api-base, mixinextras, jcpp, kff*.
- Не начаты 9 тем:
  - `topic_embeddium_taint`;
  - `topic_shader_warnings`;
  - `topic_per_dimension_shaders`: **важно** для атмосферы по измерениям;
  - `topic_tick_lag_and_saves`;
  - `topic_gl_errors`;
  - `topic_optional_classes`;
  - `topic_launcher_auth`;
  - `topic_candidate_mods`: ModernFix, Entity Culling, Sound Physics Remastered, Spark;
  - `topic_asset_pipeline`: возможности Meshy API и открытые ассеты.
- **Перепроверка не проводилась ни для одной из 23 карточек.**

**Этап 2** (`liminal-stage2-understand-*.js`):
- Из 16 кандидатов бестиария нет ни одной готовой карточки. Карточка Smilers черновая, Hound была в работе.
- Кандидаты: Smilers (редизайн), Hound, Facelings, Deathmoths, Dullers, Skin-Stealer, The Windows, Drowners, Will o' Waves, Cuddlemares, The Neighborhood Watch, Necromobile, Mimic, Warning Kites, The Lonely Scarecrow, Transporters. Ссылки в `bestiary_index.json`.
- Перепроверка 7 отчётов по подсистемам и 2 по API не проводилась.

### Артефакты ТЗ, которые ещё не созданы

- `MOD_INVENTORY.csv` и `COMPATIBILITY_MATRIX.csv`. Данные для них — в `research/stage1/*.json` (поля file, modIds, versionInJar, license, side, dependencies, sources, knownIssues и др.).
- `LOG_FINDINGS.md`: сейчас это заглушка. Нужно заполнить по `LOG_INDEX.csv`, этому файлу и темам этапа 1.
- `ENTITY_CATALOG.md` и дополненный `ENTITY_AUDIT.csv` (параметры существ из `sub_sub_encounters_entities.json`).
- Дизайн-документы этапа 3:
  - `OVERWORLD_AND_LIMINAL_DESIGN.md`;
  - `STORY_DESIGN.md`;
  - `ADVANCEMENTS_PLAN.md`;
  - `ENTITY_DESIGN_BIBLE.md`;
  - `GENERATION_MODULES.md`;
  - `DEBUG_MENU_SPEC.md` и `DEBUG_MENU_TEST_PLAN.md`.
- Прототип по этапу 4 и `TEST_REPORT.md`.
- Обновлённый `AUDIT_REPORT.md` с поправками из §3.

### Рекомендуемый порядок

1. Получить от пользователя:
   - список `mods/`;
   - `config/`, особенно `liminalspaces-common.toml`, `liminalspaces-overhaul.toml`, Oculus, Embeddium;
   - SHA-256 его JAR основного мода;
   - ответ на вопрос из §2.
2. Довести исследование этапа 1 (9 тем и `nested_libraries`) и перепроверить ключевые утверждения. Затем выпустить `MOD_INVENTORY.csv`, `COMPATIBILITY_MATRIX.csv`, `LOG_FINDINGS.md` и исправленный `AUDIT_REPORT.md`.
3. Закончить карточки бестиария. Сверять источники на `backrooms-wiki.wikidot.com`, текст там под CC BY-SA 3.0, лицензию проверить.
4. Написать дизайн-документы этапа 3 и `DEBUG_MENU_SPEC.md`. API для них уже собраны в `api_api_gui.json` и `api_api_net_data.json`.
5. Сделать прототип по этапу 4 на основе `addon-proto/`. Собирать и проверять **в реальном экземпляре пользователя**, в отдельном профиле лаунчера и на копии мира. Предварительно сделать резервную копию.

## 5. Структура архива

```
HANDOFF.md                       этот файл
RESEARCH_SUMMARY_UNVERIFIED.md   сводная таблица по модам
repo-snapshot/                   содержимое ветки claude/stage1-audit
  AUDIT_REPORT.md, MODDING_PLAN.md, MODLOG.md, LOG_FINDINGS.md (заглушка)
  DIMENSION_MANIFEST.csv (175), ENTITY_AUDIT.csv (10), LOG_INDEX.csv (242)
  tools/extract_manifest.py, tools/log_scan.py
  docs/ORIGINAL_PROMPT_RU.txt    исходное ТЗ
research/stage1/                 23 карточки модов (JSON, без перепроверки)
research/stage2/                 7 отчётов по подсистемам, 3 по Forge API и сборке, индекс бестиария
research/stage2_partial/         черновая карточка Smilers
workflows/                       два скрипта оркестрации (пути облачные)
addon-proto/                     исходники пробного аддона и собранный JAR
log/latest_anonymised.log        анонимизированный лог пользователя
main-mod/README.md               как получить и дизассемблировать основной мод (JAR в архив не включён)
```

## 6. Правила ТЗ, о которых легко забыть

- Не выдумывать mod ID, классы, измерения и ссылки. Разделять статусы `VERIFIED FROM FILES`, `VERIFIED FROM WEB SOURCE` и `HYPOTHESIS`.
- Не менять основной сейв без проверенной резервной копии и явного разрешения. Не распространять JAR основного мода и извлечённые из него ресурсы.
- Не заявлять улучшение FPS без измерений. Успешная сборка ещё не значит готовность: GUI и debug-меню проверяются в реальной игре, а то, что не проверено, помечается NOT TESTED.
- Никогда не запускать две Gradle-сборки одновременно. Учитывать, что в dev-окружении используются имена Mojang, а в собранном JAR — SRG.
