# Release v1.0.0

## 一键发版（推荐）

在仓库根目录执行：

```bash
bash scripts/release.sh 1.0.0
```

或手动：

```bash
pip install pyyaml
python scripts/validate.py
python scripts/build.py
echo 1.0.0 > VERSION
git add -A
git commit -m "release: v1.0.0"
git tag v1.0.0
git push origin main --tags
```

打上 `v1.0.0` tag 后，`.github/workflows/release.yml` 会自动：
1. 校验 + 测试 + 构建
2. 打包 `proxy-config-center-configs.zip`
3. 创建 GitHub Release

## 本版内容

- Core V1 冻结
- 六平台配置：Clash Meta / Clash / Stash / Egern / Loon / Shadowrocket
- 完整分流规则 + ClashTools 图标 + DNS 策略
- 节点仍由 Sub-Store 管理
