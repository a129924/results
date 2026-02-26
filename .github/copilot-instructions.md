# GitHub Copilot Agent 指令 — Results 專案

Rust 啟發的 Result 型別（Python 3.10+）。當前分支 `dev`。

---

## 目錄架構設計思維

**功能優先分組 + 技術細分：**

### 核心設計原則

1. **功能優先分組** — 按「功能」（如 result、maybe、either 等）分組，再按「實現技術」細分
   - 每個功能都在獨立目錄下（result/、maybe/、either/ 等）
   - 多個技術實現放在同級子目錄（sync/、asyncio/ 等）
   - 新增實現技術時無需修改頂層結構（Open/Closed 原則）

2. **契約層（core/）** — 定義所有實現的 ABC 契約
   - `base.py`：Result[T, E] 抽象類（23 個方法必須實現）
   - `types.py`：TypeVar、共用型別
   - `exceptions.py`：例外定義
   - 所有實現都必須遵循此契約（Liskov 替換原則）

3. **實現層（result/sync、result/asyncio 等）** — 按技術分組，各層獨立實現
   - `sync/` — 同步實現（Ok、Err）
   - `asyncio/` — 非同步實現（AsyncResult）
   - 同技術內的模塊可互相依賴，但不可反向依賴契約層

4. **公開 API（層級 2 暴露）** — 在 `__init__.py` 暴露必要類型
   - 只暴露使用者需要的類型（Ok、Err、AsyncResult）
   - 隱藏實現細節（result/ 內部）
   - 隱藏工具代碼（_private/ 前綴）

### 架構範例

```
src/results/
├── core/              # 共用契約層
│   ├── base.py       # ABC 定義
│   ├── types.py      # 型別定義
│   └── exceptions.py # 異常定義
├── result/           # Result 功能族群
│   ├── __init__.py  # 導出 Ok、Err、AsyncResult
│   ├── sync/        # 同步實現
│   │   ├── ok.py
│   │   └── err.py
│   └── asyncio/     # 異步實現
│       └── result.py
├── maybe/           # Maybe 功能族群（未來）
├── either/          # Either 功能族群（未來）
└── common/          # 共用工具
```

### 架構好處

- **一致性** — 使用者查找直覺（from results import Ok）
- **可擴展** — 新增功能時自動適用相同模式（如 maybe/、either/）
- **低耦合** — 實現層之間零依賴
- **易測試** — ABC 契約便於 Mock 和驗證

**測試鏡像源代碼結構：**
- `tests/sync/` ↔ `src/results/result/sync/`
- `tests/asyncio/` ↔ `src/results/result/asyncio/`（未來）
- `tests/integration/` ↔ 跨模塊整合
- `tests/test_core_*.py` ↔ `src/results/core/`

## 編碼必須遵循

| 項目 | 規則 |
|-----|------|
| **不可變** | `@dataclass(frozen=True)` — 禁用 `__slots__` |
| **方法實現** | 所有公開方法 `@override`（含型別註解） |
| **型別註解** | mypy --strict：禁止 `Any`、隱式 `Optional` |
| **Docstring** | 每個公開方法必有（格式：說明 + Args + Returns + Examples） |
| **上下文鏈** | Err 僅用 `_context_chain: tuple[str, ...] = field(default_factory=tuple, init=False, repr=False)` |

---

## Git 規範

**分支**：`dev` 主開發 → `feature/*` / `fix/*` → `release/<version>` → `hotfix/*`  
**規則**：實現時**必須開新 branch**（禁止直接在 dev 上修改）

**提交**：Conventional Commits — `<type>(<scope>): <subject>` + body（說明為什麼）  
types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`  
例：`feat(async): add AsyncResult with context chain`

**標籤**：`v<MAJOR>.<MINOR>.<PATCH>` — SemVer 2.0.0

---

## 測試規範

| 層級 | 比例 | 檔案命名 | 規則 |
|-----|------|---------|------|
| Unit | 70% | `test_*_base.py`, `test_*_impl.py` | `test_<method>_<scenario>_<expected>() -> None` |
| Integration | 20% | `test_*_integration.py` | 檢驗模塊間互動 |
| E2E | 10% | `test_async_*_real_world.py` | 端到端場景 |

**異步**：`@pytest.mark.asyncio` + `async def`  
**覆蓋率**：整體 ≥80%、core/ ≥90%、impl/ ≥75%  
**配置**：`[tool.pytest.ini_options] asyncio_mode = "auto"`

---

## Pyright（嚴格模式）

```bash
uv run pyright src/results/        # 0 errors 必須
uv run pyright tests/              # 測試層檢查（可寬鬆）
```

**核心代碼** (`src/results/`)：strict 模式，0 errors  
**類型檢查規則**：
- ✅ 禁止 `Any`、未標注參數、隱式 Optional
- ✅ 所有方法簽名完整，含返回類型
- ⚠️ 唯一例外：`# type: ignore[error-code]  # 理由：...`（必須說明為何需要）

**type: ignore 使用**：  
必須通過 `[error-code]` 指定特定錯誤，並添加理由註解。不允許無註解的 `# type: ignore`。

---

## Ruff

```bash
uv run ruff check src/results/ tests/  # 無 errors
uv run ruff format src/results/ tests/
uv run ruff check src/results/ tests/  # 二次確認
```

**Rules**：E, W, F, I, B, C4, UP  
**Ignore**：E501(行長), B008(函數默認), C901(複雜度), W191(tab)

---

## Code Style

| 項目 | 規則 |
|-----|------|
| 類/常數/函數 | `PascalCase` / `UPPER_SNAKE` / `snake_case` |
| 私有 | `_` 前綴 |
| 行長 | 88 字（建議）/ 100（硬限） |
| 導入 | 標準庫 → 第三方 → 本地（各組空行分隔，字母序） |
| 空行 | 類前後 2 行、方法間 1 行、邏輯段 1 行 |
| 多行 | 所有參數對齊到 `(` 下 |

---

## 開發環境與版本一致性

**套件管理**：**必須使用 `uv`**（而非 pip）
```bash
uv sync              # 安裝開發依賴
uv run pytest        # 執行測試
```

**版本一致性檢查**（完成階段或需求時必須執行）

三個版本號必須保持一致：
1. `pyproject.toml`：`version = "0.3.1"`
2. `src/results/__init__.py`：`__version__ = "0.3.1"`
3. `git tag`：`v0.3.1`（已發佈時）

**驗證命令**：
```bash
grep 'version = ' pyproject.toml
grep '__version__' src/results/__init__.py
git describe --tags
# 確保三者一致
```

---

## 提交前檢查清單

```
[ ] 在新 branch 上開發（禁止直接在 dev 修改）
[ ] uv run pyright src/results/
[ ] uv run ruff check src/results/ tests/
[ ] uv run ruff format src/results/ tests/
[ ] uv run pytest tests/ --cov=src/results (≥80%)
[ ] @override 用於所有公開方法
[ ] 完整的型別註解 + docstring
```

## 階段完成檢查清單

```
[ ] 驗證版本號一致（pyproject.toml、__init__.py、git tag）
[ ] 所有提交前檢查都通過
[ ] 功能測試完成
[ ] CHANGELOG.md 已更新
[ ] Merge PR 回 dev
```

---

## Markdown 檔案位置規範

### Root 目錄必須存在的 Markdown

| 檔案 | 用途 | 規則 |
|-----|------|------|
| **README.md** | 專案說明、快速開始 | 必須（英文主版本） |
| **CHANGELOG.md** | 版本變更紀錄 | **版本更新必須記錄**（Keep a Changelog 格式） |
| **README.zh-TW.md** | 中文版本文檔 | 可選（如需多語言） |

### 不應在 Root 存在的 Markdown

| 檔案 | 應放位置 |
|-----|--------|
| 開發規範 | `.github/copilot-instructions.md` |
| 貢獻指南 | `docs/CONTRIBUTING.md` 或 `.github/` |
| 部署說明 | `docs/deployment.md` |
| 架構文檔 | `docs/architecture.md` |

**規則：** Root 只放核心文檔（README、CHANGELOG）；規範、指南放 `.github/` 或 `docs/`

---

## 版本更新流程

1. **修改版本號**（三處同步）
   - `pyproject.toml`: `version = "0.3.1"`
   - `src/results/__init__.py`: `__version__ = "0.3.1"`

2. **記錄變更** — 在 `CHANGELOG.md` 更新（必須）
   ```markdown
   ## [0.4.0] - 2026-02-10
   
   ### Added
   - New feature description
   
   ### Changed
   - Changed behavior description
   
   ### Fixed
   - Bug fix description
   ```

3. **提交 & 打標籤**
   ```bash
   git commit -m "chore: bump version to 0.4.0"
   git tag -a v0.4.0 -m "Release v0.4.0"
   git push origin v0.4.0
   ```

---

**v1.1.0 | 2026-02-05**