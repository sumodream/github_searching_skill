# 输出格式模板

本模板与 `scripts/main.py` 的 JSON 输出字段对应，Agent 解析 JSON 后按以下格式渲染。

---

## 格式A: 快速列表

**触发**: 用户说"找一下..." / "有哪些..." / "推荐几个..."
**数据源**: `main.py search` 命令的 `merged` 数组

**渲染模板**:
```
🔍 找到 {count} 个相关项目：
{api_status_line}

{index}. {display_name} {verified_mark}
   {repo_name} | ⭐{star_count} | {language} | {tag1} · {tag2}

💡 说"看第{N}个"获取详情，或"对比前{N}个"进行横向对比
```

**字段映射**:
- `display_name`: 来自 JSON `display_name`
- `repo_name`: 来自 JSON `repo_name`
- `star_count`: 来自 JSON `star_count`（格式化如 95K）
- `language`: 来自 JSON `language`
- `tags`: 来自 JSON `tags` 前2个
- `verified_mark`: `verified=true` 时显示 ✅，否则 ⏳
- `api_status_line`: `api_available=false` 时显示"⚠️ GitHub API 未启用，仅展示本地库结果（2853项目）。配置 Token 可获取更多推荐。"

---

## 格式B: 详细卡片

**触发**: 用户说"看第N个" / "详细介绍一下..." / "分析一下..."
**数据源**: `main.py analyze` 命令的完整 JSON

**渲染模板**:
```
📦 {display_name} {verified_mark}
   {repo_name}
   ⭐ {star_count} | {language} | {license} | 创建于 {created_at}
   🏷️ 类型: {project_type} | 语言组成: {languages_summary}

   🏷️ {tag1} · {tag2} · {tag3}

   📝 {about}

   📦 部署支持: {docker_support ? "✅ Docker" : "❌ 无Docker"} | 安装: {install_methods.join(", ")}
   🕐 项目年龄: {age_days} 天 | 日均增长: {star_per_day} ⭐/天
   📈 Star趋势: {star_history_url}

   🔗 {html_url}

   💡 说"趋势如何"查看热度分析，或"支持docker吗"查看部署详情
```

**字段映射**:
- 基础字段: `display_name`, `repo_name`, `star_count`, `language`, `license`, `created_at`, `about`, `html_url`
- 分析字段: `docker_support`, `install_methods`, `age_days`, `star_per_day`, `star_history_url`
- 项目画像: `project_type` (tool/library/application/framework/tutorial/resource), `languages_summary` (如 "Python 92.3%, CSS 5.1%")
- `tags`: 来自 JSON `tags`

**project_type 展示逻辑**:
- 用中文名展示: tool→工具, library→开发库, application→应用, framework→框架, tutorial→教程, resource→资源集合
- `languages_summary` 紧跟 `project_type`，让用户一眼看出"类型+复杂度"
- 单语言占比 >85% 时，用 `🎯单语言` 标记（学习场景：适合重写）

---

## 格式C: 对比表格

**触发**: 用户说"对比..." / "哪个好" / "有什么区别"
**数据源**: 多个 `main.py analyze` 命令的结果数组

**渲染模板**:
```
📊 {topic} 项目对比

| 维度 | {project1.display_name} | {project2.display_name} | {project3.display_name} |
|------|------------------------|------------------------|------------------------|
| Star | ⭐{star1} | ⭐{star2} | ⭐{star3} |
| 语言 | {lang1} | {lang2} | {lang3} |
| 创建时间 | {created1} | {created2} | {created3} |
| 最后更新 | {update1} | {update2} | {update3} |
| 项目年龄 | {age1}天 | {age2}天 | {age3}天 |
| 日均增速 | {spd1}⭐/天 | {spd2}⭐/天 | {spd3}⭐/天 |
| Docker | {docker1} | {docker2} | {docker3} |
| 安装方式 | {install1} | {install2} | {install3} |
| 主要特点 | {about1} | {about2} | {about3} |

💡 {recommendation}
```

**字段映射**: 每个项目的 analyze JSON 字段

---

## 格式D: 趋势分析

**触发**: 用户说"趋势如何" / "最近火吗" / "增长快吗"
**数据源**: `main.py analyze` 命令的 JSON

**渲染模板**:
```
📈 {display_name} 热度趋势分析

📊 关键指标
├── 当前 Star: {star_count}
├── 项目年龄: {age_days} 天（创建于 {created_at}）
├── 最后更新: {last_update}
├── 状态: {status == "active" ? "✅ 活跃维护" : "⚠️ 已归档"}
└── 语言: {language}

📈 增长分析
├── 日均增速: {star_per_day} ⭐/天
├── 30天预测: +{round(star_per_day * 30)} ⭐
├── 趋势判断: {trend_emoji} {trend_desc}
└── 相对热度: {heat_level}

📉 参考数据
├── Star历史图: {star_history_url}
└── 项目主页: {html_url}

💡 {insight}
```

**字段映射**:
- `star_count`, `age_days`, `created_at`, `last_update`, `status`, `language`: 基础字段
- `star_per_day`: 分析字段
- `star_history_url`: 分析字段
- `trend_emoji`: 📈(>10/天) / 🌡️(5-10/天) / ➡️(<5/天)
- `heat_level`: 🔥(>50K) / 🌡️(10K-50K) / 😐(2K-10K) / ❄️(<2K)

---

## 格式选择逻辑

```
if 用户输入匹配 "找一下|有哪些|推荐几个":
    格式 = A
    if api_available == false:
        追加 api_status_line 提示
    if 短对话 + 本地库有同类项目:
        追加 格式E（同类推荐一行）
elif 用户输入匹配 "看第N个|详细|分析":
    格式 = B
    if 短对话 + 本地库有同类项目:
        追加 格式E（同类推荐一行）
elif 用户输入匹配 "对比|哪个好|区别|对比一下":
    if 对比项目数 <= 3:
        格式 = F  # 雷达图（优先生成 HTML 可视化）
    else:
        格式 = C  # 4+项目用文字表格
elif 用户输入匹配 "趋势|火吗|增长":
    格式 = D
elif 用户输入匹配 "类似的|替代品|其他选择":
    格式 = A + 格式E（必定展示同类推荐）
elif 用户输入匹配 "练手|重写|学习练手":
    格式 = G（rewrite 模式）
elif 用户输入匹配 "贡献|提PR|参与开源|入门开源":
    格式 = G（contribute 模式）
elif 用户输入匹配 "本地库|领域|能搜什么|有什么类别":
    格式 = H（db-stats）
elif 用户输入匹配 "按.*浏览|有哪些.*项目|按标签":
    格式 = I（discover）
else:
    格式 = A  # 默认
```

---

## 格式E: 同类推荐（轻量一行）

**触发**: 搜索结果末尾，满足 SKILL.md 横向同类推荐触发条件时追加
**数据源**: Agent 从 projects_db.json 中按标签重叠筛选

**渲染模板**:
```
🔁 同类项目: {display_name_A} ({区分特征}) · {display_name_B} ({区分特征}) · {display_name_C}
💡 说"对比一下"查看详细对比表
```

**字段说明**:
- `display_name`: 同类项目名称
- `区分特征`: 一句话说明与搜索目标的差异点（如"更轻量"、"Rust 实现"、"云端优先"）
- 最多 3 个，不展开为卡片

**渲染位置**: 紧跟在格式A/B的最后一行之后，空一行

**示例**:
```
🔁 同类项目: FastAPI (异步高性能) · Django (全功能企业级) · Tornado (长连接友好)
💡 说"对比一下"查看详细对比表
```

**重要约束**:
- 仅一行，不超过 80 字
- 不替代搜索结果，仅作补充提示
- 用户未主动说"对比"时不展开

---

## 格式F: 雷达图对比（可视化）

**触发**: 用户说"对比一下" / "画个图" / "可视化对比" / "雷达图"，且对比项目 ≤ 3 个
**数据源**: 多个 `main.py analyze` 结果 + projects_db.json 补充字段
**生成工具**: `python scripts/radar_chart.py --data-file <json> --output <html>`

**渲染流程**:
1. 对每个项目执行 `main.py analyze`
2. 从 projects_db.json 读取 learning_cost/scene 补充本地字段（按 repo_name 匹配；不在本地库的项目使用默认值）
3. 将所有项目数据合并写入临时 JSON 文件
4. 调用 radar_chart.py 生成 HTML
5. 发送 HTML 文件 + 一行极简结论

**成功时渲染模板**:
```
📊 {项目A} vs {项目B} 雷达图已生成
{项目A} 在{维度X}领先 · {项目B} 在{维度Y}领先
[雷达图 HTML 文件]

💡 说"详细对比"查看文字表格
```

**失败降级**:
- 脚本执行失败 → 重试 1 次
- 2次均失败 → 降级为格式C（文字对比表格），提示"图表生成异常，已切换为文字对比"
- 输出文件不存在或 < 100 字节 → 同上

**五维评分说明**:

| 维度 | 分数来源 | 高分条件 |
|------|---------|---------|
| 社区活跃度 | star_count + star_per_day + last_update | 高stars + 高增速 + 近期更新 |
| 功能覆盖 | tags 数量 + scene | 多标签 + 有场景描述 |
| 上手友好度 | learning_cost + docker_support + install_methods | 低学习成本 + Docker + 多安装方式 |
| 文档质量 | has_wiki + about + install_methods | 有wiki + 描述完整 + 有安装说明 |
| 维护状态 | status + last_update + star_per_day | 活跃 + 近期更新 + 高增速 |

**重要约束**:
- 图表成功时，文字部分**不重复罗列各维度数值**，仅一行结论
- 4+项目对比直接用格式C，不生成雷达图
- 雷达图 HTML 文件输出到 `/tmp/` 目录，不持久化

---

## 格式G: 学习导向推荐

**触发**: 用户说"想练手" / "想重写学习" / "想参与开源" / "找个项目练手"
**数据源**: `main.py learning rewrite/contribute "关键词" [语言]`

**rewrite 模式渲染模板**:
```
🎯 适合重写学习的项目（可移植性优先）：

{index}. {display_name} {verified_mark}
   {repo_name} | ⭐{star_count} | 🍴{forks_count} | {project_type}
   语言: {languages_summary}  {single_lang_mark}
   📝 {_learning_note}

💡 语言越单一、代码量越小的项目越适合重写学习
```

**contribute 模式渲染模板**:
```
🤝 适合参与贡献的项目（友好度优先）：

{index}. {display_name} {verified_mark}
   {repo_name} | ⭐{star_count} | 📋{open_issues} issues | {project_type}
   语言: {languages_summary}
   📝 {_learning_note}

💡 有 good-first-issue 标签的项目更适合新手入门
```

**字段说明**:
- `project_type`: 中文名展示（工具/开发库/应用/框架/教程/资源集合）
- `languages_summary`: 语言组成百分比
- `single_lang_mark`: 主语言占比 >85% 时显示 `🎯单语言，适合重写`
- `_learning_note`: 评分依据简述（如 "forks:45, stars:800, 文档:2/2"）
- `_learning_score`: 内部排序用，不展示给用户

**排序规则**: 按 `_learning_score` 降序

**重要约束**:
- 每种模式最多展示 10 个项目
- rewrite 模式强调简单性，contribute 模式强调友好度
- 不展示纯教程/资源类项目（project_type 为 tutorial/resource 时过滤）
- 本地库项目标注 ✅，GitHub 搜索结果标注 ⏳


---

## 格式H: 本地库统计（v3.4.0 新增）

**触发**: 用户说"本地库有哪些领域" / "能搜什么" / "有什么类别"
**数据源**: `main.py db-stats` 命令

**渲染模板**:
```
📊 本地库统计

📦 共 {total_projects} 个精选项目 | 数据更新于 {db_last_modified} | {unique_tags} 种标签

🏷️ 领域覆盖：
  AI/机器学习: {count}个项目 | 开发工具: {count}个项目 | 编程语言: {count}个项目
  跨平台/桌面: {count}个项目 | 基础设施: {count}个项目 | 自动化/爬虫: {count}个项目
  Web开发: {count}个项目 | 金融/交易: {count}个项目 | 安全: {count}个项目
  内容/文档: {count}个项目 | 游戏: {count}个项目

{api_status_hint}

💡 说"按AI浏览"或"按Rust浏览"查看某个领域的项目
```

**字段说明**:
- `total_projects`: 项目总数
- `db_last_modified`: 数据库最后更新日期（来自文件修改时间）
- `domain_coverage`: 各领域项目数
- `api_status_hint`: API 不可用时提示"配置 GitHub Token 可获取更多实时搜索结果"

---

## 格式I: 按标签浏览（v3.4.0 新增）

**触发**: 用户说"按...浏览" / "有哪些AI项目" / "按标签找"
**数据源**: `main.py discover "标签"` 命令

**渲染模板**:
```
🏷️ 标签「{tag}」下的项目（共 {total} 个）：

{index}. {display_name} ✅
   {repo_name} | {tag1} · {tag2} · {tag3}
   📝 {about}

💡 说"看第{N}个"获取详情
```

**字段说明**:
- `tag`: 用户指定的标签关键词
- `total`: 匹配项目总数
- 所有本地库项目均为 verified ✅
- `about`: 项目简介（截断过长内容）
