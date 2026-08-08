# Core → IR (Intermediate Representation)

## 中文

Build Engine 将 Core 语义编译为平台无关的 `ResolvedIR`，再由 capability-aware Renderer 翻译成六个平台的最终配置。

### 编译流程

1. 加载全部 Core YAML
2. Schema / semantic validation
3. Reference Graph 校验跨文件引用
4. 按 `core/rules/priority.yaml` 解析并约束规则优先级
5. 解析 service 的 proxy / dns 绑定
6. 生成 `ResolvedIR`
7. 根据平台 capability 选择可用规则表达
8. 交给平台 Renderer
9. 运行 Golden / Structural Check
10. 输出 CI Artifact / Release

### IR 包含

```text
config
DNS resolvers / groups / policies
proxy groups
services
rules
rule sources
priorities
platform capability resolution
```

### IR 不包含

- 平台专有语法
- 节点订阅生命周期
- 任意平台名称判断形式的 Core 业务逻辑

### 能力模型

远程规则能力必须分别处理：

- `rule_set`
- `rule_provider`
- `domain_fallback`

Renderer 根据 capability 选择平台可用表达，不允许 Core 为某个平台写分支。

---

## English

The Build Engine compiles Core semantics into platform-neutral `ResolvedIR`, then capability-aware renderers translate it into six platform configurations.

The IR contains resolved configuration semantics, DNS, proxy groups, services, rules, rule sources, priorities and platform capability resolution, but no platform-specific syntax or node lifecycle data.
