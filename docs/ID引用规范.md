# ID 引用规范 / ID Reference Specification

## 中文

本仓库所有 Core 语义必须使用统一的 ID 引用系统，禁止随意命名。

### 1. 命名规则
- 全部使用 **kebab-case**（小写 + 连字符）
- 禁止空格、下划线、驼峰
- ID 必须全局唯一

### 2. 前缀约定

| 类型           | 前缀示例              | 说明                     |
|----------------|-----------------------|--------------------------|
| 策略组         | `proxy-mode`, `ai`    | 无特殊前缀，语义清晰即可 |
| DNS 策略组     | `dns-apple`           | 必须以 `dns-` 开头       |
| DNS 上游       | `dns-system` 等       | 必须以 `dns-` 开头       |
| 动作（action） | `direct`, `reject`    | 固定关键字               |
| 规则服务       | `service-ai`          | 建议 `service-` 前缀     |

### 3. 引用方式

在 options 中：
- 引用其他组：`ref: <id>`
- 使用动作：`action: direct` / `action: reject` / `action: system-dns` 等
- 禁止直接写平台语法

### 4. 已锁定的核心 ID 列表

**基础策略组**
- `proxy-mode`
- `manual-select`
- `free-flow`
- `auto-select`
- `direct`
- `reject`

**分流策略组**
- `ad-block`
- `china`
- `code-repo`
- `microsoft`
- `game`
- `ai`
- `google`
- `youtube`
- `spotify`
- `telegram`
- `twitter`
- `netflix`
- `tiktok`
- `ehentai`
- `apple`
- `final`

**DNS 策略组**
- `dns-default`
- `dns-apple`
- `dns-china`
- `dns-google`
- `dns-ai`
- `dns-telegram`
- `dns-streaming`
- `dns-microsoft`
- `dns-github`
- `dns-system` / `dns-alidns` / `dns-tencent` / `dns-google-up` / `dns-cloudflare`

---

## English

All Core semantics in this repository must use a unified ID reference system.

### 1. Naming Rules
- Always use **kebab-case** (lowercase + hyphens)
- No spaces, underscores, or camelCase
- IDs must be globally unique

### 2. Prefix Conventions

| Type              | Example Prefix     | Notes                          |
|-------------------|--------------------|--------------------------------|
| Strategy Group    | `proxy-mode`, `ai` | No special prefix required     |
| DNS Strategy Group| `dns-apple`        | Must start with `dns-`         |
| DNS Upstream      | `dns-system`       | Must start with `dns-`         |
| Action            | `direct`, `reject` | Fixed keywords                 |
| Rule Service      | `service-ai`       | Recommended `service-` prefix  |

### 3. Reference Style

In options:
- Reference another group: `ref: <id>`
- Use action: `action: direct` / `action: reject` / etc.
- Never write platform-specific syntax in Core
