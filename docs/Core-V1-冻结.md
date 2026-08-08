# Core V1 冻结说明 / Core V1 Freeze

## 中文

**冻结日期：** 2026-08-08

### 已冻结内容（不得随意破坏兼容性）

1. **DNS 三层模型**
   - `core/dns/resolvers.yaml` — Layer 1
   - `core/dns/groups.yaml` — Layer 2
   - `core/dns/policies.yaml` — Layer 3

2. **策略组语义**
   - `core/proxy-groups/base.yaml`
   - `core/proxy-groups/service.yaml`（`proxy` + `dns` 双绑定）

3. **规则优先级**
   - `core/rules/priority.yaml` 为唯一优先级来源

4. **ID 规范**
   - kebab-case
   - DNS policy 必须以 `dns-` 开头
   - `ref` / `action` 引用方式

5. **IR 契约**
   - `scripts/ir.py` 产出的 `ResolvedIR` / `ResolvedService` 字段

### 允许变更
- 新增 service / rule / resolver（向后兼容）
- 完善 Renderer 细节
- 增加平台适配

### 禁止变更（需升 V2）
- 删除或重命名已有 service id / dns policy id
- 改变 priority 数字含义
- 破坏 ResolvedService 字段结构

---

## English

**Freeze date:** 2026-08-08

Core V1 locks the DNS three-layer model, strategy group semantics, priority as single source of truth, ID conventions, and Resolved IR contract.

Additive changes are allowed. Breaking changes require Core V2.
