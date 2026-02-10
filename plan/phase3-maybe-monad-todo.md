# Phase 3: Maybe Monad Implementation - TODO Plan

**Status:** 🔄 PLANNING  
**Target Branch:** feature/phase3-maybe-monad  
**Prerequisites:** ✅ Phase 2 完成 (ContextChain, Protocols 已建立)

---

## 目標

實現 Maybe[T] Monad，提供 Optional 值的函數式處理，避免 None 檢查。Maybe 有兩個變體：
- **Just[T]** - 包含有效值
- **Nothing** - 表示無值（類似 None）

---

## Protocol 實現檢查清單

基於 Phase 2 建立的 6 個 Protocol，Maybe 必須實現以下接口：

### 1. ✅ **ContextAware Protocol**
```python
# Nothing 需要實現（Just 不需要，因為沒有錯誤）
def context(self, msg: str) -> Maybe[T]
def with_context(self, f: Callable[[], str]) -> Maybe[T]
```

**實施細節：**
- Nothing 使用 `ContextChain` 記錄為什麼值不存在
- Just 的 context() 返回 self（no-op）
- 使用 Phase 2 的 `ContextChain.push()` 和 `push_lazy()`

**測試重點：**
- [ ] Nothing.context() 正確堆疊訊息
- [ ] Nothing.with_context() 支持 lazy evaluation
- [ ] Just.context() 不影響值

---

### 2. ✅ **Unwrappable Protocol**
```python
def unwrap(self) -> T
async def unwrap_async(self) -> T
```

**實施細節：**
- Just.unwrap() → 返回包裝的值
- Nothing.unwrap() → 使用 `unwrap_with_context()` 拋出 UnwrapError
- 上下文鏈會顯示在錯誤訊息中

**測試重點：**
- [ ] Just.unwrap() 返回正確值
- [ ] Nothing.unwrap() 拋出 UnwrapError 並包含上下文
- [ ] 錯誤訊息格式正確（LIFO 順序）

---

### 3. ✅ **Inspectable Protocol**
```python
def inspect(self, f: Callable[[T], None]) -> Maybe[T]
def inspect_err(self, f: Callable[[Any], None]) -> Maybe[T]
```

**實施細節：**
- Just.inspect(f) → 調用 f(value)，返回 self
- Just.inspect_err(f) → no-op，返回 self
- Nothing.inspect(f) → no-op，返回 self
- Nothing.inspect_err(f) → 調用 f(None)，返回 self

**測試重點：**
- [ ] Just.inspect() 執行副作用
- [ ] Nothing.inspect() 不執行副作用
- [ ] inspect 返回原始 Maybe（不修改）

---

### 4. ✅ **Mappable Protocol**
```python
def map(self, op: Callable[[T], U]) -> Maybe[U]
def map_err(self, op: Callable[[Any], Any]) -> Maybe[T]
```

**實施細節：**
- Just.map(f) → Just(f(value))
- Just.map_err(f) → self（no-op）
- Nothing.map(f) → Nothing（short-circuit）
- Nothing.map_err(f) → 可用於轉換「無值原因」

**測試重點：**
- [ ] Just.map() 正確轉換值
- [ ] Nothing.map() 保持 Nothing
- [ ] 類型轉換正確（Maybe[int] → Maybe[str]）

---

### 5. ✅ **Chainable Protocol**
```python
def and_then(self, op: Callable[[T], Maybe[U]]) -> Maybe[U]
```

**實施細節：**
- Just.and_then(f) → f(value)
- Nothing.and_then(f) → self（short-circuit，保留上下文）

**測試重點：**
- [ ] Just.and_then() 正確鏈接
- [ ] Nothing.and_then() 不執行函數
- [ ] 上下文鏈在鏈中保留

---

### 6. ✅ **AsyncMappable Protocol**
```python
def map_async(self, op: Callable[[T], Awaitable[U]]) -> Awaitable[Maybe[U]]
def map_err_async(self, op: Callable[[Any], Awaitable[Any]]) -> Awaitable[Maybe[T]]
```

**實施細節：**
- 類似 Result.AsyncResult 的模式
- Just.map_async() → 執行異步轉換
- Nothing.map_async() → 返回 Nothing（無需執行）

**測試重點：**
- [ ] 異步轉換正確執行
- [ ] 錯誤處理正確

---

## 實施步驟

### Step 1: 創建 Maybe ABC 契約
- [ ] 創建 `src/results/core/maybe_base.py`
- [ ] 定義 `MaybeBase[T]` ABC（繼承自 Generic[T]）
- [ ] 聲明所有抽象方法（參考 Result ABC）
- [ ] 添加 `is_just()` 和 `is_nothing()` 抽象方法

**預期代碼量：** ~150 行

---

### Step 2: 實現 Just[T]
- [ ] 創建 `src/results/maybe/sync/just.py`
- [ ] `@dataclass(frozen=True)` - 不可變
- [ ] 實現所有 Protocol 方法（~20 個方法）
- [ ] 所有方法使用 `@override` 裝飾器
- [ ] 完整的 docstring（含範例）

**預期代碼量：** ~280 行

**關鍵實現：**
```python
@dataclass(frozen=True)
class Just(MaybeBase[T], Generic[T]):
    _value: T
    
    @override
    def unwrap(self) -> T:
        return self._value
    
    @override
    def map(self, op: Callable[[T], U]) -> Maybe[U]:
        return Just(op(self._value))
    
    @override
    def and_then(self, op: Callable[[T], Maybe[U]]) -> Maybe[U]:
        return op(self._value)
```

---

### Step 3: 實現 Nothing
- [ ] 創建 `src/results/maybe/sync/nothing.py`
- [ ] `@dataclass(frozen=True)` - 不可變
- [ ] `_context_chain: ContextChain = ContextChain()` 字段
- [ ] 實現所有 Protocol 方法（~20 個方法）
- [ ] 使用 Phase 2 的 `unwrap_with_context()`

**預期代碼量：** ~220 行

**關鍵實現：**
```python
@dataclass(frozen=True)
class Nothing(MaybeBase[T], Generic[T]):
    _context_chain: ContextChain = ContextChain()
    
    @override
    def unwrap(self) -> Never:
        unwrap_with_context(None, self._context_chain)
    
    @override
    def map(self, op: Callable[[T], U]) -> Maybe[U]:
        return self  # type: ignore
    
    @override
    def context(self, msg: str) -> Maybe[T]:
        return Nothing(self._context_chain.push(msg))
```

---

### Step 4: 創建測試架構
- [ ] 創建 `tests/maybe/sync/test_just_impl.py`
- [ ] 創建 `tests/maybe/sync/test_nothing_impl.py`
- [ ] 創建 `tests/maybe/integration/test_maybe_integration.py`

**測試結構（鏡像 Result）：**
```
tests/maybe/
├── sync/
│   ├── test_just_impl.py       # ~100 個測試
│   ├── test_nothing_impl.py    # ~100 個測試
│   └── test_context_chain.py   # 上下文測試
└── integration/
    ├── test_maybe_integration.py
    └── test_maybe_result_interop.py
```

**預期測試數：** ~250 個測試

---

### Step 5: 模塊導出與集成
- [ ] 更新 `src/results/maybe/__init__.py`
- [ ] 導出 Just, Nothing, Maybe (type alias)
- [ ] 更新 `src/results/__init__.py` 頂層導出
- [ ] 創建 `Maybe = Just | Nothing` 類型別名

```python
# src/results/maybe/__init__.py
from results.maybe.sync.just import Just
from results.maybe.sync.nothing import Nothing

Maybe = Just | Nothing

__all__ = ["Just", "Nothing", "Maybe"]
```

---

### Step 6: 文檔與範例
- [ ] 更新 README.md 添加 Maybe 範例
- [ ] 創建 `docs/maybe-guide.md`（使用指南）
- [ ] 添加常見用例範例

---

### Step 7: 驗證與提交
- [ ] `mypy src/results/ --strict` (0 errors)
- [ ] `ruff check src/results/ tests/` (all pass)
- [ ] `pytest tests/ -v` (所有測試通過)
- [ ] 覆蓋率 ≥80%（整體）、≥90%（maybe/）

---

## Maybe 與 Result 的差異

| 特性 | Result[T, E] | Maybe[T] |
|------|--------------|----------|
| **成功變體** | Ok[T] | Just[T] |
| **失敗變體** | Err[E] (攜帶錯誤值) | Nothing (無值) |
| **上下文鏈** | Err 專用 | Nothing 專用 |
| **錯誤類型** | 泛型 E | 固定為 None 概念 |
| **典型用途** | 可能失敗的操作 | 可能無值的查詢 |

---

## 使用範例（目標 API）

```python
from results import Just, Nothing, Maybe

# 創建 Maybe
user_age: Maybe[int] = Just(25)
missing_age: Maybe[int] = Nothing()

# 鏈式操作
result = (
    Just(5)
    .map(lambda x: x * 2)
    .and_then(lambda x: Just(x + 1) if x < 20 else Nothing())
    .context("validating range")
)

# 與 Result 互操作
def find_user(id: int) -> Maybe[User]:
    if user := db.get(id):
        return Just(user)
    return Nothing().context(f"user {id} not found")

def validate_age(age: int) -> Result[int, str]:
    if age < 0:
        return Err("negative age")
    return Ok(age)

# 組合使用
maybe_user = find_user(123)
result = maybe_user.and_then(lambda u: validate_age(u.age))
```

---

## 成功標準

✅ **代碼質量：**
- mypy --strict: 0 errors
- ruff check: all pass
- 所有公開方法有完整 docstring

✅ **測試覆蓋：**
- 總測試數：≥250 個
- 覆蓋率：maybe/ ≥90%
- 所有 Protocol 方法都有測試

✅ **文檔完整：**
- README.md 包含 Maybe 範例
- 每個方法都有使用範例
- 常見模式有文檔

✅ **架構一致：**
- 與 Result 架構對齊
- 復用 ContextChain 和 Protocols
- 命名與行為一致

---

## 預期工作量

| 任務 | 預估代碼量 | 預估時間 |
|------|-----------|----------|
| Maybe ABC | ~150 行 | 1 小時 |
| Just 實現 | ~280 行 | 2 小時 |
| Nothing 實現 | ~220 行 | 2 小時 |
| 測試套件 | ~800 行 | 3 小時 |
| 文檔 | ~200 行 | 1 小時 |
| **總計** | **~1,650 行** | **~9 小時** |

---

## 下一步行動

1. **討論 Maybe 接口設計** - 確認方法簽名和行為
2. **創建 feature/phase3-maybe-monad 分支**
3. **實施 Step 1-7**
4. **審查與合併**

---

## 參考資料

- **Phase 2 Summary:** [phase2-shared-logic-summary.md](./phase2-shared-logic-summary.md)
- **Result 實現:** `src/results/result/sync/`
- **Protocols 定義:** `src/results/common/protocols.py`
- **ContextChain:** `src/results/core/context.py`
