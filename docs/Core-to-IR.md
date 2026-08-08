# Core → IR (Intermediate Representation)

## 中文

Build Engine 将 Core 语义编译为平台无关的中间表示（IR），再由各平台 Renderer 翻译成最终配置。

### IR 结构概览

```
IR =
  config:        # 来自 core/config/
  dns:           # 来自 core/dns/
    resolvers
    groups
    policies
  proxy_groups:  # 来自 core/proxy-groups/
    base
    service      # 含 proxy + dns 绑定
  rules:         # 按 priority.yaml 排序后的规则列表
  advertising:   # 广告相关
```

### 编译流程

1. 加载全部 Core YAML
2. 校验（validate.py）
3. 按 priority.yaml 对 rules 排序
4. 解析 service 的 proxy / dns 绑定
5. 生成 IR 对象
6. 交给对应平台 Renderer

### IR 不包含
- 任何平台语法（type: select、proxies: 等）
- 节点信息

---

## English

The Build Engine compiles Core semantics into a platform-agnostic Intermediate Representation (IR), which is then translated by each platform Renderer into the final config.

### Compilation Pipeline

1. Load all Core YAML files
2. Validate (validate.py)
3. Sort rules by priority.yaml
4. Resolve service proxy/dns bindings
5. Produce IR object
6. Hand off to platform Renderer
