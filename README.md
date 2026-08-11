# Proxy-Config-Center

**自用分流规则仓库 / Personal remote routing rules**  
**Version: 3.0.0**

> 主产物：**远程独立分流规则**（非完整客户端配置）。  
> 每策略一份规则文件；每客户端仅输出引用片段；支持 **Anywhere `.arrs`**。

## 产物结构

```text
dist/
├── rules/{policy}.list
├── rules/{policy}.yaml
├── rules/anywhere/{policy}.arrs
├── clients/{client}/...
├── icons/{policy}.png
└── manifest.json
```

**不发布**完整客户端配置。

```bash
make rule_compile
make ci
```

Anywhere: `dist/rules/anywhere/{id}.arrs`
