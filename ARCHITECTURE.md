# Generation Vault — Architecture Freeze v1.0
## 2026-07-13

---

## Core Pipeline

```
PNG
 │
 ▼
Parser          ← ComfyUIParser / A1111Parser / ...
 │
 ▼
Generation      ← 标准数据结构，所有层之间唯一传递对象
 │
 ▼
Storage         ← SQLite，只做 insert / get / query
 │
 ▼
Query           ← FTS5 + model/LoRA/seed，返回 List[Generation]
 │
 ▼
UI              ← Streamlit Presenter，不写业务逻辑
```

---

## 铁律

**任何功能必须经过这条流水线，不允许绕过。**

修改架构必须先更新本文档。

---

## 分层隔离

| 层 | 可访问 | 不可访问 |
|------|------|------|
| Parser | PNG file | DB, UI, Query |
| Generation | — (纯数据) | 任何层 |
| Storage | Generation 对象 | Parser, UI, Query |
| Query | Storage | Parser, UI |
| UI | Query + Storage | Parser (通过 Storage 间接) |

---

## 版本

| Tag | 内容 |
|------|------|
| v0.1.0 | Parser |
| v0.2.0 | Storage |
| v0.3.0 | Query |
| v0.4.0 | Streamlit UI |
| v1.0.0 | Architecture Freeze |
