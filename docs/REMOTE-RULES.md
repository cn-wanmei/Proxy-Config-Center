# 远程规则发布规范

## 正式地址

正式客户端与远程规则统一使用 GitHub Releases 的 `latest/download/<asset>` 地址，不绑定固定版本号。

基础地址：

`https://github.com/cn-wanmei/Proxy-Config-Center/releases/latest/download/`

规则资产命名：

- `rule-<service>.yaml`
- `rule-priority.yaml`
- `rule-sources.yaml`

每个正式 Release 必须同步上传完整规则资产，并由 `release-manifest.json` 记录资产名、latest URL、SHA256 和文件大小。

## 发布约束

1. `latest` 只由正式 `v*` Tag Release 更新。
2. PR、普通分支和失败构建不得成为远程规则来源。
3. Release Workflow 必须在创建 Release 后逐一 HTTP GET 验证所有客户端与规则 latest URL 为 HTTP 200。
4. 任一远程资产缺失、为空或不可访问，Release Job 必须失败。
5. 历史 `vX.Y.Z` Release 作为版本归档保留；客户端远程更新只跟随 latest。

## 客户端

七端发布资产均提供 latest URL：Clash、Clash Meta、Stash、Egern、Loon、Shadowrocket、sing-box。
