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

- [ ] 建立類型安全的 `Result[T, E]` 契約系統，模仿 Rust 的 Result 類型
- [ ] 實現同步版本 (`Ok[T]`, `Err[E]`) 的完整功能
- [ ] 實現非同步版本 (`AsyncResult`) 供未來使用
- [ ] 提供清晰的公開 API，三層暴露機制
- [ ] 確保型別檢查完整相容 (PEP 561)

### 1.2 為什麼需要這個功能？

在系統和框架開發中，隱含的異常處理會導致「驚喜」——函數可能拋異常，調用者不知道。

Result 類型帶來的好處：
- **明確的契約**：函數返回值明確表達「成功或失敗」
- **強制錯誤處理**：調用者必須顯式處理失敗情況
- **優雅的鏈式操作**：`and_then()`, `map()` 等方法支援函數式編程
- **减少驚喜**：沒有隱藏的異常，所有可能的失敗都明確在型別簽名中

### 1.3 主要需求

- [ ] Result ABC 定義核心契約（map, map_err, and_then, unwrap, ok, err）
- [ ] Ok[T] 和 Err[E] 作為具體實現類
- [ ] BaseError（可選基類）幫助開發者快速定義業務異常
- [ ] 異常類層級（ResultError, UnwrapError）用於框架內部
- [ ] 支援型別層錯誤累積（and_then 自動使用 Union 組合錯誤類型）
- [ ] 強制 private 屬性存取（_value, _error 只能通過 public 方法取得）
- [ ] 完整的單元測試和集成測試（覆蓋率 ≥ 85%）
- [ ] 清晰的 TypeVar 定義（T, E）和文檔

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

**決策 2：E 的型別約束為 `Exception`**
- 原因：所有業務異常都應該是 Exception 子類，方便 logging/traceback
- 替代方案：無約束 TypeVar（過於寬鬆，無法保證異常可被處理）
- 結論：`E = TypeVar("E", bound=Exception)` 是最佳平衡

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

#### 階段 1：核心契約層（core/）
- [ ] `core/types.py` — TypeVar T, E 定義 + 文檔
- [ ] `core/base.py` — Result ABC
  - [ ] 方法簽名定義（map, map_err, and_then, unwrap, ok, err, is_ok, is_err）
  - [ ] 異常行為文檔化
  - [ ] 型別參數化正確性

#### 階段 2：異常類層級（exceptions.py）
- [ ] BaseError ABC — 可選基類
  - [ ] @dataclass(frozen=True) 實現
  - [ ] 抽象方法 __str__
  - [ ] __post_init__ 確保 Exception.args 正確
- [ ] ResultError — 框架異常基類
- [ ] UnwrapError — unwrap() 失敗時拋出

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

- [ ] `tests/unit/test_result_contract.py`
  - [ ] Result ABC 簽名驗證
  - [ ] 無法直接實例化 Result（ABC 檢查）
  - [ ] Ok/Err 是否正確實現契約（Mixin 驗證）

- [ ] `tests/unit/test_ok_impl.py`
  - [ ] Ok._value 無法直接存取（private 檢查）
  - [ ] map() 轉換成功
  - [ ] map_err() 保持原值
  - [ ] and_then() 鏈式呼叫
  - [ ] unwrap() 返回值
  - [ ] ok() 返回 Some(value)，err() 返回 None
  - [ ] is_ok(), is_err() 正確

- [ ] `tests/unit/test_err_impl.py`
  - [ ] Err._error 無法直接存取
  - [ ] map() 保持原值
  - [ ] map_err() 轉換錯誤
  - [ ] and_then() 立即返回原 Err
  - [ ] unwrap() 拋出 UnwrapError
  - [ ] ok() 返回 None，err() 返回 Some(error)
  - [ ] 錯誤鏈記錄（_context 更新）

- [ ] `tests/unit/test_base_error.py`
  - [ ] BaseError 無法直接實例化（ABC 檢查）
  - [ ] 開發者自訂異常繼承 BaseError
  - [ ] __str__ 正確實現
  - [ ] Exception.args 正確初始化

- [ ] 覆蓋率 ≥ 85%

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

### 3.5 代碼標準檢查

- [ ] 遵循 ai-agent-rules/package-rules 規範
- [ ] Protocol 符合 SRP（單一職責原則）
- [ ] ABC 符合 CSRP（複雜單一責任原則）
- [ ] 所有 ABC 方法實現加上 @typing_extensions.override
- [ ] mypy 型別檢查無誤（--strict 模式）
- [ ] ruff 風格檢查無誤
- [ ] 無 import 循環依賴
- [ ] 所有 public API 在 __init__.py 暴露
- [ ] 所有 _ 開頭的屬性標示 private（不在 __all__ 中）

---

## 4. 驗收標準

### 4.1 功能驗收

- [ ] Result 作為 ABC，無法直接實例化
- [ ] Ok[T] 實現所有契約方法，_value 私密
- [ ] Err[E] 實現所有契約方法，_error 私密
- [ ] map() 和 map_err() 型別正確轉換
- [ ] and_then() 支援 Result 的再次返回
- [ ] unwrap() 成功時返回值，失敗時拋 UnwrapError
- [ ] ok() 和 err() 返回 Optional
- [ ] and_then 型別推導自動累積 Union 錯誤

### 4.2 質量驗收

- [ ] 所有測試通過 (100%)
- [ ] 代碼覆蓋率 ≥ 85%
- [ ] 無 lint 警告（ruff）
- [ ] mypy --strict 無型別錯誤
- [ ] 所有方法有 docstring

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

| 階段 | 任務 | 預計天數 | 備註 |
|------|------|--------|------|
| 1 | 目錄結構 + 規劃文檔 | 0.5 | 當天完成 |
| 2 | core/types.py + core/base.py | 1 | 契約層定義（Union 型別） |
| 3 | exceptions.py | 0.5 | 異常類 |
| 4 | impl/sync/ok.py | 1 | Ok 實現 |
| 5 | impl/sync/err.py | 1 | Err 實現（無錯誤鏈邏輯） |
| 6 | 單元測試（階段 4-5） | 2 | 覆蓋 Ok/Err，mypy 型別推導 |
| 7 | __init__.py + 文檔 | 1 | API 暴露 + README |
| **合計** | | 6.5 天 | |

### Git 工作流

- 主分支：`main`（生產）
- 開發分支：`dev`（開發）
- 功能分支：`feat/core-result-type`（此功能）

**提交策略：** 每個階段一次 commit，格式：
```
feat: [core-result-type] <task description>

- 具體實現內容
- 已通過測試
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

- 🔄 **Week 1（2026-01-22~01-29）：** 規劃 + 核心實現 + 測試
  - [ ] 2026-01-22：規劃文檔完成
  - [ ] 2026-01-23：契約層（core/types.py, core/base.py）完成
  - [ ] 2026-01-24：異常層（exceptions.py）完成
  - [ ] 2026-01-25：Ok/Err 同步實現完成
  - [ ] 2026-01-26：單元測試完成
  - [ ] 2026-01-27：集成測試 + 文檔完成
  - [ ] 2026-01-28：代碼標準檢查 + 微調
  - [ ] 2026-01-29：發佈 v0.1.0

### 完成檢查清單

- [ ] 所有代碼實現完成
- [ ] 所有測試通過
- [ ] 所有文檔完成
- [ ] git tag v0.1.0 發佈
- [ ] main 分支已更新

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
E = TypeVar("E", bound=Exception)

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
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, Union[F, E]]:
        """Chain operations, automatically accumulating error types via Union.
        
        Example:
            result: Result[User, GetUserError] = get_user()
            # After first and_then:
            result = result.and_then(validate_user)  
            # Type: Result[ValidatedUser, GetUserError | ValidateError]
            # After second and_then:
            result = result.and_then(send_email)     
            # Type: Result[ConfirmationData, GetUserError | ValidateError | SendEmailError]
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
