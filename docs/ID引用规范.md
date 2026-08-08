# ID 引用规范 / ID Reference Specification

## 中文

本仓库所有 Core 语义使用统一 ID 引用系统。引用关系由 Reference Validator 在构建前检查。

### 1. 命名规则

- 全部使用 **kebab-case**（小写 + 连字符）
- 禁止空格、下划线、驼峰
- ID 必须在其语义域内唯一
- 不允许通过平台专有名称替代 Core ID

### 2. 前缀约定

| 类型 | 示例 | 说明 |
|---|---|---|
| 策略组 | `proxy-mode`, `ai` | 语义清晰即可 |
| DNS 策略组 | `dns-apple` | 使用 `dns-` 前缀 |
| DNS 上游 | `dns-system` | 使用 `dns-` 前缀 |
| 动作 | `direct`, `reject` | 固定动作语义 |
| 规则服务 | `service-ai` | 推荐 `service-` 前缀 |

### 3. 引用方式

- 引用其他对象：`ref: <id>`
- 使用动作：`action: direct` / `action: reject`
- Core 禁止直接写平台语法
- 所有跨文件引用必须能够被 Reference Validator 解析

### 4. 稳定 ID 原则

v1.0.0 已发布的核心 ID 默认视为稳定接口。删除、重命名或改变既有语义属于 breaking change，应进入 Core V2。

---

## English

Core semantics use a unified ID reference system. Cross-file references are validated before build.

IDs use kebab-case, remain stable after release, and must not encode platform-specific syntax. Breaking changes to released Core IDs require Core V2.
