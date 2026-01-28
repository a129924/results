# Results: Rust 啟蒙的 Python Result 型別

[English](README.md) | [繁體中文](README.zh-TW.md)

一個型別安全、Pythonic 的實現，靈感源自 Rust 的 `Result<T, E>` 型別，提供優雅的錯誤處理和函數式編程。

[![Tests](https://img.shields.io/badge/tests-187%2F187-green)](https://github.com/a129924/results)
[![Type Checking](https://img.shields.io/badge/mypy%20%2D%2Dstrict-passing-green)](https://github.com/a129924/results)
[![Code Style](https://img.shields.io/badge/ruff-all%20checks%20passed-green)](https://github.com/a129924/results)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

## 🎯 概述

`results` 提供一個 **Result 型別**，代表成功（`Ok[T]`）或錯誤（`Err[E]`）。這樣消除了無聲的失敗，並通過型別系統確保顯式的錯誤處理。

```python
from results import Ok, Err, Result

def divide(x: int, y: int) -> Result[int, str]:
    """除以 y，或返回錯誤訊息。"""
    if y == 0:
        return Err("Cannot divide by zero")
    return Ok(x // y)

# 使用：顯式錯誤處理
result = divide(10, 2)
if result.is_ok():
    print(f"Result: {result.ok()}")  # Result: 5
else:
    print(f"Error: {result.err()}")
```

## ✨ 主要特性

- ✅ **型別安全契約** — Result ABC 強制一致的錯誤處理
- ✅ **函數式鏈接** — `map()`、`map_err()`、`and_then()` 實現優雅的組合
- ✅ **除錯工具** — `inspect()` 和 `inspect_err()` 非侵入式除錯
- ✅ **Context 鏈** — LIFO context 堆棧，提供豐富的錯誤診斷
- ✅ **非同步/等待支援** — `AsyncResult[T, E]` 用於非阻塞工作流
- ✅ **零運行時開銷** — 凍結的 dataclasses，無魔法
- ✅ **Python 3.10+ 原生** — 使用 PEP 604 union 語法（`|` 代替 `Union`）
- ✅ **靈活的錯誤型別** — 支援任何型別作為錯誤（Exception、str、int、dict 等）
- ✅ **全面測試** — 187 個測試涵蓋同步/非同步單元/整合情景

## 📦 安裝

### 本地開發

```bash
# 複製儲存庫
git clone https://github.com/a129924/results.git
cd results

# 使用 UV 安裝（推薦）
uv sync

# 或使用 pip
pip install -e ".[dev]"
```

### 用作依賴項

```bash
# 直接從 GitHub 安裝
pip install git+https://github.com/a129924/results.git

# 或使用 UV
uv add git+https://github.com/a129924/results.git
```

> **注意：** `results` 目前正在積極開發中，尚未發佈到 PyPI。它設計用於內部使用和受信任的合作者。用於生產環境，建議固定到特定版本標籤。

## 🚀 快速開始

### 基本用法

```python
from results import Ok, Err, Result

# 返回成功
result: Result[int, str] = Ok(42)
assert result.is_ok()
assert result.ok() == 42
assert result.err() is None

# 返回失敗
result: Result[int, str] = Err("operation failed")
assert result.is_err()
assert result.ok() is None
assert result.err() == "operation failed"
```

### 使用 `map()` 轉換值

```python
# 轉換成功值，保留錯誤型別
result = Ok(5).map(lambda x: x * 2).map(str)
assert result.ok() == "10"

# 錯誤原封不動地傳遞
error_result = Err("failed").map(lambda x: x * 2)
assert error_result.is_err()
assert error_result.err() == "failed"
```

### 使用 `map_err()` 處理錯誤

```python
# 轉換錯誤，同時保留成功值
result = Err(ValueError("parse failed")).map_err(
    lambda e: RuntimeError(f"Critical: {e}")
)
assert isinstance(result.err(), RuntimeError)

# Ok 值原封不動地傳遞
ok_result = Ok(42).map_err(RuntimeError)
assert ok_result.ok() == 42
```

### 使用 `and_then()` 鏈接操作

```python
def parse_int(s: str) -> Result[int, ValueError]:
    try:
        return Ok(int(s))
    except ValueError as e:
        return Err(e)

def validate_positive(x: int) -> Result[int, RuntimeError]:
    if x > 0:
        return Ok(x)
    return Err(RuntimeError("must be positive"))

# 鏈接多個操作
result = (
    parse_int("42")
    .and_then(validate_positive)
    .map(lambda x: x * 2)
)
assert result.ok() == 84

# 錯誤短路鏈
error_result = (
    parse_int("invalid")
    .and_then(validate_positive)  # 不調用
    .map(lambda x: x * 2)           # 不調用
)
assert error_result.is_err()
assert isinstance(error_result.err(), ValueError)
```

## 🔗 真實世界示例：用戶註冊

```python
from results import Ok, Err, Result

def register_user(email: str, password: str) -> Result[dict, Exception]:
    """用驗證註冊用戶。"""
    
    def validate_email(e: str) -> Result[str, ValueError]:
        if "@" not in e:
            return Err(ValueError("Invalid email format"))
        return Ok(e)
    
    def validate_password(p: str) -> Result[str, RuntimeError]:
        if len(p) < 8:
            return Err(RuntimeError("Password must be 8+ characters"))
        return Ok(p)
    
    def check_unique(e: str) -> Result[str, RuntimeError]:
        # 模擬資料庫檢查
        if e == "admin@example.com":
            return Err(RuntimeError("Email already registered"))
        return Ok(e)
    
    # 組合驗證
    return (
        validate_email(email)
        .and_then(check_unique)
        .and_then(lambda e: validate_password(password).map(lambda _: e))
        .map(lambda e: {"email": e, "password": password})
    )

# 使用
result = register_user("user@example.com", "password123")
if result.is_ok():
    user = result.ok()
    print(f"Registered: {user}")
else:
    error = result.err()
    print(f"Registration failed: {error}")
```

## ✅ 推薦的寫法

### 函數式鏈接（推薦大多數情況）

使用 `map()`、`map_err()` 和 `and_then()` 實現簡潔、可組合的代碼：

```python
# ✅ 推薦：函數式風格
def process_user_age(age: int) -> Result[str, str]:
    """處理用戶年齡與驗證。"""
    return (
        Ok(age)
        .and_then(lambda a: Ok(a) if a >= 18 else Err("Underage"))
        .map(lambda a: f"Adult age: {a}")
        .map_err(lambda e: f"Age validation failed: {e}")
    )

result = process_user_age(21)
assert result.ok() == "Adult age: 21"
```

**優點：**
- ✅ 清晰的錯誤傳播（首次失敗時短路）
- ✅ 無中間變數污染
- ✅ 可組合和可重用
- ✅ 類型安全，支援 mypy --strict

### 命令式檢查（複雜邏輯）

當需要分支邏輯時，使用 `is_ok()`、`is_err()`、`ok()`、`err()`：

```python
# ✅ 可接受：命令式風格用於複雜流程
result = divide(10, 2)

if result.is_err():
    # 優先處理錯誤（快速失敗）
    logger.error(f"Division failed: {result.err()}")
    raise RuntimeError(f"Critical: {result.err()}")

# 使用成功值
value = result.ok()
print(f"Result: {value * 2}")
```

**何時使用：**
- 複雜的錯誤處理及不同的恢復策略
- 特定錯誤型別的日誌和監控
- 基於多個條件的提前終止

### 組合方法

混合函數式和命令式風格提高可讀性：

```python
# ✅ 混合：適當組合風格
result = (
    validate_input(user_input)
    .and_then(transform_data)
)

# 檢查結果
if result.is_err():
    error = result.err()
    if isinstance(error, ValidationError):
        return Err(f"Invalid input: {error}")
    else:
        raise UnexpectedError(error)

# 使用成功值
data = result.ok()
return Ok({"processed": data})
```

## 🎯 模式匹配與 match/case（Python 3.10+）

Python 3.10 引入結構性模式匹配（`match`/`case`），非常適合 Result 型別：

### 基本模式匹配

```python
from results import Ok, Err, Result

def fetch_user(user_id: int) -> Result[dict, str]:
    """根據 ID 獲取用戶。"""
    if user_id > 0:
        return Ok({"id": user_id, "name": "Alice"})
    return Err(f"Invalid ID: {user_id}")

# ✅ 推薦：模式匹配用於 Result 分發
result = fetch_user(123)
match result:
    case Ok(user):
        print(f"Found user: {user['name']}")
    case Err(error):
        print(f"Error: {error}")
```

### 比較：if/else vs match/case

```python
# ❌ 舊：命令式 if/else（仍可用）
result = fetch_user(123)
if result.is_ok():
    user = result.ok()
    print(f"Found: {user['name']}")
else:
    error = result.err()
    print(f"Error: {error}")

# ✅ 現代：結構性模式匹配（更簡潔）
result = fetch_user(123)
match result:
    case Ok(user):
        print(f"Found: {user['name']}")
    case Err(error):
        print(f"Error: {error}")
```

### 複雜模式及型別守衛

```python
from results import Ok, Err
from dataclasses import dataclass

@dataclass
class UserError:
    """業務錯誤型別。"""
    code: str
    message: str

def validate_and_fetch(user_id: int) -> Result[dict, UserError | ValueError]:
    """返回不同的錯誤型別。"""
    if user_id <= 0:
        return Err(ValueError("ID must be positive"))
    if user_id == 666:
        return Err(UserError("FORBIDDEN", "User 666 is restricted"))
    return Ok({"id": user_id, "name": "Alice"})

# ✅ 按錯誤型別模式匹配
result = validate_and_fetch(666)
match result:
    case Ok(user):
        print(f"Success: {user}")
    case Err(UserError(code, message)):  # 型別特定模式
        print(f"Business error [{code}]: {message}")
    case Err(ValueError(msg)):  # 異常型別模式
        print(f"Validation error: {msg}")
    case _:  # 預設
        print("Unexpected error")
```

### 真實世界 API 回應處理器

```python
from results import Ok, Err, Result
from dataclasses import dataclass

@dataclass
class APIResponse:
    status: int
    data: dict | None = None
    error: str | None = None

def handle_api_response(response: APIResponse) -> Result[dict, str]:
    """將 API 回應轉換為 Result。"""
    match response:
        case APIResponse(status=200, data=data) if data is not None:
            return Ok(data)
        case APIResponse(status=404, _):
            return Err("Resource not found")
        case APIResponse(status=500, error=error):
            return Err(f"Server error: {error}")
        case APIResponse(status=code, _):
            return Err(f"Unexpected status: {code}")

# 使用模式匹配
result = handle_api_response(APIResponse(200, {"user": "Alice"}))
match result:
    case Ok(data):
        print(f"Data: {data}")
    case Err(message):
        print(f"Failed: {message}")
```

### 使用模式匹配鏈接 Results

```python
def process_and_fetch(user_id: int) -> Result[str, str]:
    """使用模式匹配鏈接多個操作。"""
    result = validate_and_fetch(user_id)
    
    match result:
        case Ok(user):
            # 繼續成功
            enriched = enrich_user_data(user)
            return Ok(f"Processed: {enriched}")
        case Err(error):
            # 短路錯誤
            return Err(f"Processing failed: {error}")

# 或使用 map/and_then 實現相同效果（兩者都有效）
result = (
    validate_and_fetch(user_id)
    .and_then(enrich_user_data)
    .map(lambda u: f"Processed: {u}")
)
```

**模式匹配指南：**
- ✅ 在 API 邊界使用 `match/case` 進行明確的 Result 分發
- ✅ 使用 `map/and_then` 進行轉換鏈接
- ✅ 組合兩者：使用 `match` 進行最終結果處理，`map` 進行中間轉換
- ✅ 模式匹配擅長型別路由（不同的錯誤型別）

## 🔍 除錯工具：檢查和 Context 鏈

### 使用 `inspect()` 和 `inspect_err()` 除錯

v0.2.0 引入除錯工具，用於非侵入式檢查中間值：

```python
from results import Ok, Err

# inspect() 以成功值調用函數，返回不變
result = (
    Ok(5)
    .inspect(lambda x: print(f"Value: {x}"))  # 輸出 "Value: 5"
    .map(lambda x: x * 2)
    .inspect(lambda x: print(f"Doubled: {x}"))  # 輸出 "Doubled: 10"
)
assert result.ok() == 10

# inspect_err() 以錯誤值調用函數，返回不變
error_result = (
    Err(ValueError("invalid input"))
    .inspect_err(lambda e: print(f"Error: {e}"))  # 輸出 "Error: invalid input"
    .map_err(lambda e: RuntimeError(f"Wrapped: {e}"))
)
```

### 使用 Context 鏈追蹤上下文（LIFO）

v0.2.0 添加 Rust anyhow 風格的 context 鏈，用於豐富的錯誤診斷：

```python
from results import Err, Ok

# 構建 context 鏈（後進先出）
result = (
    Err(ValueError("database connection failed"))
    .context("connecting to User service")
    .context("fetching user data")
    .context("POST /api/users")
)

# 解包顯示完整的 context 鏈（LIFO 順序）
try:
    result.unwrap()
except ValueError as e:
    # 錯誤訊息顯示完整 context：
    # POST /api/users
    # fetching user data
    # connecting to User service
    # database connection failed
    print(str(e))
```

**使用 `with_context()` 進行動態 context：**

```python
from datetime import datetime

result = (
    Err("operation failed")
    .with_context(lambda: f"at {datetime.now()}")  # 延遲評估
)
# 用於昂貴的除錯資訊，只在需要時評估
```

**真實世界例子（鏈接）：**

```python
def validate_user_registration(email: str, age: int) -> Result[dict, str]:
    # 驗證電子郵件
    if "@" not in email:
        return Err("invalid email").context("email validation")
    
    # 驗證年齡
    if age < 18:
        return Err("underage").context("age check").context("user registration")
    
    return Ok({"email": email, "age": age})

# 發生錯誤時，完整的 context 通過鏈保留
result = validate_user_registration("invalid", 15)
# 錯誤訊息顯示：
# user registration
# age check
# underage
```

## 📋 錯誤處理：Traceback 和 Context

**設計理念：** 如同 Rust 的 Result 型別，`results` 刻意不自動捕獲 traceback。這提供兩條清晰的路徑：

### 路徑 1：簡單（無 Traceback）
```python
def validate_age(age: int) -> Result[int, str]:
    if age >= 18:
        return Ok(age)
    else:
        return Err("User is underage")  # 簡單但無 traceback 資訊
```

### 路徑 2：保留 Traceback
```python
def validate_age_with_context(age: int) -> Result[int, Exception]:
    try:
        if age >= 18:
            return Ok(age)
        else:
            raise ValueError("User is underage")
    except (ValueError, TypeError) as e:
        return Err(e)  # 保留異常和 traceback
```

> **注意：** v0.2.0+ 引入 `with_context()`，v0.3.0+ 將其擴展到非同步工作流，具有跨 await 邊界的 context 保留。

## 📚 API 參考

### Result 型別

```python
class Result[T, E](ABC, Generic[T, E]):
    """代表成功值 (T) 或錯誤 (E)。"""
    
    def is_ok(self) -> bool:
        """檢查 Result 是否是 Ok。"""
    
    def is_err(self) -> bool:
        """檢查 Result 是否是 Err。"""
    
    def ok(self) -> T | None:
        """獲取成功值，Err 時返回 None。"""
    
    def err(self) -> E | None:
        """獲取錯誤值，Ok 時返回 None。"""
    
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """轉換成功值，保留錯誤型別。"""
    
    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        """轉換錯誤，保留成功值。"""
    
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, F | E]:
        """鏈接操作，自動累積錯誤型別。"""
    
    def inspect(self, f: Callable[[T], None]) -> Result[T, E]:
        """非侵入式檢查成功值（v0.2.0+）。"""
    
    def inspect_err(self, f: Callable[[E], None]) -> Result[T, E]:
        """非侵入式檢查錯誤值（v0.2.0+）。"""
    
    def context(self, msg: str) -> Result[T, E]:
        """推送 context 訊息到錯誤鏈（v0.2.0+）。"""
    
    def with_context(self, f: Callable[[], str]) -> Result[T, E]:
        """推送延遲評估的 context 訊息（v0.2.0+）。"""
    
    def unwrap(self) -> T:
        """提取值或拋出 UnwrapError。"""
```

### Ok[T]

```python
class Ok(Result[T, E]):
    """包含值 T 的成功變體。"""
    
    def __init__(self, value: T) -> None:
        self._value = value
```

### Err[E]

```python
class Err(Result[T, E]):
    """包含錯誤 E 的失敗變體。"""
    
    def __init__(self, error: E) -> None:
        self._error = error
```

### 異常

```python
class UnwrapError(ResultError):
    """在 Err 上調用 unwrap() 時拋出。"""
    
    def __init__(self, message: str, original_error: Any) -> None:
        self.message = message
        self.original_error = original_error
```

## 🔄 非同步/等待支援（v0.3.0+）

AsyncResult 使用與同步 Result 相同的人體工程學實現非阻塞錯誤處理：

```python
from results import AsyncResult, Ok, Err

async def fetch_user(user_id: int) -> AsyncResult[User, FetchError]:
    """非同步獲取用戶與錯誤處理。"""
    async def fetch() -> Result[User, FetchError]:
        try:
            user = await db.fetch_user(user_id)
            return Ok(user)
        except DBError as e:
            return Err(FetchError(str(e))).context("fetching user")
    
    return AsyncResult.from_awaitable(fetch())

# 使用：與同步 Result 相同的鏈接 API
result = (
    fetch_user(123)
    .context("user service")
    .and_then_async(lambda user: validate_user_async(user))
    .map_async(lambda user: enrich_user_async(user))
)

user = await result.unwrap_async()  # 解包及完整的 LIFO context 鏈
```

**主要特性：**
- ✅ `map_async()`、`map_err_async()`、`and_then_async()` 用於非同步鏈接
- ✅ `unwrap_async()` 及 UnwrapError 中的 context 鏈（與同步相同）
- ✅ `inspect_async()`、`inspect_err_async()` 用於副作用
- ✅ 跨非同步邊界的 LIFO context 保留
- ✅ 使用 `asyncio.to_thread()` 的無縫非同步/同步互操作性
- ✅ 完整的型別安全，支援 mypy --strict 合規性

## 🧪 測試

運行所有測試：

```bash
pytest tests/
```

運行特定測試類別：

```bash
# 同步測試
pytest tests/sync/ -v

# 非同步測試
pytest tests/async_/ -v

# 整合測試
pytest tests/integration/ -v

# 型別檢查
mypy src/results/ --strict

# 代碼風格
ruff check src/results/ tests/
```

## 🏗️ 架構

包遵循**契約設計模式**：

```
src/results/
├── core/
│   ├── base.py          # Result ABC（契約）
│   ├── types.py         # TypeVar 定義
│   └── exceptions.py    # ResultError、UnwrapError
└── impl/
    └── sync/
        ├── ok.py        # Ok[T] 實現
        └── err.py       # Err[E] 實現
```

**設計原則：**
- 🎯 **SRP（單一責任原則）** — 每個類有一個改變的理由
- 🔗 **CSRP（複雜單一責任原則）** — ABC 方法是內聚的
- 📦 **低耦合** — 實現之間互不依賴
- 🔓 **公共 API** — 在 `__init__.py` 中的三層暴露

## 🤝 貢獻

我們遵循嚴格的代碼質量標準：
- ✅ 100% 測試覆蓋率（或有文件說明的例外）
- ✅ mypy --strict，零錯誤
- ✅ ruff 所有檢查通過
- ✅ 所有 ABC 實現上的 @typing_extensions.override

## 📄 許可證

MIT 許可證 — 詳見 LICENSE 檔案。

## 🔗 相關資源

- **Rust Result** — 此庫的靈感來源：https://doc.rust-lang.org/std/result/enum.Result.html
- **PEP 604** — 型別 union 語法（Python 3.10+）
- **PEP 673** — TypeVar 綁定參數用於泛型約束

## 📞 支援

- **文件** — 詳見 [docs/](docs/) 的詳細指南
- **問題** — 報告 bug：https://github.com/a129924/results/issues
- **討論** — https://github.com/a129924/results/discussions

---

**用 ❤️ 為熱愛型別安全的 Python 開發者打造。**
