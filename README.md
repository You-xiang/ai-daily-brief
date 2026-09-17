# AI Daily Brief · AI 行业每日简报

每天早上 9:00（北京时间）由 GitHub Actions 自动运行：

1. 抓取机器之心、量子位、36氪、Hacker News 等 RSS 新闻源
2. 调用电信 AI Store 大模型（OpenAI 兼容接口）生成结构化简报
3. 发布到 GitHub Pages，并提交到本仓库 `docs/index.html`

## 在线阅读

https://you-xiang.github.io/ai-daily-brief/

（微信内直接点开即可）

## 需要配置的 Secrets

仓库 Settings → Secrets and variables → Actions，添加：

| Secret | 说明 | 示例 |
|--------|------|------|
| `CTYUN_API_KEY` | 电信 AI Store 的 API Key（SK 开头） | `SKxxxxxxxx` |
| `CTYUN_MODEL` | 模型 ID，在天翼云模型广场查看 | `deepseek-v3` |
| `CTYUN_BASE_URL` | API 地址（可选，默认 wishub 网关） | `https://wishub-x1.ctyun.cn/v1` |
| `PUSH_TOKEN` | 微信推送 token（可选，留空则只更新网页） | - |
| `PUSH_URL` | 微信推送接口（可选） | - |

## 手动触发

Actions → AI Daily Brief → Run workflow
