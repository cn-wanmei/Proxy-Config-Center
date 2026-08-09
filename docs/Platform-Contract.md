# Platform Contract

平台能力由三层组成：

1. `common/platforms.yaml`：平台注册表，定义正式支持的平台集合。
2. `platforms/<id>/capabilities.yaml`：平台能力与限制，必须通过 Schema。
3. `platforms/<id>/adapter/render.py`：只负责把 Resolved IR 映射为客户端原生配置。

## 设计约束

- 新客户端原则上只增加 registry + capability + adapter + tests。
- Core 不允许出现 `if platform == ...` 的平台语法分支。
- `rule_set`、`rule_provider`、`domain_fallback` 是独立能力，不能互相隐式替代。
- Fallback 必须由调用方显式启用，并且不能吞掉异常。
- 不支持的字段不得伪造输出。

## sing-box

sing-box 使用原生 JSON 配置。其 route rule / rule-set / selector / urltest 均在 Adapter 层实现。

当前 Core 的 Blackmatrix7 Clash YAML/LIST 资源不是 sing-box 原生 rule-set，因此 sing-box 不会错误地把它们声明为 `format: source`；无法安全复用的远程源使用 Core 已解析的域名规则作为明确 fallback。

sing-box 原生远程 rule-set 的 `update_interval` 使用 `168h`（7 天）。详见官方文档：

- Route：<https://sing-box.sagernet.org/configuration/route/>
- Rule Set：<https://sing-box.sagernet.org/configuration/rule-set/>
- Selector：<https://sing-box.sagernet.org/configuration/outbound/selector/>
