# v1.0.0 Release Notes

## 中文

- 补全规则：游戏平台、抖音国际、绅士漫画等
- 图标：接入 ClashTools 高清图标 CDN（22 个策略组图标）
- 全平台配置已生成：Clash Meta / Clash / Stash / Egern / Loon / Shadowrocket
- DNS nameserver-policy：苹果→系统、中国→阿里、谷歌→Google DNS 等
- 节点仍由 Sub-Store 管理

## English

- Complete rules for game / tiktok / ehentai and more
- Icons from ClashTools CDN
- All 6 platform configs generated
- DNS policy mapping included
- Nodes via Sub-Store only

## Download

Run CI or:
```bash
python scripts/build.py
```

Configs under `build/`.

## Tag

```bash
git tag v1.0.0
git push origin v1.0.0
```
