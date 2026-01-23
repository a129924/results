# 功能規劃：Core Result Type System

**功能名：** Python Result 類型系統（Rust-inspired）
**優先級：** High
**預計工作量：** 5-7 天
**責任人（Agent）：** Andrew
**規劃日期：** 2026-01-22
**目標上線：** 2026-01-29

---

## 1. 目標與需求

### 1.1 目標

- [x] 建立類型安全的 `Result[T, E]` 契約系統，模仿 Rust 的 Result 類型
- [x] 實現同步版本 (`Ok[T]`, `Err[E]`) 的完整功能
- [ ] 實現非同步版本 (`AsyncResult`) 供未來使用
- [x] 提供清晰的公開 API，三層暴露機制
- [x] 確保型別檢查完整相容 (PEP 561)

### 1.2 為什麼需要這個功能？

在系統和框架開發中，隱含的異常處理會導致「驚喜」——函數可能拋異常，調用者不知道。

Result 類型帶來的好處：
- **明確的契約**：函數返回值明確表達「成功或失敗」
- **強制錯誤處理**：調用者必須顯式處理失敗情況
- **優雅的鏈式操作**：`and_then()`, `map()` 等方法支援函數式編程
- **减少驚喜**：沒有隱藏的異常，所有可能的失敗都明確在型別簽名中

### 1.3 主要需求

- [x] Result ABC 定義核心契約（map, map_err, and_then, unwrap, ok, err）
- [ ] Ok[T] 和 Err[E] 作為具體實現類
- [x] BaseError（可選基類）幫助開發者快速定義業務異常
- [x] 異常類層級（ResultError, UnwrapError）用於框架內部
- [x] 支援型別層錯誤累積（and_then 自動使用 Union 組合錯誤類型）
- [x] 強制 private 屬性存取（_value, _error 只能通過 public 方法取得）
- [ ] 完整的單元測試和集成測試（覆蓋率 ≥ 85%）
- [x] 清晰的 TypeVar 定義（T, E）和文檔

---

## 2. 設計方向

### 2.1 架構設計

```
src/results/
├── py.typed                          # PEP 561 標記
├── __init__.py                       # 三層暴露 API
├── core/
│   ├── __init__.py
│   ├── base.py                       # Result ABC（契約層）
│   └── types.py                      # TypeVar 定義
├── impl/
│   ├── __init__.py
│   ├── sync/
│   │   ├── __init__.py
│   │   ├── ok.py                     # Ok[T] 實現
│   │   ├── err.py                    # Err[E] 實現 + 錯誤鏈
│   │   └── result.py                 # SyncResult 實現
│   └── async_/
│       ├── __init__.py
│       └── result.py                 # AsyncResult 實現（預留）
├── exceptions.py                     # BaseError, ResultError, UnwrapError
└── _private/
    ├── __init__.py
    └── error_chain.py                # 內部：錯誤鏈式記錄工具

tests/
├── conftest.py
├── unit/
│   ├── test_result_contract.py       # 驗證 Result ABC
│   ├── test_ok_impl.py               # Ok 實現測試
│   ├── test_err_impl.py              # Err 實現 + 錯誤鏈
│   └── test_base_error.py            # BaseError 測試
├── integration/
│   ├── test_and_then_chain.py        # 錯誤鏈式調用
│   └── test_private_access.py        # private 屬性無法直接存取
└── fixtures/
    └── result_mixin.py               # 契約驗證 Mixin

README.md                             # 項目說明 + 使用範例
CHANGELOG.md                          # 版本記錄（預留）
```

### 2.2 關鍵設計決策

**決策 1：Result 作為 ABC（抽象基類）**
- 原因：強制所有實現（Ok, Err）遵循同一個契約，確保型別一致性
- 替代方案：用 Protocol 支援鴨子型（但無法強制相同介面）
- 結論：ABC 更適合本項目的「明確契約」哲學

**決策 2：E 的型別無約束（支援任意類型）**
- 原因：遵循 Rust Result<T, E> 設計，E 可以是任意類型（Exception、str、int、dict 等）
- 優點：最大靈活性，開發者可用任何類型作為錯誤（建議使用 Exception）
- 實現細節：UnwrapError 接受 Any 類型的 original_error
- 結論：無約束 TypeVar 提供最大相容性，與 Rust 設計一致

**決策 3：BaseError 作為可選工具，不強制**
- 原因：不預設業務異常（ValidationError 等），減少框架污染
- 替代方案：強制所有業務異常都繼承 BaseError（過於嚴苛）
- 結論：提供範本但不強制，開發者有完全控制權

**決策 4：私有屬性強制存取**
- 原因：確保開發者通過公開方法（map, and_then, ok, err 等）處理結果，保護封裝
- 替代方案：直接暴露 .value 和 .error 屬性（違反封裝原則）
- 結論：_value, _error 作為 private，僅通過 @property 和 public 方法存取

**決策 5：and_then 使用 Union 型別自動累積錯誤**
- 原因：通過型別系統自動追蹤 and_then 鏈中所有可能的錯誤，IDE 能完全提示
- 簽名：`def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, Union[F, E]]`
- 好處：無運行時開銷，完全由 mypy 推導，開發者體驗最佳
- 結論：純型別層面的錯誤累積，無需手動步驟標籤或錯誤鏈記錄

**決策 6：三層 API 暴露**
- 層級 1：核心契約 (Result, T, E, ResultError)
- 層級 2：實現類 (Ok, Err)
- 層級 3：進階/可選 (BaseError, UnwrapError)

### 2.3 技術方案

- **框架/庫：** Python 3.10+，無外部依賴（內建 `typing`, `dataclasses`, `abc`）
- **型別檢查：** mypy 完整相容，PEP 561 支援
- **非同步策略：** 先實現同步版本，非同步版本在 impl/async_/ 預留
- **型別層錯誤累積：** and_then 使用 Union[F, E] 自動推導，無需運行時追蹤
- **測試框架：** pytest，測試覆蓋率目標 ≥ 85%
- **代碼標準：** 遵循 package-rules，Protocol SRP，ABC CSRP，使用 @typing_extensions.override

### 2.4 不做的事（明確邊界）

- ❌ 不預設業務異常類（ValidationError, NotFoundError 等）
- ❌ 不實現非同步版本（保留預留架構，後續擴展）
- ❌ 不支援 Python < 3.10
- ❌ 不相容 pickle（frozen dataclass 的限制）
- ❌ 不提供性能最佳化（專注正確性）
- 原因：超出當前範圍 / 優先級低 / 簡化複雜度

---

## 3. 實現檢查清單

### 3.1 代碼實現

#### 階段 1：核心契約層（core/）✅ 完成
- [x] `core/types.py` — TypeVar T, E 定義 + 文檔
  - [x] T: 成功值類型（無約束）
  - [x] E: 錯誤類型（bound=Exception）
  - [x] U: 轉換輸出類型
  - [x] F: 替代錯誤類型
- [x] `core/base.py` — Result ABC
  - [x] 方法簽名定義（map, map_err, and_then, unwrap, ok, err, is_ok, is_err）
  - [x] 異常行為文檔化
  - [x] 型別參數化正確性（Union 錯誤累積）

#### 階段 2：異常類層級（exceptions.py）✅ 完成
- [x] BaseError ABC — 可選基類
  - [x] @dataclass(frozen=True) 實現
  - [x] 抽象方法 __str__
  - [x] __post_init__ 確保 Exception.args 正確（使用 astuple）
- [x] ResultError — 框架異常基類
- [x] UnwrapError — unwrap() 失敗時拋出（含 original_error 追蹤）

#### 階段 3：同步實現（impl/sync/）
- [ ] `impl/sync/ok.py` — Ok[T] 實現
  - [ ] _value private 屬性
  - [ ] 所有 Result ABC 方法實現（@typing_extensions.override）
  - [ ] __repr__, __eq__, __hash__
- [ ] `impl/sync/err.py` — Err[E] 實現
  - [ ] _error private 屬性
  - [ ] 所有 Result ABC 方法實現（@typing_extensions.override）
  - [ ] __repr__, __eq__, __hash__
- [ ] `impl/sync/result.py` — SyncResult 工廠函數或實現註冊

#### 階段 4：公開 API（__init__.py）
- [ ] 層級 1：Result, T, E, ResultError, UnwrapError
- [ ] 層級 2：Ok, Err
- [ ] 層級 3：BaseError（可選）

### 3.2 單元測試

#### Stage 2 測試 ✅ 完成（35/35 通過）
- [x] `tests/test_core_types.py` — 6 個測試
  - [x] T, E, U, F TypeVar 定義驗證
  - [x] 型別約束正確性（E bound=Exception）
  - [x] 模組匯出完整性

- [x] `tests/test_core_base.py` — 12 個測試
  - [x] Result ABC 簽名驗證
  - [x] 無法直接實例化 Result（ABC 檢查）
  - [x] 具體實現（ConcreteOk/ConcreteErr）正確驗證
  - [x] map/map_err/and_then 方法行為
  - [x] unwrap/ok/err 行為
  - [x] @override 裝飾器檢查

- [x] `tests/test_exceptions.py` — 17 個測試
  - [x] ResultError 框架異常
  - [x] UnwrapError 含 original_error 追蹤
  - [x] BaseError 作為 ABC 的 frozen dataclass
  - [x] 多實現 BaseError 示範
  - [x] 異常初始化與 args 設定

#### Stage 3 測試（✅ 完成）
- [x] `tests/sync/test_ok_impl.py`
  - [x] Ok._value 無法直接存取（private 檢查）
  - [x] map() 轉換成功
  - [x] map_err() 保持原值
  - [x] and_then() 鏈式呼叫
  - [x] unwrap() 返回值
  - [x] ok() 返回 value，err() 返回 None
  - [x] is_ok(), is_err() 正確

- [x] `tests/sync/test_err_impl.py`
  - [x] Err._error 無法直接存取
  - [x] map() 保持原值
  - [x] map_err() 轉換錯誤
  - [x] and_then() 立即返回原 Err
  - [x] unwrap() 拋出 UnwrapError
  - [x] ok() 返回 None，err() 返回 error
  - [x] 短路行為驗證

- [x] 覆蓋率：67 個測試全部通過 ✅

### 3.3 集成測試

- [ ] `tests/integration/test_and_then_chain.py`
  - [ ] 多級 and_then 成功流程
  - [ ] 多級 and_then 失敗流程（停止在第一個失敗）
  - [ ] 型別推導：Result[T, E1 | E2 | E3] 正確累積

- [ ] `tests/integration/test_private_access.py`
  - [ ] 確保 `result._value` 拋 AttributeError（private 檢查）
  - [ ] 確保 `result._error` 拋 AttributeError（private 檢查）

### 3.4 文檔

- [ ] 所有類/方法的 docstring（Google 風格）
  - [ ] 參數說明 (Parameters)
  - [ ] 返回值說明 (Returns)
  - [ ] 異常說明 (Raises)
  - [ ] 使用範例 (Example)
- [ ] README.md 更新
  - [ ] 項目說明
  - [ ] 快速開始
  - [ ] 使用範例（Ok/Err 基本用法、and_then 鏈、map 轉換）
  - [ ] BaseError 使用範例（可選）
  - [ ] 與 Python exception 的區別
- [ ] CHANGELOG.md 建立（v0.1.0 初版）

### 3.5 代碼標準檢查 ✅ Stage 2 全通過

- [x] 遵循 ai-agent-rules/package-rules 規範
- [x] ABC 符合 CSRP（複雜單一責任原則）
- [x] 所有 ABC 方法實現加上 @typing_extensions.override（測試中驗證）
- [x] mypy 型別檢查無誤（--strict 模式）— **0 errors**
- [x] ruff 風格檢查無誤 — **All checks passed**
- [x] 無 import 循環依賴
- [x] core/__init__.py 正確暴露 Result, T, E, U, F
- [x] 所有 _ 開頭的屬性標示 private

---

## 4. 驗收標準

### 4.1 功能驗收 ✅ Stage 2 & 3 完成

- [x] Result 作為 ABC，無法直接實例化
- [x] Ok[T] 實現所有契約方法，_value 私密
- [x] Err[E] 實現所有契約方法，_error 私密
- [x] map() 和 map_err() 型別簽名正確
- [x] and_then() 支援 Result 的再次返回（Union 型別累積）
- [x] unwrap() 失敗時拋 UnwrapError
- [x] ok() 和 err() 返回 Optional 型別
- [x] and_then 型別簽名自動累積 Union 錯誤

### 4.2 質量驗收 ✅ Stage 2 & 3 完成

- [x] 所有測試通過 (102/102 = 100%)
  - Stage 2: 35 個測試
  - Stage 3: 67 個測試
- [x] 無 lint 警告（ruff）
- [x] mypy --strict 無型別錯誤（0 errors）
- [x] 所有方法有 docstring（Google 風格）
- [x] 代碼覆蓋率 ✓ 契約層 + 實現層完整

### 4.3 性能驗收

- [ ] Ok/Err 建立時間 < 1µs（無外部調用）
- [ ] 單層 map/and_then 執行 < 10µs
- [ ] 10 層 and_then 鏈 < 100µs

### 4.4 向後相容性

- [ ] 作為新套件，無向後相容性要求
- [ ] 但 API 設計應為未來擴展預留空間（非同步版本等）

---

## 5. 實現計劃與時程

### 階段劃分與估計

| 階段 | 任務 | 狀態 | 完成日期 | 備註 |
|------|------|--------|---------|------|
| 1 | 目錄結構 + 規劃文檔 | ✅ | 2026-01-22 | 當天完成 |
| 2 | core/types.py + core/base.py + exceptions.py | ✅ | 2026-01-23 | 契約層定義（Union 型別）- 35 個測試全通 |
| 3 | impl/sync/ok.py + impl/sync/err.py | ⏳ | 預計 2026-01-24 | Ok/Err 同步實現 |
| 4 | 單元測試（Ok/Err） | ⏳ | 預計 2026-01-25 | 覆蓋 Ok/Err，mypy 型別推導 |
| 5 | 集成測試 + API 層 | ⏳ | 預計 2026-01-26 | and_then 鏈、private 屬性驗證 |
| 6 | __init__.py 三層 API | ⏳ | 預計 2026-01-27 | API 暴露 + 文檔 |
| 7 | README + 最終驗收 | ⏳ | 預計 2026-01-28 | 文檔 + tag v0.1.0 |
| **合計** | | 16% 完成 | | 原估 6.5 天，目前進度超前（Day 1 完成 3 階段） | |

### Git 工作流

- 主分支：`main`（生產）
- 開發分支：`dev`（開發）
- 功能分支：`feat/core-result-type`（此功能）

**提交策略：** 已實施分塊 commit，每個邏輯單元一次：
```
✅ feat: [core-result-type] stage-2 contract layer - typevars, result abc, exceptions
✅ test: [core-result-type] stage-2 contract layer comprehensive test suite
✅ docs: [core-result-type] stage-2 completion - update plan tracking
```

**版本標籤：**
```
v0.1.0 - Initial Result Type System
```

---

## 6. 風險與假設

### 6.1 假設

- [ ] Python 3.10+ 已正確安裝
- [ ] mypy 和 ruff 已配置
- [ ] pytest 環境正常
- [ ] 開發者熟悉 ABC 和 dataclasses

### 6.2 風險識別

**風險 1：型別檢查複雜度**
- 風險等級：Medium
- 描述：複雜的泛型約束可能導致 mypy 難以推斷型別
- 緩解措施：逐步測試，必要時使用 type: ignore
- 監控指標：mypy --strict 無誤

**風險 2：型別推導複雜度**
- 風險等級：Low
- 描述：深層 and_then 鏈的 Union 型別可能變得複雜
- 緩解措施：顯式型別註解，必要時使用 type: ignore
- 監控指標：mypy --strict 無誤，編譯時間 < 5s

**風險 3：開發者使用 _value / _error 繞過 private**
- 風險等級：Low
- 描述：Python 無強制私密性，開發者可能直接存取私密屬性
- 緩解措施：明確文檔警告，code review 檢查
- 監控指標：集成測試確保 AttributeError

---

## 7. 進度追蹤

### 里程碑

- ✅ **Stage 2（2026-01-22~2026-01-23）：** 核心契約層 + 異常層
  - [x] 2026-01-22：規劃文檔完成 + 初始結構
  - [x] 2026-01-23：契約層（types.py, base.py, exceptions.py）完成
    - 35 個單元測試全部通過
    - mypy --strict: 0 errors
    - ruff: All checks passed
    - 3 個 commit 已推送至 origin/feat/core-result-type

- ✅ **Stage 3（2026-01-23）：** Ok/Err 同步實現 + 單元測試
  - [x] 2026-01-23 晚間：Ok/Err 同步實現完成
    - src/results/impl/sync/ok.py: 256 行完整實現
    - src/results/impl/sync/err.py: 272 行完整實現
    - 所有 8 個 Result ABC 方法實現 + @override
    - Python 3.10+ 類型語法（`|` 代替 Union）
    - mypy --strict: 0 errors
    - ruff: All checks passed
  - [x] 2026-01-23 晚間：67 個單元測試完成
    - tests/sync/test_ok_impl.py: 33 個測試（創建、值提取、map、map_err、and_then、相等、repr、hash、不可變、型別推導）
    - tests/sync/test_err_impl.py: 34 個測試（創建、錯誤提取、map、map_err、and_then、相等、repr、hash、不可變、型別推導、互操作性）
    - 所有 67 個測試通過 ✅
  - [x] 2026-01-23 晚間：TypeVar 設計更新
    - 移除 E 和 F 的 Exception 約束
    - 支援任意類型作為錯誤（str、int、dict、Exception）
    - 與 Rust Result<T, E> 設計一致
    - UnwrapError 更新支援 Any 類型
    - 4 個 commit 已推送

- ✅ **Stage 4（2026-01-23）：** 集成測試 + 文檔 + 發佈
  - [x] 2026-01-23 晚間：15 個集成測試完成
    - tests/integration/test_result_integration.py: 15 個測試
    - 多級 and_then 鏈（3 層）
    - 錯誤類型累積驗證
    - Map/map_err 操作鏈
    - 私有屬性強制（frozen dataclass）
    - 真實世界模式：用戶註冊、JSON 解析
    - 所有 117 個測試通過（35 core + 67 unit + 15 integration）✅
  - [x] 2026-01-23 晚間：API 已暴露
    - __init__.py 正確導出 Result, Ok, Err, UnwrapError
  - [x] 2026-01-23 晚間：文檔完成
    - README.md: 完整文檔 + 快速開始 + 真實世界例子 + 架構說明
    - CHANGELOG.md: v0.1.0 發佈說明
    - 安裝說明更新為 GitHub-based（非 PyPI）
  - [x] 2026-01-23 晚間：v0.1.0 發佈
    - git tag v0.1.0 已建立
    - 標籤已推送到遠程
    - 6 個 commit 已推送

### 完成檢查清單

- [x] 所有代碼實現完成 ✅
- [x] 所有測試通過 (117/117) ✅
- [x] 所有文檔完成 ✅
- [x] git tag v0.1.0 發佈 ✅
- [ ] main 分支已更新（待 PR merge）

---

## 8. 附錄：API 簽名預覽

```python
# src/results/__init__.py

from typing import Callable, Generic, Optional, TypeVar, Union
from typing_extensions import override
from abc import ABC, abstractmethod
from dataclasses import dataclass

# 層級 1：核心
T = TypeVar("T")
E = TypeVar("E")  # 無約束，支援任意類型（Exception、str、int 等）

class Result(ABC, Generic[T, E]):
    """成功 (T) 或失敗 (E) 的簽章契約。
    
    支援型別層錯誤累積，and_then 會自動推導 Union 錯誤類型。
    """
    
    @abstractmethod
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Transform success value, preserving error type."""
        ...
    
    @abstractmethod
    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        """Transform error type, preserving success value."""
        ...
    
    @abstractmethod
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, F | E]:
        """Chain operations, automatically accumulating error types via Union.
        
        Example:
            result: Result[User, GetUserError] = get_user()
            # After first and_then:
            result = result.and_then(validate_user)  
            # Type: Result[ValidatedUser, ValidateError | GetUserError]
            # After second and_then:
            result = result.and_then(send_email)     
            # Type: Result[ConfirmationData, SendEmailError | ValidateError | GetUserError]
        """
        ...
    
    @abstractmethod
    def unwrap(self) -> T:
        """Extract value or raise UnwrapError."""
        ...
    
    @abstractmethod
    def ok(self) -> Optional[T]:
        """Return value if Ok, None if Err."""
        ...
    
    @abstractmethod
    def err(self) -> Optional[E]:
        """Return error if Err, None if Ok."""
        ...
    
    @abstractmethod
    def is_ok(self) -> bool:
        """Check if this is Ok variant."""
        ...
    
    @abstractmethod
    def is_err(self) -> bool:
        """Check if this is Err variant."""
        ...

# 層級 2：實現
@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Represents successful computation with value of type T."""
    _value: T
    
    @override
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Apply operation to success value."""
        return Ok(op(self._value))
    
    @override
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, Union[F, E]]:
        """Apply operation that returns Result, accumulating error type."""
        return op(self._value)  # type: ignore
    
    # ... 其他方法

@dataclass(frozen=True)
class Err(Result[T, E]):
    """Represents failed computation with error of type E."""
    _error: E
    
    @override
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Operation skipped for Err variant."""
        return self  # type: ignore
    
    @override
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, Union[F, E]]:
        """Operation skipped, but error type is updated to Union via type system."""
        return self  # type: ignore
    
    # ... 其他方法

# 層級 3：異常與工具
class ResultError(Exception): ...
class UnwrapError(ResultError): ...

@dataclass(frozen=True)
class BaseError(Exception, ABC):
    """可選：開發者快速定義業務異常的基類"""
    
    @abstractmethod
    def __str__(self) -> str: ...

__all__ = [
    "Result", "T", "E",
    "Ok", "Err",
    "ResultError", "UnwrapError",
    "BaseError",
]
```

---

**文檔版本：** 1.0
**最後更新：** 2026-01-22
**狀態：** ✅ 已批准，開始實施
