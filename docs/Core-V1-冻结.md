# Core V1 冻结说明 / Core V1 Freeze

## 中文

**冻结日期：** 2026-08-08  
**正式版本：** v1.0.0

Core V1 是稳定版本的语义契约。允许向后兼容的增量扩展；破坏性变更必须进入 Core V2。

### 已冻结内容

1. **DNS 三层模型**
   - `core/dns/resolvers.yaml`
   - `core/dns/groups.yaml`
   - `core/dns/policies.yaml`
2. **策略组语义**
   - `core/proxy-groups/base.yaml`
   - `core/proxy-groups/service.yaml`
3. **规则优先级**
   - `core/rules/priority.yaml` 是唯一优先级来源
4. **ID / Reference 契约**
   - kebab-case
   - DNS policy 使用 `dns-` 前缀
   - `ref` / `action` 引用
5. **IR 契约**
   - `ResolvedIR` / `ResolvedService` 的稳定字段语义
6. **平台解耦**
   - Core 不写平台名称分支
   - 平台差异通过 capability + adapter 表达

### 允许变更

- 新增 service / rule / resolver
- 完善 Renderer
- 增加新的 adapter + capability
- 增加验证、测试和发布能力

### 必须升 V2 的变更

- 删除或重命名已有核心 ID
- 改变已有 priority 的业务含义
- 破坏 Resolved IR 稳定字段
- 让 Core 重新依赖具体平台语法

---

## English

Core V1 is the stable semantic contract shipped as v1.0.0. Backward-compatible additions are allowed; breaking semantic or IR changes require Core V2.
