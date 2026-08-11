# Proxy-Config-Center

**分流规则编译与审计中心**  
**Version: 3.2.0**

## 定位

Core 只负责分流规则：输入、规范化、语义分析、冲突检测、审计、确定性编译与可追溯发布。

Core **不负责** DNS、节点、代理组、TUN、Fake-IP、完整客户端配置或客户端网络策略。

```text
规则输入
  ↓
规范化
  ↓
语义分析
  ↓
冲突 / 覆盖 / 重复检测
  ↓
Fail-Closed 审计 Gate
  ↓
确定性规则编译
  ↓
规则文件 + Manifest
  ↓
客户端自行引用
```

## 3.2 核心原则

- Canonical Rule Identity：Global Rule ID + Policy Scoped Rule ID + 完整 SHA-256
- Semantic Engine：duplicate / conflict / shadow / overlap
- Fail-Closed：审计失败禁止编译
- Deterministic Build：相同输入必须产生相同规则输出
- Provenance：每条规则记录来源与身份
- Client Agnostic：客户端只消费规则，不进入 Core 编译链

## 使用

```bash
make audit_gate
make rule_compile
make ci
```

编译结果位于 `dist/rules/`，每个策略独立发布，`dist/manifest.json` 提供版本与规则索引。
