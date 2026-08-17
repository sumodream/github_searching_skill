# GitHub 项目搜索与推荐

[![Version](https://img.shields.io/badge/version-4.4.0-blue.svg)](./SKILL.md)
[![Projects](https://img.shields.io/badge/projects-2377-green.svg)](./data/projects_db.json)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](./LICENSE)

多源 GitHub 项目搜索与推荐技能，整合 **12+ 数据源**，覆盖本地精选库、GitHub API、社区精选月刊、技术周刊、Awesome 列表及跨平台智能体技能搜索。内置 6 维度安全评价体系与源码级安全扫描，解决 AI 幻觉推荐差项目的问题。

---

## ✨ 核心特性

### 📊 多源数据整合

| 数据源 | 说明 | 规模 |
|--------|------|------|
| **本地精选库** | 人工筛选的中文项目元数据 | 2,377 个项目 |
| **GitHub API** | 实时搜索公开仓库 | 按需查询 |
| **HelloGitHub** | 社区精选月刊 | CC BY-NC-ND 4.0 |
| **阮一峰周刊** | 科技爱好者周刊工具推荐 | 每周更新 |
| **Awesome 列表** | 各领域精选清单索引 | 按需检索 |
| **MCP Registry** | 官方 MCP 注册中心 | 4,500+ 服务器 |
| **Smithery** | MCP 平台 | 7,300+ 服务器 |
| **Glama** | MCP 目录，自带质量评级 | 67,960+ 服务器 |
| **Hermes** | Agent Skills Hub | 100+ 验证技能 |
| **虾评** | Agent 技能评测平台 | 用户评分 + SBI |
| **SkillHub** | 腾讯技能生态 | 13,000+ 技能 |

### 🔒 安全评估体系

- **6 维度评价**：代码透明度 / 来源可信度 / 维护活跃度 / 社区采纳度 / 权限透明度 / 安全记录
- **源码级扫描**：eval/exec 检测、混淆 base64、TLS 降级、环境变量窃取等 9 类风险识别
- **多源交叉验证**：识别控评行为，过滤虚假好评
- **红旗项检测**：标注可疑模式（如短期内大量好评）

### 🌍 区域适用性检测

- `domestic`：国内可直接使用（无需 VPN）
- `international`：需要海外网络环境
- `universal`：全球通用

### 📈 精确 Star 增量统计

基于 GitHub Events API 统计近 30 天 / 90 天 WatchEvent，反映项目真实热度趋势。

### 🤖 智能体技能搜索

专项搜索 AI Agent 技能、MCP Server、工具等，支持：
- 按平台分类（Coze / Dify / AutoGPT / Cursor 等）
- 按用途分类（开发工具 / 数据处理 / 内容生成等）
- 信任评估与安全评级

---

## 📁 项目结构

```
github_searching_skill/
├── SKILL.md                    # 技能定义文档（触发条件、工作流、示例）
├── README.md                   # 本文件
├── LICENSE                     # MIT 许可证
├── data/
│   └── projects_db.json        # 本地精选项目库（2,377 个项目）
├── references/
│   ├── filter-rules.md         # 过滤规则说明
│   ├── output-templates.md     # 输出模板定义
│   └── tag-guide.md            # 标签体系说明
└── scripts/
    ├── main.py                 # 主脚本（搜索、分析、统计）
    └── radar_chart.py          # 信任评估雷达图生成
```

### 本地库字段说明

每个项目包含 12 个字段：

```json
{
  "repo_name": "owner/repo",
  "display_name": "项目显示名",
  "about": "一句话定位",
  "tags": ["标签1", "标签2"],
  "scene": "适合场景",
  "verified": true,
  "html_url": "https://github.com/...",
  "value_prop": "可尝试价值",
  "form": "开源项目/应用/网页",
  "cost": "上手成本",
  "source_url": "推荐来源链接",
  "proj_type": "开源项目/工具/资源"
}
```

---

## 🚀 快速开始

### 在 Coze 中使用

1. 在 Coze 中安装此技能
2. 直接对话即可触发，例如：
   - "帮我找一个 Python 爬虫项目"
   - "分析一下 langchain 这个项目"
   - "有没有安全的 MCP server"
   - "国内能用的 AI 工具推荐"

### 环境变量配置（可选）

**零配置即可使用**，无需任何配置即可体验全部基础功能。

| 变量名 | 用途 | 获取方式 |
|--------|------|----------|
| `COZE_GITHUB_TOKEN_*` | 提升 GitHub API 限额至 5000次/时 | [GitHub Settings](https://github.com/settings/tokens) |
| `COZE_SMITHERY_TOKEN` | 启用 Smithery 源（7300+ MCP） | [smithery.ai](https://smithery.ai) |
| `XIAPING_KEY` | 启用虾评源（Agent 技能） | [xiaping.coze.com](https://xiaping.coze.com) |

### 能力矩阵

| 功能 | 无 Token | 有 Token |
|------|:--------:|:--------:|
| 本地库搜索（2377 项目） | ✅ | ✅ |
| GitHub API 实时搜索 | ✅ (60次/时) | ✅ (5000次/时) |
| HelloGitHub / 阮一峰 / Awesome | ✅ | ✅ |
| 项目详情 / 分析 / 文档生成 | ✅ | ✅ |
| 近 30/90 天 star 精确增量 | ⚠️ 跳过 | ✅ |
| 信任评估 / 安全评估 | ✅ | ✅ |
| 跨平台搜索（MCP / Hermes 等） | ✅ | ✅ |

---

## 📖 使用示例

### 搜索项目
```
用户: 帮我找一个好用的 PDF 处理工具
→ 搜索本地库 + GitHub API，返回带信任评分的结果
```

### 项目分析
```
用户: 分析一下 https://github.com/langchain-ai/langchain
→ 获取仓库详情、依赖分析、star 趋势、信任评估雷达图
```

### 安全评估
```
用户: 这个 MCP server 安全吗？
→ 6 维度评分 + 源码扫描 + 多源交叉验证
```

### 领域发现
```
用户: 本地库有哪些领域的项目？
→ 展示 11 个领域的项目分布统计
```

---

## 🏷️ 本地库领域分布

| 领域 | 项目数 | 主要标签 |
|------|--------|----------|
| 开源/工具/效率 | ~800 | 开源、工具、Python、效率 |
| AI | ~530 | AI、机器学习、LLM、Agent |
| 编程语言 | ~410 | JavaScript、TypeScript、Go、Rust |
| 跨平台/桌面 | ~190 | Electron、Tauri、桌面应用 |
| Web 开发 | ~170 | React、Vue、Next.js、API |
| 数据/数据库 | ~100 | 数据分析、数据库、可视化 |
| DevOps/云 | ~80 | Docker、K8s、CI/CD |
| 安全 | ~60 | 安全、加密、渗透测试 |
| 移动开发 | ~50 | iOS、Android、Flutter |
| 教育/学习 | ~40 | 教程、学习、面试 |
| 其他 | ~40 | 各类长尾标签 |

---

## 📝 版本历史

| 版本 | 主要更新 |
|------|----------|
| v4.4.0 | 本地库从飞书多维表格覆盖（2377 条），新增 5 字段，标签归并，domain_map 重写 |
| v4.3.0 | 精确 star 增量（Events API），零配置可用 |
| v4.2.0 | 区域适用性检测（domestic/international/universal） |
| v4.1.0 | 源码级安全扫描，多源交叉验证，Hermes/虾评/SkillHub 源 |
| v4.0.0 | 6 维度安全评价，MCP Registry/Smithery/Glama 跨平台源 |
| v3.x | 飞书同步本地库，同类推荐+雷达图，trust/docs/agent 命令 |

---

## 📄 许可证

本项目采用 [MIT License](./LICENSE)。

第三方数据源请遵守各自许可协议：
- HelloGitHub 数据：CC BY-NC-ND 4.0（署名-非商业-禁止演绎）
- GitHub API 数据：遵循 [GitHub API Terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#api-terms)
- Awesome 列表：各仓库独立许可证

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request！

- 报告 Bug
- 建议新功能
- 改进文档
- 添加新项目到本地库

---

<p align="center">
  <strong>🔍 让 AI 推荐靠谱的 GitHub 项目</strong>
</p>
