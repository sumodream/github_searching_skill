# GitHub 搜索筛选规则

## 说明
本文件为参考文档，**所有筛选逻辑由 `scripts/main.py` 自动执行**，Agent 无需手动干预。

## main.py 自动执行的筛选

| 条件 | 规则 | 默认值 |
|------|------|--------|
| Star 数 | `stars:>=N` | >= 2000 |
| 更新时间 | `pushed:>YYYY-MM-DD` | > 6个月前 |
| 归档状态 | `archived:false` | 必选项 |
| README | `has:readme` | 必选项 |

## 动态降级策略

当结果不足 5 条时，main.py 自动放宽：
1. Star 门槛: 2000 → 1000 → 500 → 0
2. 更新时间: 6个月 → 12个月 → 24个月

## 排序规则

main.py `search` 命令返回的 `merged` 数组已排序：
1. `verified=true`（本地库）优先
2. 按 `star_count` 降序
3. 最多 20 条

## Agent 注意事项

- 调用 `main.py search` 即可，无需手动构建查询语句
- 所有筛选和排序已由 main.py 完成
- 如遇 API 错误，按 SKILL.md 错误处理表响应
