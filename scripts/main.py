#!/usr/bin/env python3
"""
GitHub 项目搜索与推荐 - 核心执行脚本
功能：
1. 从内置 JSON 数据库搜索项目（Agent 也可直接读取 JSON）
2. 调用 GitHub Search API 搜索项目（支持中英文关键词）
3. 采集 GitHub Trending 热门项目（独立命令）
4. 查询项目详情和 README 分析
5. 项目状态检测
6. HelloGitHub 社区精选项目搜索（解析月刊 markdown）
7. Awesome 列表搜索（按领域发现优质 awesome 清单）

环境变量：
- COZE_GITHUB_TOKEN_{SKILL_ID}: 通过 skill_draft_credential 注入的 GitHub Token
"""

import os
import sys
import json
import re
import base64
import math
from datetime import datetime, timedelta
from typing import List, Dict

from coze_workload_identity import requests

# ============ 配置 ============
GITHUB_API_BASE = "https://api.github.com"

# 内置项目数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "projects_db.json")

# 默认筛选参数
DEFAULT_MIN_STARS = 2000

# 中文停用词（expand_keywords 提取后过滤）
_CN_STOPWORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '他', '她', '它', '们', '那', '些', '什么', '怎么', '如何',
    '来', '用', '做', '开发', '服务', '项目', '工具', '找', '请', '帮', '给',
    '想', '能', '可以', '需要', '适合', '相关', '关于', '进行', '实现',
    '管理', '系统', '平台', '框架', '库', '包', '模块', '组件',
}

# 中英文关键词映射（用于 GitHub 搜索扩展）
# 策略：贪心最长匹配 → 中文词替换为英文搜索词
KEYWORD_MAP = {
    # ---- Web 开发 ----
    "Web框架": "web framework",
    "前端框架": "frontend framework",
    "后端框架": "backend framework",
    "前端": "frontend web",
    "后端": "backend server",
    "全栈": "fullstack",
    "微服务": "microservice",
    "API网关": "api gateway",
    "GraphQL": "graphql",
    "REST": "rest api",
    # ---- 编程语言/形式 ----
    "命令行": "cli command-line terminal",
    "终端": "terminal cli shell",
    "脚本语言": "scripting language",
    # ---- 数据与可视化 ----
    "可视化": "visualization chart",
    "数据分析": "data analysis pandas",
    "数据采集": "data collection scraping",
    "数据处理": "data processing etl",
    "机器学习": "machine learning",
    "深度学习": "deep learning neural-network",
    "自然语言处理": "nlp natural language processing",
    "大模型": "llm large-language-model",
    "图像识别": "image recognition computer-vision",
    "计算机视觉": "computer-vision image",
    "推荐系统": "recommendation system",
    # ---- 基础设施 ----
    "数据库": "database sql",
    "关系型数据库": "relational database sql",
    "文档数据库": "document database mongodb",
    "缓存": "cache redis",
    "消息队列": "message-queue mq",
    "搜索引擎": "search engine",
    # ---- 运维与安全 ----
    "自动化": "automation",
    "监控": "monitoring observability",
    "日志": "logging",
    "安全": "security",
    "渗透测试": "penetration-testing security",
    "网络代理": "proxy",
    # ---- 部署与平台 ----
    "自托管": "self-hosted",
    "跨平台": "cross-platform",
    "容器化": "container docker",
    "云原生": "cloud-native",
    # ---- 应用类型 ----
    "桌面应用": "desktop application electron",
    "移动应用": "mobile app",
    "知识管理": "knowledge-management wiki",
    "工作流引擎": "workflow engine",
    "游戏引擎": "game-engine",
    "博客系统": "blog cms",
    "内容管理": "cms content-management",
    "电商": "ecommerce shop",
    # ---- 开发工具 ----
    "代码编辑器": "code-editor ide",
    "代码生成": "code-generation",
    "静态分析": "static-analysis lint",
    "代码审查": "code-review",
    "调试工具": "debugging",
    "测试框架": "testing framework",
    # ---- 网络与通信 ----
    "即时通讯": "instant-messaging chat",
    "视频会议": "video-conference webrtc",
    "邮件": "email smtp",
    # ---- 文件与文档 ----
    "文档工具": "documentation",
    "模板引擎": "template engine",
    # ---- 学习与面试 ----
    "教程": "tutorial learning",
    "面试": "interview preparation",
    "算法": "algorithm data-structure",
    # ---- 原有映射 ----
    "量化交易": "quantitative-trading",
    "爬虫": "web-crawler scraping",
    "低代码": "low-code no-code",
    "金融终端": "financial-terminal trading",
    "虚拟人": "virtual-human avatar",
    "舆情分析": "sentiment-analysis opinion",
    "云桌面": "cloud-desktop remote",
    "数据归档": "web-archiving archive",
    # ---- 更多领域 ----
    "游戏": "game",
    "区块链": "blockchain",
    "密码管理": "password-manager",
    "文件管理": "file-manager",
    "下载工具": "downloader",
    "翻译": "translation",
    "OCR": "ocr text-recognition",
    "语音识别": "speech-recognition asr",
    "音乐": "music audio",
    "图片处理": "image-processing",
    "PDF": "pdf",
    "电子书": "ebook reader",
    "笔记": "note-taking",
    "日程管理": "calendar schedule",
    "代理工具": "proxy vpn",
    "科学上网": "proxy vpn",
    "网络工具": "network-tool",
}


def _has_github_token() -> bool:
    """检查是否配置了 GitHub Token"""
    return bool(os.environ.get("COZE_GITHUB_TOKEN_7649400342840426502", ""))


def get_github_token() -> str:
    """从环境变量获取 GitHub Token（通过 skill 凭证注入）

    v3.4.0: 不再抛出异常，返回空字符串表示无 Token。
    调用方应根据 _has_github_token() 判断是否走 API 路径。
    """
    return os.environ.get("COZE_GITHUB_TOKEN_7649400342840426502", "")


def github_api_request(endpoint: str, params: Dict[str, str] = None) -> Dict:
    """发送 GitHub API 请求

    v4.3.0: 无 Token 时走未认证模式（60次/小时），不再直接拒绝。
    有 Token 时走认证模式（5000次/小时）。
    速率限制时返回明确的降级提示。
    """
    url = f"{GITHUB_API_BASE}{endpoint}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Project-Search-Skill",
    }

    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 404:
            return {"error": "not_found", "status": 404}
        elif response.status_code == 403:
            # 检查是否速率限制
            remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
            reset_time = response.headers.get("X-RateLimit-Reset", "")
            if token:
                return {"error": "rate_limited", "status": 403,
                        "message": f"认证 API 速率限制（剩余 {remaining}），请稍后再试"}
            else:
                return {"error": "rate_limited", "status": 403,
                        "message": f"未认证 API 限额已用完（60次/小时）。配置 GitHub Token 可提升至 5000次/小时"}
        elif response.status_code == 401:
            return {"error": "invalid_token", "status": 401,
                    "message": "GitHub Token 无效或已过期，请更新凭证"}
        elif response.status_code >= 400:
            return {"error": "api_error", "status": response.status_code, "message": response.text[:200]}
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": "request_failed", "message": str(e)}


# ============ 1. 内置数据库搜索 ============

def load_local_db() -> List[Dict]:
    """加载内置项目数据库"""
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def search_local_db(query: str, language: str = None) -> List[Dict]:
    """
    从内置数据库搜索项目（支持关键词子串匹配）
    
    注意：Agent 可以直接读取 projects_db.json 做语义匹配，
    此函数仅作为脚本级搜索备用。
    """
    projects = load_local_db()
    results = []
    query_lower = query.lower()

    for project in projects:
        score = 0

        # 1. 名称匹配
        name = project.get("display_name", "").lower()
        if query_lower in name:
            score += 10

        # 2. 标签匹配
        project_tags = [t.lower() for t in project.get("tags", [])]
        for tag in project_tags:
            if query_lower in tag:
                score += 8

        # 3. 场景匹配
        scene = project.get("scene", "").lower()
        if query_lower in scene:
            score += 5

        # 4. 简介匹配
        about = project.get("about", "").lower()
        if query_lower in about:
            score += 3

        # 5. 价值主张匹配（v4.4.0 新增）
        value_prop = project.get("value_prop", "").lower()
        if value_prop and query_lower in value_prop:
            score += 4

        # 6. 形式/类型匹配（v4.4.0 新增）
        form = project.get("form", "").lower()
        if form and query_lower in form:
            score += 3
        proj_type = project.get("proj_type", "").lower()
        if proj_type and query_lower in proj_type:
            score += 3

        # 7. 上手成本匹配（v4.4.0 新增）
        cost = project.get("cost", "").lower()
        if cost and query_lower in cost:
            score += 2

        # 8. 语言过滤
        if language:
            proj_lang = project.get("language", "").lower()
            if language.lower() not in proj_lang:
                score = 0

        if score > 0:
            project_copy = dict(project)
            project_copy["_match_score"] = score
            project_copy["_source"] = "local_db"
            project_copy["verified"] = True
            results.append(project_copy)

    results.sort(key=lambda x: x["_match_score"], reverse=True)
    return results[:20]


# ============ 1b. 本地库统计与发现 ============

def _get_db_metadata() -> Dict:
    """
    获取本地库元数据（新鲜度、版本等）

    v3.4.0 新增：为搜索结果提供新鲜度标注
    """
    db_file = os.path.abspath(DB_PATH)
    meta = {
        "total_projects": 0,
        "db_file_size_kb": 0,
        "db_last_modified": None,
    }
    try:
        stat = os.stat(db_file)
        meta["db_file_size_kb"] = round(stat.st_size / 1024, 1)
        meta["db_last_modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        pass
    return meta


def db_stats() -> Dict:
    """
    本地库统计信息：项目总数、标签分布、领域覆盖

    v3.4.0 新增命令：帮助用户了解本地库能覆盖哪些领域，
    解决菜鸟月月评价中提出的"小众领域覆盖不透明"问题。
    """
    projects = load_local_db()
    meta = _get_db_metadata()

    from collections import Counter
    tag_counts = Counter()
    for p in projects:
        for t in p.get("tags", []):
            tag_counts[t] += 1

    # 领域分类统计（基于归并+分号拆分后标签，v4.4.0）
    domain_map = {
        "AI": ["AI", "RAG", "MCP", "Claude Code", "Cursor", "Skills",
               "OpenClaw", "多模态", "语音", "OCR"],
        "开源/工具/效率": ["开源", "工具", "效率", "CLI", "终端", "免费"],
        "Web/前端": ["前端", "React", "Web", "低代码", "CMS", "网页"],
        "开发": ["编辑器", "IDE", "调试", "DevOps", "Git", "测试",
                "框架", "API", "编程语言"],
        "基础设施": ["Docker", "数据库", "监控", "Shell", "运维", "部署"],
        "编程语言": ["Python", "Rust", "Go", "TypeScript", "JavaScript",
                    "Java", "C++", "Swift", "Kotlin", "C"],
        "金融": ["金融", "量化"],
        "安全/隐私": ["安全", "隐私"],
        "内容/知识": ["知识管理", "文档", "博客", "Markdown", "PDF",
                    "教程", "学习", "资源列表"],
        "跨平台/桌面": ["跨平台", "桌面应用", "macOS", "Windows", "Linux",
                      "Android", "iOS", "Tauri", "Flutter", "Electron"],
        "游戏/多媒体": ["游戏", "视频", "音乐", "图片处理", "3D", "动画",
                      "语音", "TTS"],
    }

    domain_stats = {}
    for domain, domain_tags in domain_map.items():
        count = sum(tag_counts.get(t, 0) for t in domain_tags)
        # 去重：一个项目可能匹配多个标签，用集合统计
        matched_projects = set()
        for p in projects:
            p_tags = set(p.get("tags", []))
            if p_tags & set(domain_tags):
                matched_projects.add(p.get("repo_name", ""))
        domain_stats[domain] = {
            "project_count": len(matched_projects),
            "top_tags": [(t, tag_counts[t]) for t in domain_tags if t in tag_counts][:5],
        }

    return {
        "total_projects": len(projects),
        "unique_tags": len(tag_counts),
        "db_last_modified": meta["db_last_modified"],
        "db_file_size_kb": meta["db_file_size_kb"],
        "top_tags": [(t, c) for t, c in tag_counts.most_common(30)],
        "domain_coverage": domain_stats,
        "api_available": True,
        "token_mode": "authenticated" if _has_github_token() else "unauthenticated",
    }


def discover(tag: str = None, limit: int = 20) -> Dict:
    """
    按标签浏览本地库项目

    v3.4.0 新增命令：让用户按领域/标签浏览本地库，
    解决"不知道本地库能覆盖什么"的问题。

    参数：
        tag: 标签关键词（如 AI, Python, Rust, 工具）
        limit: 返回项目数量上限
    """
    projects = load_local_db()
    results = []

    if tag:
        tag_lower = tag.lower()
        for p in projects:
            p_tags = [t.lower() for t in p.get("tags", [])]
            # 精确匹配或子串匹配
            if any(tag_lower == t or tag_lower in t for t in p_tags):
                results.append({**p, "_source": "discover"})
        # 按标签数排序（标签越多的项目越可能是该领域的核心项目）
        results.sort(key=lambda x: len(x.get("tags", [])), reverse=True)
    else:
        # 无标签时随机展示项目（按 display_name 排序保证稳定）
        results = [{**p, "_source": "discover"} for p in projects]
        results.sort(key=lambda x: x.get("display_name", ""))

    return {
        "tag": tag,
        "total": len(results),
        "projects": results[:limit],
        "api_available": True,
        "token_mode": "authenticated" if _has_github_token() else "unauthenticated",
    }


# ============ 2. GitHub Search API ============

def expand_keywords(keywords: str) -> str:
    """
    将中文自然语言描述转换为英文搜索词，用于 GitHub Search API

    策略：贪心最长匹配 KEYWORD_MAP → 提取剩余英文词 → 输出纯英文查询串

    示例：
        "Python的Web框架来开发后端API服务"
        → 匹配: Web框架→web framework, 后端→backend server
        → 提取英文: Python, API
        → 输出: "python web framework backend server api"

    修复历史：
        v3.2.0 及更早版本的 bug：
        - any(c in keywords for c in cn) 导致"前端"错误匹配"金融终端"的"端"
        - 全中文模糊匹配产生无关英文词
        v3.3.0：改为贪心最长匹配，避免子串误匹配
    """
    keywords = keywords.strip()
    if not keywords:
        return keywords

    mapped_terms = []
    remaining = keywords

    # 贪心最长匹配：按 KEYWORD_MAP 键长度降序排列
    # 优先匹配长词（如"前端框架"优先于"前端"），避免子串截断
    sorted_keys = sorted(KEYWORD_MAP.keys(), key=len, reverse=True)

    for cn_key in sorted_keys:
        if cn_key in remaining:
            mapped_terms.append(KEYWORD_MAP[cn_key])
            remaining = remaining.replace(cn_key, ' ', 1)  # 替换已匹配部分

    # 提取剩余英文单词（过滤单字母和常见虚词）
    _EN_STOPWORDS = {'in', 'on', 'at', 'to', 'for', 'of', 'the', 'a', 'an', 'is', 'it',
                     'and', 'or', 'with', 'from', 'by', 'as', 'be', 'do', 'no', 'not'}
    en_words = [w for w in re.findall(r'[a-zA-Z][a-zA-Z0-9+#.]*', remaining)
                if len(w) > 1 and w.lower() not in _EN_STOPWORDS]
    mapped_terms.extend(en_words)

    # 提取剩余中文词（2字以上，过滤停用词）— 不加入 GitHub 查询但可作参考
    cn_remaining = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', remaining)
                    if w not in _CN_STOPWORDS]

    # 构建最终查询：英文词用空格连接（GitHub API AND 语义）
    # 将所有映射结果展平为词级别，去重后组合
    if mapped_terms:
        all_words = []
        for term in mapped_terms:
            all_words.extend(term.split())
        seen = set()
        unique_words = []
        for w in all_words:
            w_lower = w.lower()
            if w_lower not in seen:
                seen.add(w_lower)
                unique_words.append(w)
        return ' '.join(unique_words)

    # 如果映射完全失败，返回原始关键词（fallback）
    return keywords


def build_search_query(keywords: str, language: str = None, min_stars: int = None) -> str:
    """构建 GitHub Search API 查询语句"""
    parts = []

    # 关键词（支持中英文扩展）
    if keywords:
        expanded = expand_keywords(keywords)
        parts.append(f"{expanded} in:name,description,readme")

    # 语言
    if language:
        parts.append(f"language:{language}")

    # Star 门槛
    min_stars = min_stars or DEFAULT_MIN_STARS
    parts.append(f"stars:>={min_stars}")

    # 更新时间（6个月内）
    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    parts.append(f"pushed:>{six_months_ago}")

    # 排除归档
    parts.append("archived:false")

    # 有 README
    parts.append("has:readme")

    return " ".join(parts)


def search_github_api(query: str, language: str = None, min_stars: int = None, per_page: int = 30) -> List[Dict]:
    """调用 GitHub Search API 搜索项目"""
    search_q = build_search_query(query, language, min_stars)
    params = {"q": search_q, "sort": "stars", "order": "desc", "per_page": per_page}

    data = github_api_request("/search/repositories", params)

    if "error" in data:
        return [{"error": data.get("message", "搜索失败")}]

    items = data.get("items", [])
    results = []

    for item in items:
        project = {
            "repo_name": item["full_name"],
            "display_name": item["name"],
            "about": item.get("description", ""),
            "tags": item.get("topics", []),
            "star_count": item["stargazers_count"],
            "language": item.get("language", ""),
            "status": "archived" if item.get("archived") else "active",
            "created_at": item["created_at"][:10] if item.get("created_at") else None,
            "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
            "readme_url": f"https://github.com/{item['full_name']}/blob/main/README.md",
            "homepage": item.get("homepage", ""),
            "verified": False,
            "_source": "github_search"
        }
        results.append(project)

    return results


def search_github_with_fallback(query: str, language: str = None) -> List[Dict]:
    """带降级策略的 GitHub 搜索"""
    # 阶段 1: 默认门槛
    results = search_github_api(query, language, min_stars=DEFAULT_MIN_STARS)
    if len(results) >= 5 and "error" not in results[0]:
        return results

    # 阶段 2: 降低 Star 门槛到 1000
    results = search_github_api(query, language, min_stars=1000)
    if len(results) >= 5 and "error" not in results[0]:
        return results

    # 阶段 3: 降低 Star 门槛到 500
    results = search_github_api(query, language, min_stars=500)
    if len(results) >= 3 and "error" not in results[0]:
        return results

    # 阶段 4: 移除 Star 限制
    results = search_github_api(query, language, min_stars=0)
    return results


# ============ 3. Trending 采集（独立命令） ============

def fetch_trending(period: str = "weekly", language: str = None) -> List[Dict]:
    """
    采集 GitHub Trending 项目
    注意：此函数只在用户明确要求 Trending 时调用，search 命令不自动调用
    """
    if period == "daily":
        days = 1
    else:
        days = 7

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 构建查询：最近有推送的高 Star 项目
    query_parts = [f"pushed:>{since}", "archived:false", "has:readme"]
    if language:
        query_parts.append(f"language:{language}")

    search_q = " ".join(query_parts)
    params = {"q": search_q, "sort": "stars", "order": "desc", "per_page": 25}

    data = github_api_request("/search/repositories", params)

    if "error" in data:
        return [{"error": data.get("message", "采集失败")}]

    items = data.get("items", [])
    results = []

    for item in items:
        created = datetime.strptime(item["created_at"][:10], "%Y-%m-%d")
        age_days = (datetime.now() - created).days
        star_per_day = item["stargazers_count"] / max(age_days, 1)

        project = {
            "repo_name": item["full_name"],
            "display_name": item["name"],
            "about": item.get("description", ""),
            "tags": item.get("topics", []),
            "star_count": item["stargazers_count"],
            "language": item.get("language", ""),
            "status": "active",
            "created_at": item["created_at"][:10],
            "last_update": item["pushed_at"][:10],
            "readme_url": f"https://github.com/{item['full_name']}/blob/main/README.md",
            "verified": False,
            "_source": "trending",
            "_star_per_day": round(star_per_day, 2)
        }
        results.append(project)

    return results


# ============ 4. 项目详情查询 ============

def get_repo_details(repo_name: str) -> Dict:
    """查询项目详细信息"""
    data = github_api_request(f"/repos/{repo_name}")

    if "error" in data:
        if data.get("status") == 404:
            return {
                "repo_name": repo_name,
                "status": "deleted",
                "error": "项目已删除或转私人"
            }
        return {"error": data.get("message", "查询失败")}

    status = "archived" if data.get("archived") else ("private" if data.get("private") else "active")

    # 获取语言组成（额外一次 API 调用，仅 details/analyze 时调用）
    languages = get_repo_languages(repo_name)

    return {
        "repo_name": data["full_name"],
        "display_name": data["name"],
        "about": data.get("description", ""),
        "tags": data.get("topics", []),
        "star_count": data["stargazers_count"],
        "language": data.get("language", ""),
        "languages": languages,
        "license": (data.get("license") or {}).get("name", ""),
        "status": status,
        "created_at": data["created_at"][:10] if data.get("created_at") else None,
        "last_update": data["pushed_at"][:10] if data.get("pushed_at") else None,
        "homepage": data.get("homepage", ""),
        "has_wiki": data.get("has_wiki", False),
        "readme_url": f"https://github.com/{data['full_name']}/blob/main/README.md",
        "html_url": data["html_url"],
        "forks_count": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "watchers": data.get("watchers_count", 0),
        "owner_login": data.get("owner", {}).get("login", ""),
        "owner_type": data.get("owner", {}).get("type", ""),
        "pushed_at": data.get("pushed_at", ""),
    }


def get_readme_content(repo_name: str) -> str:
    """
    获取项目 README 内容
    处理多种编码情况
    """
    data = github_api_request(f"/repos/{repo_name}/readme")

    if "error" in data:
        return ""

    content = data.get("content", "")
    encoding = data.get("encoding", "base64")

    if not content:
        return ""

    try:
        if encoding == "base64":
            decoded = base64.b64decode(content)
            # 尝试 UTF-8
            try:
                return decoded.decode("utf-8")[:5000]
            except UnicodeDecodeError:
                # 尝试其他编码
                for enc in ["gbk", "gb2312", "latin-1"]:
                    try:
                        return decoded.decode(enc)[:5000]
                    except UnicodeDecodeError:
                        continue
                return decoded.decode("utf-8", errors="ignore")[:5000]
        else:
            return content[:5000]
    except Exception:
        return ""


def get_star_history_url(repo_name: str) -> str:
    """生成 Star 历史图链接"""
    return f"https://star-history.com/#{repo_name}&Date"


def _get_recent_star_counts(repo_name: str) -> Dict:
    """
    通过 GitHub Events API 精确统计近30天/90天的star增量（v4.3.0）

    Events API 保留最近90天的事件，每页30条，最多10页。
    限制最多读5页（150条事件），避免过多API调用。
    WatchEvent 类型即为 star 事件。

    返回: {"star_30d": int, "star_90d": int, "star_method": str}
    """
    if not _has_github_token():
        return {"star_30d": None, "star_90d": None, "star_method": "no_token"}

    now = datetime.now()
    cutoff_30d = now - timedelta(days=30)
    cutoff_90d = now - timedelta(days=90)

    star_30d = 0
    star_90d = 0
    partial = False

    for page in range(1, 6):  # 最多5页
        data = github_api_request(
            f"/repos/{repo_name}/events",
            {"page": str(page), "per_page": "30"}
        )

        if isinstance(data, dict) and "error" in data:
            # API 出错时返回已收集的数据
            return {
                "star_30d": star_30d if page > 1 else None,
                "star_90d": star_90d if page > 1 else None,
                "star_method": "events_api_partial"
            }

        if not isinstance(data, list) or len(data) == 0:
            break

        page_has_old = False
        for event in data:
            if event.get("type") != "WatchEvent":
                continue
            created_at_str = event.get("created_at", "")
            if not created_at_str:
                continue
            try:
                event_time = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
            if event_time >= cutoff_30d:
                star_30d += 1
            if event_time >= cutoff_90d:
                star_90d += 1
            else:
                page_has_old = True

        # 如果本页有超过90天的事件，或本页不满，说明已覆盖完整90天
        if page_has_old or len(data) < 30:
            break

        # 如果到达第5页仍未覆盖完
        if page == 5:
            partial = True

    method = "events_api" if not partial else "events_api_partial"
    return {"star_30d": star_30d, "star_90d": star_90d, "star_method": method}


def get_repo_languages(repo_name: str) -> Dict[str, int]:
    """
    获取项目的语言组成（语言 → 代码字节数）

    GitHub API 端点: GET /repos/{owner}/{repo}/languages
    返回示例: {"Python": 123456, "JavaScript": 6789, "HTML": 1234}

    用途：
    - 判断项目主语言占比（单语言项目更适合重写学习）
    - 评估项目技术栈复杂度
    - 辅助学习场景的推荐判断
    """
    data = github_api_request(f"/repos/{repo_name}/languages")
    if "error" in data:
        return {}
    return data


# ============ 5. 综合分析 ============

# 项目类型推断的关键词映射
# 注意：匹配按字典顺序执行，resource 需在 tutorial 之前（awesome- 更偏资源集合）
_PROJECT_TYPE_RULES = {
    "resource": {
        "name_patterns": ["awesome-", "list-of-", "curated-", "collection-"],
        "topic_patterns": ["awesome-list", "list", "collection", "curated"],
    },
    "tutorial": {
        "name_patterns": ["learn-", "tutorial-", "interview-", "roadmap-", "study-",
                          "course-", "book-", "guide-", "cheatsheet"],
        "topic_patterns": ["tutorial", "learning", "education", "course",
                           "interview", "study", "roadmap", "book"],
        "readme_patterns": ["学习路线", "面试题", "教程", "课程", "书单"],
    },
    "framework": {
        "name_patterns": ["-framework", "-engine", "-runtime", "-platform", "-core"],
        "topic_patterns": ["framework", "engine", "runtime", "platform", "library"],
        "readme_patterns": ["framework", "engine", "快速开发", "脚手架"],
    },
    "library": {
        "name_patterns": ["-sdk", "-client", "-wrapper", "-driver", "-adapter",
                          "-plugin", "-extension", "-mod", "py-", "go-", "rust-"],
        "topic_patterns": ["sdk", "client", "library", "api-client", "wrapper",
                           "driver", "plugin", "extension"],
        "readme_patterns": ["pip install", "npm install", "cargo add", "go get",
                           "API client", "SDK"],
    },
    "tool": {
        "name_patterns": ["-cli", "-tool", "-util", "-helper", "-converter",
                          "-generator", "-downloader", "-manager", "-checker"],
        "topic_patterns": ["cli", "tool", "utility", "command-line"],
        "readme_patterns": ["command-line", "CLI", "命令行工具"],
    },
}


def _infer_project_type(details: Dict, readme: str, repo_name: str) -> str:
    """
    推断项目类型：tool / library / application / framework / tutorial / resource

    基于客观特征（名称模式、topics、README关键词），不做"成熟度"判断。
    推断优先级：tutorial > resource > framework > library > tool > application（默认）
    """
    name = repo_name.split("/")[-1].lower() if "/" in repo_name else repo_name.lower()
    topics = [t.lower() for t in details.get("tags", [])]
    readme_lower = readme[:2000].lower() if readme else ""

    for ptype, rules in _PROJECT_TYPE_RULES.items():
        # 名称匹配
        for pattern in rules.get("name_patterns", []):
            if pattern in name:
                return ptype
        # topic 匹配
        for pattern in rules.get("topic_patterns", []):
            if pattern in topics:
                return ptype
        # README 关键词匹配
        for pattern in rules.get("readme_patterns", []):
            if pattern.lower() in readme_lower:
                return ptype

    # 兜底：根据语言组成推断
    languages = details.get("languages", {})
    if languages:
        # 如果主语言占比极高(>85%)且只有1-2种语言，倾向 tool
        total = sum(languages.values())
        if total > 0:
            max_lang = max(languages.values())
            ratio = max_lang / total
            if ratio > 0.85 and len(languages) <= 2:
                return "tool"
            # 如果有3种以上语言且有 HTML/CSS，倾向 application
            lang_names = set(languages.keys())
            if len(languages) >= 3 and lang_names & {"HTML", "CSS", "JavaScript", "TypeScript"}:
                return "application"

    # 默认为 application
    return "application"


def _calc_languages_summary(languages: Dict[str, int]) -> Dict[str, str]:
    """
    将语言字节数转换为百分比摘要

    返回示例: {"Python": "92.3%", "JavaScript": "5.1%", "HTML": "2.6%"}
    低于1%的合并为 "Other"
    """
    if not languages:
        return {}

    total = sum(languages.values())
    if total == 0:
        return {}

    result = {}
    other_pct = 0.0
    for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        pct = round(bytes_count / total * 100, 1)
        if pct >= 1.0:
            result[lang] = f"{pct}%"
        else:
            other_pct += pct

    if other_pct > 0:
        result["Other"] = f"{round(other_pct, 1)}%"

    return result


def analyze_project(repo_name: str) -> Dict:
    """综合分析项目：详情 + README + 趋势"""
    details = get_repo_details(repo_name)

    if "error" in details:
        return details

    readme = get_readme_content(repo_name)

    # 分析 README 关键信息
    readme_lower = readme.lower()
    docker_support = "docker" in readme_lower or "docker-compose" in readme_lower
    install_methods = []
    if "pip install" in readme_lower:
        install_methods.append("pip")
    if "npm install" in readme_lower or "yarn add" in readme_lower:
        install_methods.append("npm")
    if "docker" in readme_lower:
        install_methods.append("docker")
    if "cargo install" in readme_lower:
        install_methods.append("cargo")
    if "go install" in readme_lower:
        install_methods.append("go")

    # 计算项目年龄和增速
    if details.get("created_at"):
        created = datetime.strptime(details["created_at"], "%Y-%m-%d")
        age_days = (datetime.now() - created).days
        star_per_day = details["star_count"] / max(age_days, 1)
    else:
        age_days = 0
        star_per_day = 0

    # v4.3.0: 精确统计近30天/90天star增量（Events API）
    recent_stars = _get_recent_star_counts(repo_name)

    # 推断项目类型（基于客观特征，非主观"成熟度"判断）
    project_type = _infer_project_type(details, readme, repo_name)

    # 计算语言组成百分比
    languages_summary = _calc_languages_summary(details.get("languages", {}))

    return {
        **details,
        "readme_preview": readme[:1000] if readme else "",
        "docker_support": docker_support,
        "install_methods": install_methods,
        "project_type": project_type,
        "languages_summary": languages_summary,
        "age_days": age_days,
        "star_per_day": round(star_per_day, 2),
        "star_30d": recent_stars.get("star_30d"),
        "star_90d": recent_stars.get("star_90d"),
        "star_method": recent_stars.get("star_method", "avg_estimate"),
        "star_history_url": get_star_history_url(repo_name),
        "deepwiki_url": f"https://deepwiki.com/{repo_name}",
        "zread_url": f"https://zread.ai/r/{repo_name}",
    }


# ============ 5C. 仓库文档生成（DeepWiki/Zread-inspired） ============

def generate_docs(repo_name: str) -> Dict:
    """
    生成项目快速理解文档：目录结构 + 技术栈 + 模块划分 + Quick Start。
    不克隆仓库，仅通过 GitHub API 获取必要信息（最多 5 次 API 调用）。
    """
    # 1. 获取基本信息
    details = get_repo_details(repo_name)
    if "error" in details:
        return details

    # 2. 获取仓库目录树（浅层，避免大仓库超时）
    tree = _get_repo_tree(repo_name)

    # 3. 获取 README
    readme = get_readme_content(repo_name)

    # 4. 尝试读取关键配置文件以推断技术栈
    tech_stack = _detect_tech_stack(repo_name, tree, primary_language=details.get("language", ""))

    # 5. 分析目录结构，提取模块划分
    modules = _extract_modules(tree)

    # 6. 从 README 提取 Quick Start
    quick_start = _extract_quick_start(readme)

    return {
        "repo_name": repo_name,
        "display_name": details.get("display_name", ""),
        "about": details.get("about", ""),
        "star_count": details.get("star_count", 0),
        "language": details.get("language", ""),
        "license": details.get("license", ""),
        "tech_stack": tech_stack,
        "directory_structure": _format_tree_summary(tree),
        "key_modules": modules,
        "quick_start": quick_start,
        "readme_preview": readme[:800] if readme else "",
        "deepwiki_url": f"https://deepwiki.com/{repo_name}",
        "zread_url": f"https://zread.ai/r/{repo_name}",
    }


def _get_repo_tree(repo_name: str, max_depth: int = 2) -> List[Dict]:
    """获取仓库目录树（通过 Contents API 逐层获取，避免大仓库 recursive tree 超时）"""
    result = []
    dirs_to_scan = [("", 0)]  # (path, depth)

    while dirs_to_scan:
        path, depth = dirs_to_scan.pop(0)
        if depth > max_depth:
            continue
        endpoint = f"/repos/{repo_name}/contents/{path}" if path else f"/repos/{repo_name}/contents"
        data = github_api_request(endpoint)
        if "error" in data or not isinstance(data, list):
            continue
        for item in data:
            name = item.get("name", "")
            item_type = item.get("type", "")  # file or dir
            full_path = f"{path}/{name}" if path else name
            result.append({
                "path": full_path,
                "type": "blob" if item_type == "file" else "tree",
            })
            if item_type == "dir" and depth < max_depth:
                # 跳过不需要递归的目录
                if name not in {".git", "node_modules", "vendor", "__pycache__", ".github"}:
                    dirs_to_scan.append((full_path, depth + 1))
        # 限制总量
        if len(result) > 500:
            break
    return result


def _detect_tech_stack(repo_name: str, tree: List[Dict], primary_language: str = "") -> Dict:
    """从目录树和配置文件推断技术栈"""
    paths = [item["path"] for item in tree]
    filenames = set(os.path.basename(p) for p in paths)

    # 主语言优先使用 GitHub API 返回的 language 字段
    lang = primary_language or ""
    pkg_manager = ""
    build_tool = ""

    # 从配置文件补充包管理器
    if "package.json" in filenames:
        if not lang:
            lang = "JavaScript/TypeScript"
        pkg_manager = "npm/yarn"
        if "tsconfig.json" in filenames and "TypeScript" not in lang:
            lang = "TypeScript"
    if "Cargo.toml" in filenames:
        if not lang:
            lang = "Rust"
        if not pkg_manager:
            pkg_manager = "cargo"
    if "go.mod" in filenames:
        if not lang:
            lang = "Go"
        if not pkg_manager:
            pkg_manager = "go modules"
    if "pyproject.toml" in filenames or "setup.py" in filenames or "requirements.txt" in filenames:
        if not lang:
            lang = "Python"
        if not pkg_manager:
            pkg_manager = "pip"
    if "Gemfile" in filenames:
        if not lang:
            lang = "Ruby"
        if not pkg_manager:
            pkg_manager = "bundler"
    if "pom.xml" in filenames:
        if not lang:
            lang = "Java"
        build_tool = "Maven"
    if "build.gradle" in filenames or "build.gradle.kts" in filenames:
        if not lang:
            lang = "Java/Kotlin"
        build_tool = "Gradle"

    # 检测框架（从目录名推断）
    dir_names = set(os.path.dirname(p) for p in paths if p)
    framework = ""
    if "src" in dir_names or "app" in dir_names:
        for p in paths:
            if "next" in p.lower() and ("config" in p.lower() or "app" in p.lower()):
                framework = "Next.js"
                break
            if "nuxt" in p.lower():
                framework = "Nuxt.js"
                break

    # 检测 CI/CD
    ci_cd = []
    ci_files = [p for p in paths if ".github/workflows/" in p or ".gitlab-ci.yml" in p or "Jenkinsfile" in p]
    if ci_files:
        for f in ci_files:
            if "github" in f:
                ci_cd.append("GitHub Actions")
            elif "gitlab" in f:
                ci_cd.append("GitLab CI")
            elif "Jenkins" in f:
                ci_cd.append("Jenkins")

    # 检测 Docker
    if "Dockerfile" in filenames or "docker-compose.yml" in filenames or "docker-compose.yaml" in filenames:
        build_tool = (build_tool + " Docker").strip()

    return {
        "language": lang,
        "framework": framework,
        "package_manager": pkg_manager,
        "build_tool": build_tool,
        "ci_cd": list(set(ci_cd)),
    }


def _extract_modules(tree: List[Dict]) -> List[str]:
    """从目录树提取关键模块（顶层目录）"""
    top_dirs = set()
    for item in tree:
        path = item["path"]
        if item["type"] == "tree" and "/" not in path:
            top_dirs.add(path)
    # 过滤常见的非模块目录
    skip = {".github", ".git", "docs", "test", "tests", "scripts", "examples", "assets", ".vscode", "node_modules"}
    modules = [d for d in sorted(top_dirs) if d not in skip and not d.startswith(".")]
    return modules


def _extract_quick_start(readme: str) -> str:
    """从 README 中提取 Quick Start / Installation / Getting Started 段落"""
    if not readme:
        return ""
    lower = readme.lower()
    # 查找常见段落标题
    patterns = ["quick start", "getting started", "installation", "install", "usage", "快速开始", "安装", "使用方法"]
    for pat in patterns:
        idx = lower.find(pat)
        if idx != -1:
            # 提取该段落（到下一个 ## 或 500 字符）
            end = readme.find("\n## ", idx + 1)
            if end == -1:
                end = min(idx + 800, len(readme))
            section = readme[idx:end].strip()
            if len(section) > 600:
                section = section[:600] + "..."
            return section
    return ""


def _format_tree_summary(tree: List[Dict]) -> Dict:
    """生成目录结构摘要统计"""
    total_files = sum(1 for item in tree if item["type"] == "blob")
    total_dirs = sum(1 for item in tree if item["type"] == "tree")
    # 按扩展名统计
    ext_count = {}
    for item in tree:
        if item["type"] == "blob":
            ext = os.path.splitext(item["path"])[1].lower()
            if ext:
                ext_count[ext] = ext_count.get(ext, 0) + 1
    # 取 top 10 扩展名
    top_exts = sorted(ext_count.items(), key=lambda x: -x[1])[:10]
    return {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "top_file_types": [{"ext": ext, "count": cnt} for ext, cnt in top_exts],
    }


# ============ 5B. 信任评估（Starguard-inspired） ============

# 许可证风险分级
_LICENSE_RISK = {
    # 安全（宽松许可）
    "mit": ("safe", "MIT — 最宽松的开源许可，商用无限制"),
    "mit license": ("safe", "MIT — 最宽松的开源许可，商用无限制"),
    "apache-2.0": ("safe", "Apache 2.0 — 宽松许可，含专利保护条款"),
    "apache license 2.0": ("safe", "Apache 2.0 — 宽松许可，含专利保护条款"),
    "apache-2.0 license": ("safe", "Apache 2.0 — 宽松许可，含专利保护条款"),
    "bsd-2-clause": ("safe", "BSD 2-Clause — 极简许可"),
    "bsd-3-clause": ("safe", "BSD 3-Clause — 极简许可"),
    "bsd": ("safe", "BSD — 宽松许可"),
    "isc": ("safe", "ISC — 极简许可"),
    "isc license": ("safe", "ISC — 极简许可"),
    "unlicense": ("safe", "Unlicense — 无限制，等同于公有领域"),
    "the unlicense": ("safe", "Unlicense — 无限制，等同于公有领域"),
    "0bsd": ("safe", "0BSD — 无限制"),
    "bsd zero clause license": ("safe", "0BSD — 无限制"),
    "cc0-1.0": ("safe", "CC0 1.0 — 公有领域"),
    "creative commons zero": ("safe", "CC0 1.0 — 公有领域"),
    "wtfpl": ("safe", "WTFPL — 无限制"),
    "do what the f*ck": ("safe", "WTFPL — 无限制"),
    "mozilla public license 2.0": ("moderate", "MPL 2.0 — 文件级 copyleft，修改同文件需开源"),
    # 中等风险（弱 copyleft）
    "lgpl-2.1": ("moderate", "LGPL 2.1 — 弱 copyleft，链接使用需遵守部分条件"),
    "lgpl-3.0": ("moderate", "LGPL 3.0 — 弱 copyleft，链接使用需遵守部分条件"),
    "mpl-2.0": ("moderate", "MPL 2.0 — 文件级 copyleft，修改同文件需开源"),
    "epl-2.0": ("moderate", "EPL 2.0 — 弱 copyleft，修改需开源"),
    "eupl-1.2": ("moderate", "EUPL 1.2 — 欧盟公共许可"),
    # 高风险（强 copyleft）
    "gpl-2.0": ("high", "GPL 2.0 — 强 copyleft，衍生作品必须开源"),
    "gpl-3.0": ("high", "GPL 3.0 — 强 copyleft，衍生作品必须开源"),
    "agpl-3.0": ("high", "AGPL 3.0 — 网络 copyleft，SaaS 使用也需开源"),
    "gnu affero general public license": ("high", "AGPL 3.0 — 网络 copyleft，SaaS 使用也需开源"),
    "gnu general public license": ("high", "GPL — 强 copyleft，衍生作品必须开源"),
}

def _classify_license(license_name: str) -> Dict:
    """许可证风险分级"""
    if not license_name or license_name == "":
        return {"risk_level": "unknown", "score": 30, "assessment": "未声明许可证 — 使用存在法律风险，需联系作者确认"}
    
    lower = license_name.lower().strip()
    for key, (risk, desc) in _LICENSE_RISK.items():
        if key in lower:
            score_map = {"safe": 95, "moderate": 65, "high": 35}
            return {"risk_level": risk, "score": score_map[risk], "assessment": desc}
    
    return {"risk_level": "unknown", "score": 50, "assessment": f"未知许可证类型: {license_name}，建议确认是否可商用"}


def _check_star_quality(details: Dict) -> Dict:
    """
    Star 质量检查：检测异常星数/叉比
    正常范围：star/fork ≈ 3-15
    可疑范围：star/fork > 30（可能有刷星）
    高度可疑：star/fork > 100
    """
    stars = details.get("star_count", 0)
    forks = details.get("forks_count", 0)
    age_days = details.get("age_days", 0)
    star_per_day = details.get("star_per_day", 0)
    
    if forks == 0:
        ratio = stars if stars > 0 else 0
        risk = "high" if stars > 100 else "moderate"
        score = 20 if risk == "high" else 50
        return {
            "score": score,
            "star_fork_ratio": f"{ratio:.0f}:1",
            "risk": risk,
            "assessment": f"fork 数为 0 但 star 数 {stars}，比例异常，可能存在刷星活动"
        }
    
    ratio = stars / forks
    if ratio > 100:
        return {"score": 15, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "high",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 极度异常，强烈怀疑存在假星"}
    elif ratio > 50:
        return {"score": 35, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "high",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 偏高，可能存在部分刷星"}
    elif ratio > 30:
        return {"score": 55, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "moderate",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 略高，建议关注"}
    elif ratio > 15:
        return {"score": 70, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "low",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 正常偏高"}
    elif ratio >= 3:
        return {"score": 95, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "low",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 健康"}
    else:
        return {"score": 80, "star_fork_ratio": f"{ratio:.1f}:1", "risk": "low",
                "assessment": f"star/fork 比例 {ratio:.1f}:1 偏低但正常（fork 活跃度高）"}


def _get_maintainer_health(repo_name: str) -> Dict:
    """获取维护者健康度：贡献者数量 + 最近提交时间"""
    # 获取贡献者（前5个，检查是否集中）
    contributors_data = github_api_request(f"/repos/{repo_name}/contributors", {"per_page": "5", "anon": "false"})
    contributor_count = 0
    top5_pct = 0
    if isinstance(contributors_data, list) and len(contributors_data) > 0:
        contributor_count = len(contributors_data)
        total_contribs = sum(c.get("contributions", 0) for c in contributors_data)
        if total_contribs > 0:
            top1 = contributors_data[0].get("contributions", 0)
            top5_pct = round(top1 / total_contribs * 100, 1)
    elif isinstance(contributors_data, dict) and "error" in contributors_data:
        return {"score": 50, "contributors": 0, "last_commit_days_ago": None,
                "assessment": "无法获取贡献者数据", "error": contributors_data.get("error")}
    
    # 获取最近提交
    commits_data = github_api_request(f"/repos/{repo_name}/commits", {"per_page": "3"})
    last_commit_days_ago = None
    if isinstance(commits_data, list) and len(commits_data) > 0:
        last_commit_date = commits_data[0].get("commit", {}).get("committer", {}).get("date", "")
        if last_commit_date:
            try:
                commit_dt = datetime.strptime(last_commit_date, "%Y-%m-%dT%H:%M:%SZ")
                last_commit_days_ago = (datetime.now() - commit_dt).days
            except ValueError:
                pass
    
    # 评分逻辑
    score = 50
    # 贡献者数量
    if contributor_count >= 10:
        score += 25
    elif contributor_count >= 5:
        score += 15
    elif contributor_count >= 2:
        score += 5
    else:
        score -= 15
    
    # 最近提交时间
    if last_commit_days_ago is not None:
        if last_commit_days_ago <= 7:
            score += 25
        elif last_commit_days_ago <= 30:
            score += 15
        elif last_commit_days_ago <= 90:
            score += 5
        elif last_commit_days_ago <= 180:
            score -= 10
        else:
            score -= 25
    
    # 贡献者集中度（前1人占>80%是风险）
    if top5_pct > 80 and contributor_count > 1:
        score -= 10
    
    score = max(0, min(100, score))
    
    # 生成评估文案
    if contributor_count == 0 and last_commit_days_ago is None:
        assessment = "无法获取维护者数据"
    elif contributor_count <= 1:
        assessment = "单人维护，存在 bus factor=1 风险"
    elif last_commit_days_ago is not None and last_commit_days_ago > 180:
        assessment = f"已有 {contributor_count} 位贡献者，但最后提交在 {last_commit_days_ago} 天前，项目可能已停止维护"
    elif last_commit_days_ago is not None and last_commit_days_ago > 90:
        assessment = f"最后提交在 {last_commit_days_ago} 天前，维护频率偏低"
    elif last_commit_days_ago is not None and last_commit_days_ago <= 30:
        assessment = f"活跃维护中（{contributor_count} 位贡献者，最后提交 {last_commit_days_ago} 天前）"
    else:
        assessment = f"基本活跃（{contributor_count} 位贡献者，最后提交 {last_commit_days_ago} 天前）"
    
    return {
        "score": score,
        "contributors": contributor_count,
        "last_commit_days_ago": last_commit_days_ago,
        "top_contributor_pct": top5_pct,
        "assessment": assessment
    }


def _check_dependency_safety(repo_name: str, details: Dict) -> Dict:
    """检查依赖安全：manifest 文件存在性 + lockfile（支持 monorepo 子目录扫描）"""
    root_contents = github_api_request(f"/repos/{repo_name}/contents/")
    
    if "error" in root_contents:
        return {"score": 50, "assessment": "无法获取仓库文件列表", "manifests": [], "has_lockfile": None}
    
    if not isinstance(root_contents, list):
        return {"score": 50, "assessment": "仓库结构异常", "manifests": [], "has_lockfile": None}
    
    # 收集根目录文件和子目录
    file_names = {f.get("name", "") for f in root_contents if f.get("type") == "file"}
    dir_names = [f.get("name", "") for f in root_contents if f.get("type") == "dir"]
    
    # Manifest 和 lockfile 定义
    manifest_files = {
        "package.json": "npm/yarn",
        "requirements.txt": "pip",
        "pyproject.toml": "pip/modern",
        "setup.py": "pip/legacy",
        "setup.cfg": "pip/legacy",
        "go.mod": "go",
        "Cargo.toml": "rust",
        "pom.xml": "maven/java",
        "build.gradle": "gradle/java",
        "Gemfile": "ruby",
        "composer.json": "php",
    }
    lockfiles = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
                 "Pipfile.lock", "go.sum", "Cargo.lock", "Gemfile.lock", "composer.lock"}
    
    found_manifests = []
    has_lockfile = False
    checked_paths = []
    
    # 检查根目录
    for manifest, eco in manifest_files.items():
        if manifest in file_names:
            found_manifests.append({"file": manifest, "ecosystem": eco, "path": manifest})
    has_lockfile = bool(file_names & lockfiles)
    
    # 如果根目录没有 manifest，递归扫描子目录（monorepo 支持）
    if not found_manifests:
        common_subdirs = [d for d in dir_names if d in {"src", "packages", "lib", "app", "modules", "services", "libs"}]
        other_dirs = [d for d in dir_names if d not in common_subdirs and not d.startswith(".")][:5]
        dirs_to_check = common_subdirs + other_dirs
        
        api_calls = 0
        max_api_calls = 8  # 限制总 API 调用次数
        
        def _scan_dir(path_prefix: str, depth: int = 0):
            nonlocal api_calls, has_lockfile
            if api_calls >= max_api_calls or len(found_manifests) >= 3 or depth > 1:
                return
            sub_contents = github_api_request(f"/repos/{repo_name}/contents/{path_prefix}")
            api_calls += 1
            if not isinstance(sub_contents, list):
                return
            sub_files = {f.get("name", "") for f in sub_contents if f.get("type") == "file"}
            sub_dirs = [f.get("name", "") for f in sub_contents if f.get("type") == "dir"]
            # 检查 manifest 和 lockfile
            for manifest, eco in manifest_files.items():
                if manifest in sub_files:
                    found_manifests.append({"file": manifest, "ecosystem": eco, "path": f"{path_prefix}/{manifest}"})
            if sub_files & lockfiles:
                has_lockfile = True
            # 递归进入子目录（monorepo 常见如 packages/xxx/pyproject.toml）
            if not found_manifests and depth < 1:
                # 优先检查常见代码目录名
                priority = [d for d in sub_dirs if d in {"src", "lib", "app", "core", "main"}]
                rest = [d for d in sub_dirs if d not in priority and not d.startswith(".")][:3]
                for d in priority + rest:
                    if len(found_manifests) >= 3 or api_calls >= max_api_calls:
                        break
                    _scan_dir(f"{path_prefix}/{d}", depth + 1)
        
        for subdir in dirs_to_check:
            if len(found_manifests) >= 3 or api_calls >= max_api_calls:
                break
            _scan_dir(subdir)
    
    # 检查可疑文件
    suspicious_files = []
    if ".env" in file_names or ".env.local" in file_names:
        suspicious_files.append(".env 文件暴露在仓库根目录")
    
    # 评分
    score = 70  # 基础分
    if found_manifests:
        score += 10
    if has_lockfile:
        score += 15
    if not found_manifests:
        score -= 10
    if suspicious_files:
        score -= 20
    
    score = max(0, min(100, score))
    
    parts = []
    if found_manifests:
        paths_str = ", ".join(m["path"] for m in found_manifests)
        parts.append(f"检测到 {len(found_manifests)} 个 manifest ({paths_str})")
    if has_lockfile:
        parts.append("有 lockfile（依赖锁定，更安全）")
    elif found_manifests:
        parts.append("无 lockfile（依赖版本可能浮动）")
    if suspicious_files:
        parts.append(f"⚠️ {', '.join(suspicious_files)}")
    if not found_manifests and not suspicious_files:
        parts.append("未发现标准包管理文件（可能是非代码仓库或 monorepo 结构）")
    
    assessment = "；".join(parts)
    
    return {
        "score": score,
        "manifests": found_manifests,
        "has_lockfile": has_lockfile,
        "suspicious_files": suspicious_files,
        "assessment": assessment
    }


def trust_assessment(repo_name: str) -> Dict:
    """
    综合信任评估（受 Starguard 启发）
    
    返回一个 0-100 的 trust_score 和分项评估，帮助用户快速判断项目风险。
    """
    # 获取基本信息
    details = get_repo_details(repo_name)
    if "error" in details:
        return details
    
    # 补充 age_days（用于 star 质量检查）
    if details.get("created_at"):
        created = datetime.strptime(details["created_at"], "%Y-%m-%d")
        details["age_days"] = (datetime.now() - created).days
        details["star_per_day"] = details["star_count"] / max(details["age_days"], 1)
    else:
        details["age_days"] = 0
        details["star_per_day"] = 0
    
    # 各维度检查
    license_check = _classify_license(details.get("license", ""))
    star_quality = _check_star_quality(details)
    maintainer_health = _get_maintainer_health(repo_name)
    dep_safety = _check_dependency_safety(repo_name, details)
    
    # 综合评分（加权平均）
    weights = {
        "license": 0.25,
        "star_quality": 0.20,
        "maintainer_health": 0.30,
        "dependency_safety": 0.25,
    }
    
    trust_score = round(
        license_check["score"] * weights["license"] +
        star_quality["score"] * weights["star_quality"] +
        maintainer_health["score"] * weights["maintainer_health"] +
        dep_safety["score"] * weights["dependency_safety"]
    )
    
    # 信任等级
    if trust_score >= 80:
        trust_badge = "✅ reliable"
    elif trust_score >= 60:
        trust_badge = "🟡 generally safe"
    elif trust_score >= 40:
        trust_badge = "🟠 caution"
    else:
        trust_badge = "🔴 risky"
    
    # 汇总警告和亮点
    warnings = []
    highlights = []
    
    if license_check["risk_level"] == "high":
        warnings.append(f"许可证风险高: {license_check['assessment']}")
    elif license_check["risk_level"] == "unknown":
        warnings.append(f"许可证未知: {license_check['assessment']}")
    elif license_check["risk_level"] == "safe":
        highlights.append(f"许可证安全: {license_check['assessment']}")
    
    if star_quality["risk"] == "high":
        warnings.append(f"Star 质量异常: {star_quality['assessment']}")
    elif star_quality["score"] >= 85:
        highlights.append(f"Star 数据健康: {star_quality['assessment']}")
    
    if maintainer_health["score"] < 40:
        warnings.append(f"维护者健康度低: {maintainer_health['assessment']}")
    elif maintainer_health["score"] >= 75:
        highlights.append(f"维护活跃: {maintainer_health['assessment']}")
    
    if dep_safety.get("suspicious_files"):
        warnings.append(f"依赖安全: {dep_safety['assessment']}")
    elif dep_safety.get("has_lockfile"):
        highlights.append(f"依赖管理规范: {dep_safety['assessment']}")
    
    return {
        "repo_name": repo_name,
        "trust_score": trust_score,
        "trust_badge": trust_badge,
        "checks": {
            "license": license_check,
            "star_quality": star_quality,
            "maintainer_health": maintainer_health,
            "dependency_safety": dep_safety,
        },
        "warnings": warnings,
        "highlights": highlights,
    }


# ============ 6. HelloGitHub 社区精选 ============

HELLOGITHUB_REPO = "521xueweihan/HelloGitHub"
HELLOGITHUB_CONTENT_PATH = "content"

# 语言分类映射（HelloGitHub 月刊中的标题 → 编程语言）
HG_LANGUAGE_MAP = {
    "C 项目": "C",
    "C# 项目": "C#",
    "C++ 项目": "C++",
    "Go 项目": "Go",
    "Java 项目": "Java",
    "JavaScript 项目": "JavaScript",
    "Python 项目": "Python",
    "Rust 项目": "Rust",
    "Swift 项目": "Swift",
    "Ruby 项目": "Ruby",
    "TypeScript 项目": "TypeScript",
    "Kotlin 项目": "Kotlin",
    "Dart 项目": "Dart",
    "Objective-C 项目": "Objective-C",
    "Lua 项目": "Lua",
    "Shell 项目": "Shell",
}


def _fetch_hg_issue(issue_num: int) -> str:
    """获取 HelloGitHub 指定期号的 markdown 内容"""
    path = f"{HELLOGITHUB_CONTENT_PATH}/HelloGitHub{issue_num}.md"
    data = github_api_request(f"/repos/{HELLOGITHUB_REPO}/contents/{path}")
    if "error" in data:
        return ""
    content = data.get("content", "")
    if not content:
        return ""
    try:
        return base64.b64decode(content).decode("utf-8")
    except Exception:
        return ""


def _parse_hg_projects(markdown: str) -> List[Dict]:
    """
    解析 HelloGitHub 月刊 markdown，提取项目条目
    
    格式示例：
    1、[ds4](https://hellogithub.com/periodical/statistics/click?target=https://github.com/antirez/ds4)：Redis 作者写的 DeepSeek 专用推理引擎。...
    """
    import re
    projects = []
    current_language = ""

    for line in markdown.split("\n"):
        # 检测语言分类标题（如 "### C 项目"）
        lang_match = re.match(r"^###\s+(.+?项目)", line.strip())
        if lang_match:
            current_language = HG_LANGUAGE_MAP.get(lang_match.group(1), "")
            continue

        # 检测项目条目：数字、[名称](链接)：描述
        proj_match = re.match(
            r'^\d+、\[(.+?)\]\((.+?)\)[：:](.+)',
            line.strip()
        )
        if proj_match:
            name = proj_match.group(1)
            link = proj_match.group(2)
            description = proj_match.group(3).strip()

            # 从链接中提取 GitHub 仓库
            repo_name = ""
            # 链接可能是 hellogithub 的跳转链接：target=https://github.com/owner/repo
            # 或直接的 GitHub 链接
            target_match = re.search(r'target=(https://github\.com/[^&\s]+)', link)
            if target_match:
                gh_url = target_match.group(1)
                gh_match = re.search(r'github\.com/([^/\s]+/[^/\s]+)', gh_url)
                if gh_match:
                    repo_name = gh_match.group(1)
            if not repo_name:
                gh_match = re.search(r'github\.com/([^/\s]+/[^/\s\)?]+)', link)
                if gh_match:
                    repo_name = gh_match.group(1).rstrip(")")

            # 清理描述中的 HTML 标签
            description = re.sub(r'<[^>]+>', '', description).strip()
            # 截断过长描述
            if len(description) > 200:
                description = description[:200] + "..."

            project = {
                "repo_name": repo_name,
                "display_name": name,
                "about": description,
                "tags": [],
                "language": current_language,
                "scene": f"HelloGitHub 推荐",
                "verified": False,
                "_source": "hellogithub",
                "html_url": f"https://github.com/{repo_name}" if repo_name else link,
            }
            projects.append(project)

    return projects


def search_hellogithub(query: str, issues: int = 10, language: str = None) -> Dict:
    """
    搜索 HelloGitHub 社区精选项目
    
    从最近 N 期月刊中解析项目，按关键词匹配
    
    参数：
        query: 搜索关键词
        issues: 搜索最近几期（默认10期，v3.4.0从5提升至10；最多20期）
        language: 编程语言过滤
    """
    results = {
        "query": query,
        "source": "hellogithub",
        "issues_searched": 0,
        "projects": []
    }

    # 获取最新期号：通过 GitHub API 获取 content 目录列表
    dir_data = github_api_request(f"/repos/{HELLOGITHUB_REPO}/contents/{HELLOGITHUB_CONTENT_PATH}")
    if "error" in dir_data:
        results["error"] = "无法获取 HelloGitHub 月刊目录"
        return results

    # 提取期号列表
    issue_nums = []
    for item in dir_data:
        name = item.get("name", "")
        match = re.match(r"HelloGitHub(\d+)\.md$", name)
        if match:
            issue_nums.append(int(match.group(1)))

    if not issue_nums:
        results["error"] = "未找到 HelloGitHub 月刊"
        return results

    # 取最近 N 期
    issue_nums.sort(reverse=True)
    latest_issues = issue_nums[:issues]
    results["issues_searched"] = len(latest_issues)

    # 解析并搜索
    query_lower = query.lower()
    all_projects = []

    for issue_num in latest_issues:
        markdown = _fetch_hg_issue(issue_num)
        if not markdown:
            continue
        projects = _parse_hg_projects(markdown)
        for proj in projects:
            # 关键词匹配
            score = 0
            if query_lower in proj.get("display_name", "").lower():
                score += 10
            if query_lower in proj.get("about", "").lower():
                score += 5
            if query_lower in proj.get("language", "").lower():
                score += 3
            # 额外中文关键词映射匹配
            for cn, en in KEYWORD_MAP.items():
                if cn in query_lower and en in proj.get("about", "").lower():
                    score += 3
                if en in query_lower and cn in proj.get("about", "").lower():
                    score += 3

            if score > 0:
                proj["_match_score"] = score
                proj["_issue"] = issue_num
                all_projects.append(proj)

    # 语言过滤
    if language:
        lang_lower = language.lower()
        all_projects = [p for p in all_projects if lang_lower in p.get("language", "").lower()]

    # 排序
    all_projects.sort(key=lambda x: x.get("_match_score", 0), reverse=True)

    results["projects"] = all_projects[:15]
    return results


# ============ 7. Awesome 列表搜索 ============

def search_awesome(query: str, language: str = None) -> Dict:
    """
    搜索 Awesome 列表：按领域发现优质精选清单
    
    策略：
    1. 搜索名为 awesome-{topic} 的仓库
    2. 搜索带 topic:awesome-list 标签的仓库
    3. 在 sindresorhus/awesome 的索引中搜索
    
    参数：
        query: 领域/技术关键词（如 python, react, machine-learning）
        language: 编程语言过滤（可选）
    """
    results = {
        "query": query,
        "source": "awesome",
        "lists": []
    }

    # 策略1: 搜索 awesome-{query} 名称的仓库
    search_q1 = f'awesome {query} in:name,description topic:awesome-list'
    if language:
        search_q1 += f' language:{language}'
    
    params1 = {"q": search_q1, "sort": "stars", "order": "desc", "per_page": 15}
    data1 = github_api_request("/search/repositories", params1)

    seen_repos = set()
    awesome_lists = []

    if "items" in data1:
        for item in data1["items"]:
            key = item["full_name"]
            if key not in seen_repos:
                seen_repos.add(key)
                awesome_lists.append({
                    "repo_name": key,
                    "display_name": item["name"],
                    "about": item.get("description", ""),
                    "star_count": item["stargazers_count"],
                    "language": item.get("language", ""),
                    "tags": item.get("topics", []),
                    "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
                    "html_url": item["html_url"],
                    "_source": "awesome_search",
                })

    # 策略2: 搜索名称包含 awesome 且描述匹配 query 的仓库（放宽条件）
    search_q2 = f'awesome {query} in:name,description stars:>100 archived:false'
    if language:
        search_q2 += f' language:{language}'

    params2 = {"q": search_q2, "sort": "stars", "order": "desc", "per_page": 15}
    data2 = github_api_request("/search/repositories", params2)

    if "items" in data2:
        for item in data2["items"]:
            key = item["full_name"]
            if key not in seen_repos:
                seen_repos.add(key)
                awesome_lists.append({
                    "repo_name": key,
                    "display_name": item["name"],
                    "about": item.get("description", ""),
                    "star_count": item["stargazers_count"],
                    "language": item.get("language", ""),
                    "tags": item.get("topics", []),
                    "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
                    "html_url": item["html_url"],
                    "_source": "awesome_search",
                })

    # 按星数排序
    awesome_lists.sort(key=lambda x: x.get("star_count", 0), reverse=True)

    results["lists"] = awesome_lists[:20]
    return results


# ============ 8. 阮一峰周刊搜索 ============

RUANYF_WEEKLY_REPO = "ruanyf/weekly"
RUANYF_WEEKLY_CONTENT_PATH = "docs"


def _fetch_ruanyf_issue(issue_num: int) -> str:
    """获取阮一峰周刊指定期号的 markdown 内容"""
    path = f"{RUANYF_WEEKLY_CONTENT_PATH}/issue-{issue_num}.md"
    data = github_api_request(f"/repos/{RUANYF_WEEKLY_REPO}/contents/{path}")
    if "error" in data:
        return ""
    content = data.get("content", "")
    if not content:
        return ""
    try:
        return base64.b64decode(content).decode("utf-8")
    except Exception:
        return ""


def _parse_ruanyf_projects(markdown: str) -> List[Dict]:
    """
    解析阮一峰周刊 markdown，提取「工具」和「AI 相关」板块的项目条目

    周刊格式示例：
    ## 工具
    1、[Gander](https://github.com/mokshablr/gander)
    开源的安卓应用，用来查看各种文件的内容，体积约 15MB，完全离线使用。
    2、[StatLite](https://github.com/PVRLabs/statlite)
    一个开源的 Spring Boot 应用的服务器仪表板，适合个人架设。

    ## AI 相关
    1、[Codex Security](https://github.com/openai/codex-security)
    OpenAI 官方推出的命令行工具，用来扫描代码漏洞，基于 Codex。
    """
    projects = []
    current_section = ""
    current_name = None
    current_url = None
    current_desc_lines = []

    # 仅解析包含 GitHub 项目推荐的板块
    TARGET_SECTIONS = {"工具", "AI 相关"}

    for line in markdown.split("\n"):
        # 检测二级标题（板块名）
        section_match = re.match(r"^##\s+(.+?)$", line.strip())
        if section_match:
            # 保存上一个项目
            if current_name and current_url:
                projects.append(_build_ruanyf_project(
                    current_name, current_url,
                    " ".join(current_desc_lines), current_section
                ))
            current_section = section_match.group(1).strip()
            current_name = None
            current_url = None
            current_desc_lines = []
            continue

        # 仅在目标板块内解析
        if current_section not in TARGET_SECTIONS:
            continue

        # 检测项目条目：数字、[名称](链接) 后面可能有描述
        proj_match = re.match(r'^\d+、\[(.+?)\]\((.+?)\)\s*(.*)', line.strip())
        if proj_match:
            # 保存上一个项目
            if current_name and current_url:
                projects.append(_build_ruanyf_project(
                    current_name, current_url,
                    " ".join(current_desc_lines), current_section
                ))
            current_name = proj_match.group(1)
            current_url = proj_match.group(2)
            current_desc_lines = [proj_match.group(3)] if proj_match.group(3) else []
            continue

        # 收集描述行（跳过图片行和空行）
        if current_name and current_url:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith("!["):
                current_desc_lines.append(line_stripped)

    # 保存最后一个项目
    if current_name and current_url:
        projects.append(_build_ruanyf_project(
            current_name, current_url,
            " ".join(current_desc_lines), current_section
        ))

    return projects


def _build_ruanyf_project(name: str, url: str, desc: str, section: str) -> Dict:
    """构建阮一峰周刊项目字典"""
    # 从链接中提取 GitHub 仓库
    repo_name = ""
    gh_match = re.search(r'github\.com/([^/\s]+/[^/\s\)?]+)', url)
    if gh_match:
        repo_name = gh_match.group(1).rstrip(")")

    # 清理描述
    desc = re.sub(r'<[^>]+>', '', desc).strip()
    if len(desc) > 200:
        desc = desc[:200] + "..."

    return {
        "repo_name": repo_name,
        "display_name": name,
        "about": desc,
        "tags": [],
        "language": "",
        "scene": f"阮一峰周刊·{section}",
        "verified": False,
        "_source": "ruanyf_weekly",
        "html_url": f"https://github.com/{repo_name}" if repo_name else url,
    }


def search_ruanyf(query: str, issues: int = 10, language: str = None) -> Dict:
    """
    搜索阮一峰科技爱好者周刊中的项目推荐

    从最近 N 期周刊中解析「工具」和「AI 相关」板块，按关键词匹配。
    阮一峰周刊每周五发布，推荐的项目通常星数不高但质量不错。

    参数：
        query: 搜索关键词
        issues: 搜索最近几期（默认10期，最多20期）
        language: 编程语言过滤（周刊不标注语言，此参数仅做描述文本匹配）
    """
    results = {
        "query": query,
        "source": "ruanyf_weekly",
        "issues_searched": 0,
        "projects": []
    }

    # 获取最新期号：通过 GitHub API 获取 docs 目录列表
    dir_data = github_api_request(f"/repos/{RUANYF_WEEKLY_REPO}/contents/{RUANYF_WEEKLY_CONTENT_PATH}")
    if "error" in dir_data:
        results["error"] = f"无法获取阮一峰周刊目录: {dir_data.get('error')}"
        return results

    # 提取期号列表
    issue_nums = []
    for item in dir_data:
        name = item.get("name", "")
        match = re.match(r"issue-(\d+)\.md$", name)
        if match:
            issue_nums.append(int(match.group(1)))

    if not issue_nums:
        results["error"] = "未找到阮一峰周刊"
        return results

    # 取最近 N 期
    issue_nums.sort(reverse=True)
    latest_issues = issue_nums[:issues]
    results["issues_searched"] = len(latest_issues)

    # 解析并搜索
    query_lower = query.lower()
    all_projects = []

    for issue_num in latest_issues:
        markdown = _fetch_ruanyf_issue(issue_num)
        if not markdown:
            continue
        projects = _parse_ruanyf_projects(markdown)
        for proj in projects:
            # 只保留有 GitHub repo 的项目
            if not proj.get("repo_name"):
                continue

            # 关键词匹配
            score = 0
            if query_lower in proj.get("display_name", "").lower():
                score += 10
            if query_lower in proj.get("about", "").lower():
                score += 5
            # 额外中文关键词映射匹配
            for cn, en in KEYWORD_MAP.items():
                if cn in query_lower and en in proj.get("about", "").lower():
                    score += 3
                if en in query_lower and cn in proj.get("about", "").lower():
                    score += 3

            if score > 0:
                proj["_match_score"] = score
                proj["_issue"] = issue_num
                all_projects.append(proj)

    # 语言过滤（周刊不标注语言，仅在描述中匹配）
    if language:
        lang_lower = language.lower()
        all_projects = [p for p in all_projects if lang_lower in p.get("about", "").lower()]

    # 排序
    all_projects.sort(key=lambda x: x.get("_match_score", 0), reverse=True)

    results["projects"] = all_projects[:15]
    return results


# ============ 9. 智能体技能/工具搜索 ============

# Awesome Agent Skills 仓库（跨平台技能目录）
AGENT_SKILLS_REPO = "philipbankier/awesome-agent-skills"

# Awesome AI Agents 仓库（AI agent 项目/框架列表）
AI_AGENTS_REPO = "e2b-dev/awesome-ai-agents"

# GitHub Topics 用于搜索 agent 相关项目
AGENT_GITHUB_TOPICS = [
    "coze-skill", "ai-plugins", "ai-agent",
    "agent-framework", "llm-agent", "mcp-server",
]

# awesome-agent-skills section → (is_skill, agent_integration, standalone)
_SKILL_SECTION_MAP = {
    "agent skills": (True, "SKILL.md", False),
    "mcp servers": (False, "MCP", True),
    "cursor rules": (True, "cursor-rules", False),
    "windsurf rules": (True, "windsurf-rules", False),
    "gemini cli": (True, "gemini-extension", False),
    "copilot": (True, "copilot-extension", False),
    "openclaw": (True, "openclaw-skill", False),
    "langchain": (False, "langchain-tool", True),
    "crewai": (False, "crewai-tool", True),
    "n8n": (False, "n8n-node", True),
    "multi-platform": (False, "multi-platform", True),
    "clis": (False, "cli", True),
}

# GitHub topic → (is_skill, agent_integration, standalone)
_TOPIC_MAP = {
    "coze-skill": (True, "coze-skill", False),
    "ai-plugins": (True, "plugin", False),
    "ai-agent": (False, "framework", True),
    "agent-framework": (False, "framework", True),
    "llm-agent": (False, "framework", True),
    "mcp-server": (False, "MCP", True),
}

# 跳过的 section（非项目条目）
_SKIP_SECTIONS = {"contents", "data sources", "contributing", "license", "specs", "directories"}


def _fetch_repo_readme(repo: str, path: str = "README.md") -> str:
    """获取指定仓库的文件内容（通用版）"""
    data = github_api_request(f"/repos/{repo}/contents/{path}")
    if "error" in data:
        return ""
    content = data.get("content", "")
    if not content:
        return ""
    try:
        return base64.b64decode(content).decode("utf-8")
    except Exception:
        return ""


def _parse_agent_skills_readme(content: str) -> List[Dict]:
    """
    解析 awesome-agent-skills README，提取项目条目
    格式：- [name](url) - description. ![GitHub stars](...)
    按 section 分类，section 决定 is_skill / agent_integration / standalone
    """
    projects = []
    current_section = ""
    current_class = (False, None, True)

    for line in content.split("\n"):
        # 检测 section header
        if line.startswith("## ") and not line.startswith("## Contents"):
            header = line[3:].strip().lower()
            if any(skip in header for skip in _SKIP_SECTIONS):
                current_section = ""
                continue
            matched = False
            for key, val in _SKILL_SECTION_MAP.items():
                if key in header:
                    current_section = line[3:].strip()
                    current_class = val
                    matched = True
                    break
            if not matched:
                current_section = ""
            continue

        # 解析项目条目
        if current_section and line.strip().startswith("- "):
            match = re.match(r'-\s+\[([^\]]+)\]\(([^)]+)\)\s*-?\s*(.+)', line.strip())
            if match:
                name, url, desc = match.groups()
                desc = re.sub(r'!\[GitHub stars\]\([^)]*\)', '', desc).strip()
                desc = re.sub(r'!\[.*?\]\([^)]*\)', '', desc).strip()

                repo_match = re.match(r'https://github\.com/([^/]+/[^/)]+)', url)
                repo_name = repo_match.group(1).rstrip('.') if repo_match else None

                is_skill, agent_integration, standalone = current_class

                projects.append({
                    "name": name,
                    "repo_name": repo_name or name,
                    "html_url": url,
                    "about": desc,
                    "section": current_section,
                    "is_skill": is_skill,
                    "agent_integration": agent_integration,
                    "standalone": standalone,
                    "_source": "awesome-agent-skills",
                })

    return projects


def _parse_ai_agents_readme(content: str) -> List[Dict]:
    """
    解析 awesome-ai-agents README，提取项目条目
    格式：## [Name](url) 后跟描述行
    这些是 agent 框架/平台，is_skill=False, standalone=True
    """
    projects = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        # 检测项目 header: ## [Name](url)
        if line.startswith("## [") and "](" in line:
            match = re.match(r'##\s+\[([^\]]+)\]\(([^)]+)\)', line)
            if match:
                name, url = match.groups()
                if not url.startswith("http"):
                    i += 1
                    continue

                # 读取下一行作为描述
                desc = ""
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith("<") and not next_line.startswith("#") and not next_line.startswith("Category"):
                        desc = next_line

                # 尝试提取 GitHub owner/repo
                repo_match = re.match(r'https://github\.com/([^/]+/[^/)]+)', url)
                repo_name = repo_match.group(1).rstrip('.') if repo_match else None

                # 从 <details> 中提取 Category（快速扫描）
                category = ""
                for j in range(i + 2, min(i + 15, len(lines))):
                    if "### Category" in lines[j]:
                        if j + 1 < len(lines):
                            category = lines[j + 1].strip()
                        break
                    if lines[j].startswith("## [") and "](" in lines[j]:
                        break

                # 判断是否框架类（可接入 agent）
                cat_lower = category.lower()
                agent_integration = None
                if any(k in cat_lower for k in ["build", "framework", "multi-agent", "tool"]):
                    agent_integration = "framework"

                # 只收录有 GitHub 链接的项目
                if repo_name:
                    projects.append({
                        "name": name,
                        "repo_name": repo_name,
                        "html_url": url,
                        "about": desc,
                        "category": category,
                        "is_skill": False,
                        "agent_integration": agent_integration,
                        "standalone": True,
                        "_source": "awesome-ai-agents",
                    })
        i += 1

    return projects


def _search_github_topics(query: str, limit: int = 20) -> List[Dict]:
    """按 GitHub topic 搜索 agent 相关项目"""
    projects = []
    seen = set()

    for topic in AGENT_GITHUB_TOPICS:
        search_q = f'{query} topic:{topic}' if query else f'topic:{topic}'
        params = {"q": search_q, "sort": "stars", "order": "desc", "per_page": 5}
        data = github_api_request("/search/repositories", params)

        if "items" not in data:
            continue

        is_skill, agent_integration, standalone = _TOPIC_MAP.get(topic, (False, None, True))

        for item in data["items"]:
            key = item["full_name"]
            if key in seen:
                continue
            seen.add(key)

            projects.append({
                "name": item["name"],
                "repo_name": key,
                "html_url": item["html_url"],
                "about": item.get("description", ""),
                "star_count": item["stargazers_count"],
                "language": item.get("language", ""),
                "tags": item.get("topics", []),
                "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
                "is_skill": is_skill,
                "agent_integration": agent_integration,
                "standalone": standalone,
                "_source": f"github-topic:{topic}",
                "_github_license": item.get("license", {}).get("name", "") if item.get("license") else "",
                "_github_owner_type": item.get("owner", {}).get("type", ""),
                "_github_owner_login": item.get("owner", {}).get("login", ""),
                "_github_pushed_at": item.get("pushed_at", ""),
            })

    return projects


def _match_agent_keywords(text: str, query: str) -> int:
    """计算关键词匹配分数（用于 agent 搜索）"""
    if not text or not query:
        return 0
    text_lower = text.lower()
    query_lower = query.lower()
    score = 0
    if query_lower in text_lower:
        score += 10
    for word in query_lower.split():
        if len(word) > 1 and word in text_lower:
            score += 3
    # 额外中文关键词映射匹配
    for cn, en in KEYWORD_MAP.items():
        if cn in query_lower and en in text_lower:
            score += 3
        if en in query_lower and cn in text_lower:
            score += 3
    return score


# --- 区域适用性检测（v4.2.0） ---

# 国内环境特征信号（项目依赖/面向国内生态）
_DOMESTIC_SIGNALS = [
    "wechat", "weixin", "alipay", "zhifubao", "dingtalk", "dingding",
    "feishu", "lark", "baidu", "tencent", "qq.com", "weibo",
    "douyin", "bilibili", "taobao", "tmall", "jd.com", "gitee",
    "qcloud", "aliyun", "aliyuncs", "huaweicloud", "huawei cloud",
    "miniprogram", "minapp", "wxapp", "微信", "支付宝", "钉钉",
    "飞书", "百度", "腾讯", "微博", "抖音", "小程序", "微信公众号",
    "企业微信", "快手", "小红书", "知乎", "掘金", "csdn",
    "npmmirror", "cnpm", "taobao.org", "registry.npmmirror",
    "oss-cn", "cos.ap-", "cloudbase", "tcb-", "jdcloud",
    "wechaty", "itchat", "wechatpy", "wxpy",
]

# 外网环境特征信号（项目依赖/面向国际生态）
_FOREIGN_SIGNALS = [
    "openai", "anthropic", "claude", "stripe", "slack", "discord",
    "notion", "linear", "figma", "airtable", "supabase", "firebase",
    "vercel", "netlify", "heroku", "railway", "render.com",
    "aws", "amazonaws", "gcp", "googleapis", "azure.microsoft",
    "cloudflare", "github actions", "gitlab ci",
    "twitter", "x.com", "reddit", "medium.com", "producthunt",
    "google maps", "youtube", "gmail", "google drive",
    "google sheets", "google calendar", "zoom", "webex",
    "shopify", "ebay", "amazon sp-api",
]


def _detect_region(project: Dict) -> str:
    """
    检测项目的区域适用性（v4.2.0）

    返回值:
        "domestic" - 面向国内环境（依赖国内服务/API，国内用户友好）
        "international" - 面向国际环境（依赖外网服务/API，国内无VPN可能不可用）
        "universal" - 通用（无明显区域依赖或同时依赖国内外服务）

    判断依据:
        1. 项目描述/名称/tags 中的服务依赖信号
        2. 项目来源平台（虾评/SkillHub → 偏国内；MCP Registry/Smithery → 偏外网）
        3. URL 域名（gitee.com → 国内）
    """
    domestic_score = 0
    foreign_score = 0

    # 汇总可搜索文本
    searchable_parts = [
        project.get("name", ""),
        project.get("about", ""),
        project.get("description", ""),
        project.get("section", ""),
        project.get("category", ""),
        " ".join(project.get("tags", []) or []),
        " ".join(project.get("topics", []) or []),
    ]
    searchable = " ".join(searchable_parts).lower()

    # 检查国内信号
    for signal in _DOMESTIC_SIGNALS:
        if signal in searchable:
            domestic_score += 1

    # 检查外网信号
    for signal in _FOREIGN_SIGNALS:
        if signal in searchable:
            foreign_score += 1

    # URL 域名判断
    url = (project.get("html_url", "") or "").lower()
    repo = (project.get("repo_name", "") or "").lower()
    if "gitee.com" in url or "gitee.com" in repo:
        domestic_score += 2
    if "coding.net" in url:
        domestic_score += 2

    # 来源平台判断
    source = (project.get("_source", "") or "").lower()
    if source in ("xiaping", "skillhub"):
        domestic_score += 1
    elif source in ("mcp_registry", "smithery", "glama", "hermes"):
        foreign_score += 1

    # 判定逻辑
    if domestic_score >= 2 and foreign_score == 0:
        return "domestic"
    elif foreign_score >= 2 and domestic_score == 0:
        return "international"
    elif domestic_score >= 2 and foreign_score >= 2:
        return "universal"  # 同时依赖国内外服务
    elif domestic_score >= 1 and foreign_score == 0:
        return "domestic"
    elif foreign_score >= 1 and domestic_score == 0:
        return "international"
    else:
        return "universal"


def _filter_by_region(projects: List[Dict], region: str) -> List[Dict]:
    """按区域过滤项目列表（v4.2.0）

    参数:
        region: "all"(不过滤) / "cn"(国内用户) / "global"(国际用户)
    """
    if not region or region == "all":
        return projects

    filtered = []
    for proj in projects:
        proj_region = proj.get("region", "universal")
        if region in ("cn", "domestic"):
            # 国内用户：保留 domestic + universal
            if proj_region in ("domestic", "universal"):
                filtered.append(proj)
        elif region in ("global", "international"):
            # 国际用户：保留 international + universal
            if proj_region in ("international", "universal"):
                filtered.append(proj)
    return filtered


# --- 广义搜索+智能体适配检测（v4.1.0） ---

# 智能体适配关键词（用于检测非技能标签项目是否有 agent 适配）
_AGENT_ADAPT_KEYWORDS = {
    "mcp": "MCP",
    "model context protocol": "MCP",
    "mcp-server": "MCP",
    "skill": "SKILL.md",
    "agentskills": "SKILL.md",
    "skill.md": "SKILL.md",
    "coze-skill": "coze-skill",
    "coze skill": "coze-skill",
    "plugin": "plugin",
    "ai-plugin": "plugin",
    "ai plugin": "plugin",
    "cursor rules": "cursor-rules",
    "copilot extension": "copilot-extension",
    "openclaw": "openclaw-skill",
    "gemini extension": "gemini-extension",
    "windsurf rules": "windsurf-rules",
}


def _search_broad_agent_match(query: str, limit: int = 10) -> List[Dict]:
    """
    广义搜索 + 智能体适配检测（v4.1.0）

    策略：先搜索关键词本身（不加 skill/agent topic 限定），
    再检查搜索结果是否包含智能体适配信号（README 描述、topics、名称中的关键词）

    这能发现那些后续做了智能体适配但未打标签的项目，
    以及项目名称/描述中提及 MCP/Agent 但未被 awesome 列表收录的项目
    """
    # 广义搜索（不加 topic 限定）
    search_q = query if query else "ai agent tool"
    params = {"q": search_q, "sort": "stars", "order": "desc", "per_page": min(limit, 10)}
    data = github_api_request("/search/repositories", params)
    if "items" not in data:
        return []

    projects = []
    for item in data["items"]:
        desc = (item.get("description") or "").lower()
        topics = [t.lower() for t in item.get("topics", [])]
        name = (item.get("name") or "").lower()
        full_name = (item.get("full_name") or "").lower()
        searchable = f"{name} {desc} {' '.join(topics)}"

        # 检测智能体适配信号
        agent_integration = None
        for keyword, integration_type in _AGENT_ADAPT_KEYWORDS.items():
            if keyword in searchable or keyword in topics:
                agent_integration = integration_type
                break

        # 额外检查：名称中包含 agent/tool/mcp 等关键词
        if not agent_integration:
            if any(kw in name for kw in ["mcp", "agent", "skill", "plugin"]):
                agent_integration = "framework"

        if not agent_integration:
            continue  # 无适配信号，跳过

        # 判断是否技能类
        is_skill = agent_integration in ("SKILL.md", "plugin", "coze-skill",
                                         "cursor-rules", "copilot-extension",
                                         "openclaw-skill", "gemini-extension", "windsurf-rules")

        projects.append({
            "name": item["name"],
            "repo_name": item["full_name"],
            "html_url": item["html_url"],
            "about": item.get("description", ""),
            "star_count": item["stargazers_count"],
            "language": item.get("language", ""),
            "tags": item.get("topics", []),
            "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
            "is_skill": is_skill,
            "agent_integration": agent_integration,
            "standalone": True,
            "_source": "broad-agent-match",
            "_github_license": item.get("license", {}).get("name", "") if item.get("license") else "",
            "_github_owner_type": item.get("owner", {}).get("type", ""),
            "_github_owner_login": item.get("owner", {}).get("login", ""),
            "_github_pushed_at": item.get("pushed_at", ""),
        })

    return projects


def _cross_validate_ratings(projects: List[Dict]) -> Dict:
    """
    多源交叉验证（v4.1.0）

    检测同一项目在不同平台的评分差异，识别可能的控评行为
    平台评分可能受官方和技能发布者监控与管控，极端评论可能被掩盖

    返回 {repo_name: cross_validation_info} 字典
    """
    # 按 repo_name 分组
    by_repo = {}
    for p in projects:
        repo = p.get("repo_name", "")
        if not repo:
            continue
        if repo not in by_repo:
            by_repo[repo] = []
        by_repo[repo].append(p)

    cross_results = {}
    for repo, sources in by_repo.items():
        if len(sources) < 2:
            continue  # 仅对出现在 2+ 平台的项目做交叉验证

        ratings = []
        for s in sources:
            pd = s.get("_platform_data", {})
            source_name = s.get("_source", "")

            # 收集各平台的评分数据（统一到 0-5 分制）
            avg_rating = pd.get("avg_rating", 0)
            popularity = pd.get("popularity_score", 0)
            ai_score = pd.get("ai_score", 0)
            star_count = s.get("star_count", 0)

            if avg_rating and avg_rating > 0:
                ratings.append({"source": source_name, "rating": float(avg_rating), "type": "user_rating"})
            if popularity and popularity > 0:
                # popularity_score 是 0-1，转换为 0-5
                ratings.append({"source": source_name, "rating": float(popularity) * 5, "type": "popularity"})
            if ai_score and ai_score > 0:
                ratings.append({"source": source_name, "rating": float(ai_score), "type": "ai_score"})
            if star_count and star_count > 0:
                # star 数对数缩放到 0-5（10000 stars ≈ 5分）
                star_rating = min(5.0, math.log10(max(star_count, 1)) * 1.25)
                ratings.append({"source": source_name, "rating": round(star_rating, 2), "type": "stars"})

        if len(ratings) >= 2:
            rating_values = [r["rating"] for r in ratings]
            max_diff = max(rating_values) - min(rating_values)
            avg_rating_val = sum(rating_values) / len(rating_values)

            # 评分差异 > 2 分（5分制）标记为可能控评
            flag_manipulation = max_diff > 2.0

            cross_results[repo] = {
                "sources": [s.get("_source", "") for s in sources],
                "ratings": ratings,
                "avg_rating": round(avg_rating_val, 2),
                "max_discrepancy": round(max_diff, 2),
                "flag_review_manipulation": flag_manipulation,
            }

    return cross_results


def search_agent(query: str, mode: str = "all", limit: int = 15, region: str = "all") -> Dict:
    """
    搜索智能体技能/工具相关项目

    三个维度的分类：
    - is_skill: 是否为技能/插件（需要 agent 平台才能运行）
    - agent_integration: 接入 agent 的方式（MCP / SKILL.md / API / SDK / framework / None）
    - standalone: 是否可独立使用（不依赖 agent 平台）

    is_skill 和 agent_integration 是独立维度：
    - 技能一定可接入 agent，但可接入 agent 的不一定是技能
    - 框架/工具可以接入 agent 但不是技能

    参数：
        query: 搜索关键词
        mode: 搜索模式
            - "all": 返回所有 agent 相关项目（技能 + 工具 + 框架）
            - "skill": 仅返回技能/插件（需要 agent 平台才能使用）
            - "standalone": 仅返回可独立使用的项目（排除纯技能）
            - "integrate": 仅返回可接入 agent 的项目（有 agent_integration 值）
            - "safe": 仅返回安全评分≥60的结果，按安全评分排序
        limit: 返回结果上限
    """
    results = {
        "query": query,
        "source": "agent",
        "mode": mode,
        "region_filter": region,
        "projects": [],
    }

    all_projects = []

    # 1. 解析 awesome-agent-skills（技能/插件/MCP/工具目录）
    skills_readme = _fetch_repo_readme(AGENT_SKILLS_REPO)
    if skills_readme:
        all_projects.extend(_parse_agent_skills_readme(skills_readme))

    # 2. 解析 awesome-ai-agents（agent 框架/平台）
    agents_readme = _fetch_repo_readme(AI_AGENTS_REPO)
    if agents_readme:
        all_projects.extend(_parse_ai_agents_readme(agents_readme))

    # 3. 搜索 GitHub topics
    topic_projects = _search_github_topics(query, limit=limit)
    all_projects.extend(topic_projects)

    # 4. 搜索 MCP Registry（官方注册中心，无需认证，4500+ 服务器）
    mcp_projects = search_mcp_registry(query, limit=limit)
    all_projects.extend(mcp_projects)

    # 5. 搜索 Smithery（可选，需免费 token，无 token 时静默跳过）
    smithery_projects = search_smithery(query, limit=limit)
    all_projects.extend(smithery_projects)

    # 6. 搜索 Glama MCP 目录（网页解析，可能不稳定，失败时静默跳过）
    glama_projects = search_glama(query, limit=limit)
    all_projects.extend(glama_projects)

    # 6b. 搜索 Hermes Skills Hub（v4.1.0，agentskills.io 标准，100+ 验证技能）
    hermes_projects = search_hermes_skills(query, limit=limit)
    all_projects.extend(hermes_projects)

    # 6c. 搜索虾评技能平台（v4.1.0，需 token，无 token 时静默跳过）
    xiaping_projects = search_xiaping(query, limit=limit)
    all_projects.extend(xiaping_projects)

    # 6d. 搜索腾讯 SkillHub（v4.1.0，网页解析，失败时静默跳过）
    skillhub_projects = search_skillhub(query, limit=limit)
    all_projects.extend(skillhub_projects)

    # 6e. 广义搜索 + 智能体适配检测（v4.1.0）
    # 先搜索关键词本身，再检查是否有 agent 适配信号
    # 发现后续做了智能体适配但未打标签的项目
    broad_projects = _search_broad_agent_match(query, limit=limit)
    all_projects.extend(broad_projects)

    # 7. 关键词匹配和评分
    scored = []
    for proj in all_projects:
        searchable = " ".join([
            proj.get("name", ""),
            proj.get("about", ""),
            proj.get("section", ""),
            proj.get("category", ""),
            " ".join(proj.get("tags", [])),
        ])
        if query:
            score = _match_agent_keywords(searchable, query)
            if score > 0:
                proj["_match_score"] = score
                scored.append(proj)
        else:
            proj["_match_score"] = 1
            scored.append(proj)

    # 8. 按 mode 过滤
    if mode == "skill":
        scored = [p for p in scored if p.get("is_skill")]
    elif mode == "standalone":
        scored = [p for p in scored if p.get("standalone") and not p.get("is_skill")]
    elif mode == "integrate":
        scored = [p for p in scored if p.get("agent_integration")]

    # 9. 排序
    scored.sort(key=lambda x: x.get("_match_score", 0), reverse=True)

    # 10. 去重（按 repo_name）
    seen = set()
    unique = []
    for p in scored:
        key = p.get("repo_name", p.get("name", ""))
        if key not in seen:
            seen.add(key)
            unique.append(p)

    # 10b. 区域适用性检测与过滤（v4.2.0）
    # 为每个项目标注 region 字段，并按用户环境过滤
    for proj in unique:
        proj["region"] = _detect_region(proj)
    if region and region != "all":
        unique = _filter_by_region(unique, region)

    # 11. 安全评估（v4.0.0 + v4.1.0 源码扫描）
    # 对每个结果应用 6 维度安全评估
    # GitHub topic 结果已含 license/owner/star 信息，无需额外 API 调用
    # 仅对 awesome 列表/MCP Registry 等非 GitHub Search 来源的 GitHub 项目做轻量级 API 调用
    # v4.1.0: 对小项目追加源码级安全扫描
    github_cache = {}
    _api_calls = 0
    _max_api_calls = 8  # 限制额外 GitHub API 调用数量，避免超时
    _scan_calls = 0
    _max_scan_calls = 3  # 限制源码扫描次数（每次扫描涉及多次 API 调用）
    for proj in unique[:limit]:
        repo_name = proj.get("repo_name", "")

        # 如果已有 GitHub Search API 返回的数据，直接使用
        if proj.get("_github_license") is not None or proj.get("_github_owner_type"):
            github_cache[repo_name] = {
                "license": proj.get("_github_license", ""),
                "star_count": proj.get("star_count", 0),
                "pushed_at": proj.get("_github_pushed_at", ""),
                "owner_type": proj.get("_github_owner_type", ""),
                "owner_login": proj.get("_github_owner_login", ""),
            }
        elif "github.com" in proj.get("html_url", "") and repo_name and repo_name not in github_cache and _api_calls < _max_api_calls:
            try:
                _api_calls += 1
                _data = github_api_request(f"/repos/{repo_name}")
                if "error" not in _data:
                    github_cache[repo_name] = {
                        "license": _data.get("license", {}).get("name", "") if _data.get("license") else "",
                        "star_count": _data.get("stargazers_count", 0),
                        "pushed_at": _data.get("pushed_at", ""),
                        "owner_type": _data.get("owner", {}).get("type", ""),
                        "owner_login": _data.get("owner", {}).get("login", ""),
                        "forks_count": _data.get("forks_count", 0),
                        "size": _data.get("size", 0),
                    }
                else:
                    github_cache[repo_name] = None
            except Exception:
                github_cache[repo_name] = None

        repo_details = github_cache.get(repo_name)
        safety = assess_safety(proj, repo_details)

        # v4.1.0: 源码级安全扫描（仅对小项目，避免超时）
        # 条件：GitHub 项目 + 有 repo_name + 未超出扫描次数限制 + 项目较小（< 5000KB）
        repo_size = github_cache.get(repo_name, {}).get("size", 0) if github_cache.get(repo_name) else 0
        if (repo_name and "github.com" in proj.get("html_url", "")
                and "/" in repo_name and _scan_calls < _max_scan_calls
                and repo_size > 0 and repo_size < 5000):
            try:
                _scan_calls += 1
                code_flags = scan_source_code(repo_name, max_files=10)
                if code_flags:
                    # 合并源码扫描结果到红旗列表
                    safety["red_flags"].extend(code_flags)
                    # 重新计算降级
                    critical_count = sum(1 for f in safety["red_flags"] if f["severity"] == "critical")
                    high_count = sum(1 for f in safety["red_flags"] if f["severity"] == "high")
                    if critical_count > 0:
                        safety["safety_score"] = min(safety["safety_score"], 25)
                    elif high_count >= 2:
                        safety["safety_score"] = min(safety["safety_score"], 40)
                    elif high_count >= 1:
                        safety["safety_score"] = min(safety["safety_score"], 55)
                    # 重新计算风险等级
                    score = safety["safety_score"]
                    if score >= 80:
                        safety["risk_level"] = "low"
                        safety["risk_badge"] = "🟢"
                        safety["risk_label"] = "低风险"
                    elif score >= 60:
                        safety["risk_level"] = "medium"
                        safety["risk_badge"] = "🟡"
                        safety["risk_label"] = "中风险"
                    elif score >= 30:
                        safety["risk_level"] = "high"
                        safety["risk_badge"] = "🟠"
                        safety["risk_label"] = "高风险"
                    else:
                        safety["risk_level"] = "critical"
                        safety["risk_badge"] = "🔴"
                        safety["risk_label"] = "极高风险"
            except Exception:
                pass  # 源码扫描失败不影响基本安全评估

        proj["safety"] = safety
        proj["safety_summary"] = _safety_summary(safety)

    # 11b. 多源交叉验证（v4.1.0）
    # 检测同一项目在不同平台的评分差异，识别可能的控评行为
    cross_validation = _cross_validate_ratings(unique)
    if cross_validation:
        for proj in unique[:limit]:
            repo = proj.get("repo_name", "")
            if repo in cross_validation:
                cv = cross_validation[repo]
                proj["cross_validation"] = cv
                if cv.get("flag_review_manipulation"):
                    proj["safety_summary"] += " ⚠评分差异大"

    # safe 模式：仅返回安全评分 ≥ 60 的结果，按安全评分排序
    if mode == "safe":
        unique = [p for p in unique if p.get("safety", {}).get("safety_score", 0) >= 60]
        unique.sort(key=lambda x: x.get("safety", {}).get("safety_score", 0), reverse=True)

    # 统计数据源分布
    source_stats = {}
    region_stats = {}
    for p in unique:
        src = p.get("_source", "unknown")
        source_stats[src] = source_stats.get(src, 0) + 1
        reg = p.get("region", "universal")
        region_stats[reg] = region_stats.get(reg, 0) + 1

    results["projects"] = unique[:limit]
    results["total_found"] = len(unique)
    results["source_stats"] = source_stats
    results["region_stats"] = region_stats
    results["safety_enabled"] = True
    results["code_scan_enabled"] = _scan_calls > 0
    results["cross_validation_count"] = len(cross_validation)
    return results


# ============ 10. 跨平台技能搜索与安全评估（v4.0.0） ============

# --- 平台 API 端点 ---
MCP_REGISTRY_API = "https://registry.modelcontextprotocol.io/v0/servers"
SMITHERY_API = "https://smithery.ai/v1/servers"
GLAMA_URL = "https://glama.ai/mcp/servers"

# --- 安全评价维度权重 ---
_SAFETY_WEIGHTS = {
    "code_transparency": 0.30,       # 代码透明度
    "source_credibility": 0.25,      # 来源可信度
    "maintenance": 0.15,             # 维护活跃度
    "community_adoption": 0.15,      # 社区采纳度
    "permission_transparency": 0.10, # 权限透明度
    "security_record": 0.05,         # 安全记录
}

# --- Red Flag 正则 ---
_REDFLAG_PATTERNS = {
    "hardcoded_ip": re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b'),
    "http_insecure": re.compile(r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)'),
    "apikey_exposed": re.compile(r'(?:api[_-]?key|token|secret|password)\s*[=:]\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
}


def _safe_http_get(url: str, headers: Dict = None, params: Dict = None, timeout: int = 15) -> Dict:
    """安全 HTTP GET 请求（用于非 GitHub API 的外部请求）"""
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"_raw_text": resp.text}
        return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ---------- 平台搜索函数 ----------

def search_mcp_registry(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索 MCP Registry（官方注册中心，由 Anthropic + GitHub + PulseMCP 维护）
    无需认证，REST API，4500+ 服务器
    API: GET https://registry.modelcontextprotocol.io/v0/servers?search={q}&limit={n}
    """
    params = {"search": query} if query else {}
    params["limit"] = str(limit)
    data = _safe_http_get(MCP_REGISTRY_API, params=params)
    if "error" in data:
        return []

    servers = data.get("servers", [])
    if not servers and isinstance(data, list):
        servers = data

    projects = []
    seen_names = set()  # MCP Registry 返回多版本，去重
    for item in servers:
        # MCP Registry v0 格式：每条记录嵌套在 "server" 键内
        srv = item.get("server", item) if isinstance(item, dict) else {}

        name = srv.get("name", "")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        repo_url = srv.get("repository", {}).get("url", "") if isinstance(srv.get("repository"), dict) else ""
        repo_name = None
        if repo_url:
            m = re.match(r'https://github\.com/([^/]+/[^/)]+)', repo_url)
            if m:
                repo_name = m.group(1).rstrip('.')

        # _meta 中的官方验证状态
        meta = item.get("_meta", srv.get("_meta", {}))
        official_meta = meta.get("io.modelcontextprotocol.registry/official", {}) if isinstance(meta, dict) else {}
        is_verified = official_meta.get("status") == "active"

        projects.append({
            "name": name,
            "repo_name": repo_name or name,
            "html_url": repo_url or srv.get("url", ""),
            "about": srv.get("description", ""),
            "is_skill": False,
            "agent_integration": "MCP",
            "standalone": True,
            "_source": "mcp-registry",
            "_platform_data": {
                "registry_id": srv.get("id", name),
                "version": srv.get("version", ""),
                "license": srv.get("license", ""),
                "verified": is_verified,
            },
        })

    return projects


def search_smithery(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索 Smithery（7300+ MCP 服务器，支持语义搜索）
    需要免费 token：smithery.ai 注册后 Account Settings > API Keys 获取
    环境变量：COZE_SMITHERY_TOKEN
    无 token 时静默跳过
    """
    token = os.getenv("COZE_SMITHERY_TOKEN", "")
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query or "", "page": "1", "pageSize": str(limit)}
    data = _safe_http_get(SMITHERY_API, headers=headers, params=params)
    if "error" in data:
        return []

    servers = data.get("servers", data.get("data", []))
    if not isinstance(servers, list):
        return []

    projects = []
    for srv in servers:
        repo_url = srv.get("repository", srv.get("url", ""))
        repo_name = None
        if repo_url:
            m = re.match(r'https://github\.com/([^/]+/[^/)]+)', repo_url)
            if m:
                repo_name = m.group(1).rstrip('.')

        projects.append({
            "name": srv.get("name", srv.get("qualifiedName", "")),
            "repo_name": repo_name or srv.get("name", ""),
            "html_url": repo_url or f"https://smithery.ai/server/{srv.get('qualifiedName', '')}",
            "about": srv.get("description", ""),
            "is_skill": False,
            "agent_integration": "MCP",
            "standalone": True,
            "_source": "smithery",
            "_platform_data": {
                "smithery_id": srv.get("id", ""),
                "verified": srv.get("isVerified", False),
                "downloads": srv.get("downloads", 0),
                "license": srv.get("license", ""),
            },
        })

    return projects


def search_glama(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索 Glama MCP 目录（67960+ 服务器，网页解析）
    Glama 自带 A/B/C 质量评级（license/quality/maintenance 三维度）
    无公开 API，通过 HTML 解析；解析失败时静默返回空列表
    """
    params = {"q": query} if query else {}
    data = _safe_http_get(GLAMA_URL, params=params)
    if "error" in data or "_raw_text" not in data:
        return []

    html = data.get("_raw_text", "")
    if not html:
        return []

    projects = []
    # Glama 服务器卡片格式：<a href="/mcp/servers/@xxx" ...> 名称、描述
    card_pattern = re.compile(
        r'href="/mcp/servers/([^"]+)"[^>]*>.*?<h[23][^>]*>\s*([^<]+)\s*</h[23]>',
        re.DOTALL
    )

    for match in card_pattern.finditer(html):
        server_id = match.group(1).strip()
        name = match.group(2).strip()
        if len(projects) >= limit:
            break

        # 尝试提取描述（卡片内 <p> 标签）
        desc = ""
        desc_match = re.search(r'<p[^>]*>\s*([^<]{10,})\s*</p>', html[match.end():match.end()+500])
        if desc_match:
            desc = desc_match.group(1).strip()

        # 提取质量评级（A/B/C）
        quality_grade = None
        qm = re.search(r'(?:quality|grade)["\s>:]*([ABC])', html[match.start():match.end()+800], re.IGNORECASE)
        if qm:
            quality_grade = qm.group(1)

        projects.append({
            "name": name,
            "repo_name": server_id,
            "html_url": f"https://glama.ai/mcp/servers/{server_id}",
            "about": desc,
            "is_skill": False,
            "agent_integration": "MCP",
            "standalone": True,
            "_source": "glama",
            "_platform_data": {
                "glama_id": server_id,
                "quality_grade": quality_grade,
            },
        })

    return projects


def search_hermes_skills(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索 Hermes Skills Hub（agentskills.io 标准，100+ 验证技能）
    数据源：freshtemp-labs/hermes-skills-bridge 仓库的 top100.json
    含 popularity_score、category、tags，所有技能已验证
    """
    url = "https://raw.githubusercontent.com/freshtemp-labs/hermes-skills-bridge/main/top100.json"
    data = _safe_http_get(url, timeout=20)
    if "error" in data:
        return []

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        return []

    projects = []
    query_lower = (query or "").lower()

    for skill in skills:
        name = skill.get("name", "")
        desc = skill.get("description", "")
        reason = skill.get("reason", "")
        tags = skill.get("tags", [])
        category = skill.get("category", "")
        repo = skill.get("repo", "")
        path = skill.get("path", "")

        # 关键词匹配
        if query_lower:
            searchable = f"{name} {desc} {reason} {' '.join(tags)} {category}".lower()
            if query_lower not in searchable:
                # 分词匹配
                words = query_lower.split()
                if not all(w in searchable for w in words if len(w) > 1):
                    continue

        html_url = f"https://github.com/{repo}/tree/main/{path}" if repo and path else (f"https://github.com/{repo}" if repo else "")

        projects.append({
            "name": name,
            "repo_name": repo or name,
            "html_url": html_url,
            "about": desc or reason,
            "is_skill": True,
            "agent_integration": "SKILL.md",
            "standalone": False,
            "_source": "hermes",
            "_platform_data": {
                "popularity_score": skill.get("popularity_score", 0),
                "category": category,
                "tags": tags,
                "verified": True,
            },
        })

        if len(projects) >= limit:
            break

    return projects


def search_xiaping(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索虾评技能平台（xiaping.coze.com）
    Agent 技能评测平台，含用户评分、下载量、评测数
    需要 XIAPING_KEY 或 COZE_XIAPING_TOKEN 环境变量
    无 token 时静默跳过
    """
    token = os.getenv("XIAPING_KEY", "") or os.getenv("COZE_XIAPING_TOKEN", "")
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query or "", "page": "1", "limit": str(limit)}
    data = _safe_http_get("https://xiaping.coze.com/api/skills/search",
                          headers=headers, params=params)
    if "error" in data:
        return []

    skills = data.get("data", data.get("skills", []))
    if not isinstance(skills, list):
        return []

    projects = []
    for skill in skills:
        name = skill.get("name", "")
        desc = skill.get("description", "")
        repo_url = skill.get("repo_url", skill.get("github_url", ""))
        repo_name = None
        if repo_url:
            m = re.match(r'https://github\.com/([^/]+/[^/)]+)', repo_url)
            if m:
                repo_name = m.group(1).rstrip('.')

        # 虾评的多维评分
        dims = skill.get("dimensions", {})
        avg_rating = skill.get("avg_rating", skill.get("stars", 0))

        projects.append({
            "name": name,
            "repo_name": repo_name or name,
            "html_url": repo_url or skill.get("url", f"https://xiaping.coze.com/skill/{skill.get('id', '')}"),
            "about": desc,
            "is_skill": True,
            "agent_integration": "coze-skill",
            "standalone": False,
            "_source": "xiaping",
            "_platform_data": {
                "stars": skill.get("stars", 0),
                "downloads": skill.get("downloads", 0),
                "reviews": skill.get("review_count", skill.get("comments_count", 0)),
                "avg_rating": avg_rating,
                "status": skill.get("status", ""),
                "verified": skill.get("status") == "official",
                "functionality": dims.get("functionality", 0),
                "effectiveness": dims.get("effectiveness", 0),
                "scarcity": dims.get("scarcity", 0),
            },
        })

    return projects


def search_skillhub(query: str, limit: int = 10) -> List[Dict]:
    """
    搜索腾讯 SkillHub（skillhub.cn）
    基于 OpenClaw/ClawHub 生态，13000+ 技能，含 AI 评分和安全审核
    无公开 API，通过网页解析；解析失败时静默返回空列表
    """
    url = "https://skillhub.cn/skills"
    params = {"search": query} if query else {}
    data = _safe_http_get(url, params=params, timeout=20)
    if "error" in data or "_raw_text" not in data:
        return []

    html = data.get("_raw_text", "")
    if not html:
        return []

    projects = []
    # SkillHub 使用 Next.js，尝试从 __NEXT_DATA__ 提取
    next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data_match:
        try:
            next_data = json.loads(next_data_match.group(1))
            # 尝试从 props 中提取技能列表
            skills = (next_data.get("props", {})
                      .get("pageProps", {})
                      .get("skills", []))
            for skill in skills[:limit]:
                name = skill.get("name", "")
                skill_id = skill.get("id", skill.get("slug", ""))
                author = skill.get("author", skill.get("developer", ""))
                ai_score = skill.get("ai_score", skill.get("rating", 0))
                desc = skill.get("description", skill.get("summary", ""))

                projects.append({
                    "name": name,
                    "repo_name": skill_id or name,
                    "html_url": f"https://skillhub.cn/skills/{skill_id}" if skill_id else "https://skillhub.cn/skills",
                    "about": desc,
                    "is_skill": True,
                    "agent_integration": "openclaw-skill",
                    "standalone": False,
                    "_source": "skillhub",
                    "_platform_data": {
                        "ai_score": ai_score,
                        "author": author,
                        "downloads": skill.get("downloads", 0),
                        "verified": True,  # SkillHub 有安全审核
                    },
                })
        except (json.JSONDecodeError, KeyError):
            pass

    # 如果 Next.js 数据提取失败，尝试 HTML 卡片解析
    if not projects:
        card_pattern = re.compile(
            r'href="/skills/([^"]+)"[^>]*>.*?<h[2-4][^>]*>\s*([^<]+)\s*</h[2-4]',
            re.DOTALL
        )
        for match in card_pattern.finditer(html):
            skill_id = match.group(1).strip()
            name = match.group(2).strip()
            if len(projects) >= limit:
                break

            # 尝试提取描述和评分
            snippet = html[match.end():match.end() + 500]
            desc_match = re.search(r'<p[^>]*>\s*([^<]{10,})\s*</p>', snippet)
            desc = desc_match.group(1).strip() if desc_match else ""
            score_match = re.search(r'(\d+\.\d+)\s*/\s*5', snippet)
            ai_score = float(score_match.group(1)) if score_match else 0

            projects.append({
                "name": name,
                "repo_name": skill_id,
                "html_url": f"https://skillhub.cn/skills/{skill_id}",
                "about": desc,
                "is_skill": True,
                "agent_integration": "openclaw-skill",
                "standalone": False,
                "_source": "skillhub",
                "_platform_data": {
                    "ai_score": ai_score,
                    "verified": True,
                },
            })

    return projects


# ---------- 安全评估函数 ----------

def detect_red_flags(project: Dict, readme_content: str = "", repo_details: Dict = None) -> List[Dict]:
    """
    检测红旗项（Red Flags）
    参考真实安全事件：JetBrains 恶意插件（2026.06，硬编码IP+TLS降级）、WordPress恶意插件研究
    返回检测到的红旗列表，每项含 type / severity / detail
    """
    flags = []
    platform_data = project.get("_platform_data", {})

    # 1. 无许可证
    license_name = platform_data.get("license", "")
    if not license_name and repo_details:
        # get_repo_details 返回 license 为字符串
        license_obj = repo_details.get("license")
        if isinstance(license_obj, dict):
            license_name = license_obj.get("spdx_id", "") or license_obj.get("name", "")
        elif isinstance(license_obj, str) and license_obj and license_obj != "None":
            license_name = license_obj
    if not license_name:
        flags.append({
            "type": "no_license",
            "severity": "high",
            "detail": "未声明许可证，使用存在法律风险",
        })

    # 2. 检查 README 中的红旗模式
    if readme_content:
        # 硬编码 IP（排除 localhost / 内网段）
        ip_matches = _REDFLAG_PATTERNS["hardcoded_ip"].findall(readme_content)
        suspicious_ips = [
            ip for ip in ip_matches
            if ip not in ("127.0.0.1", "0.0.0.0")
            and not ip.startswith(("192.168.", "10.", "172."))
        ]
        if suspicious_ips:
            flags.append({
                "type": "hardcoded_ip",
                "severity": "critical",
                "detail": f"发现硬编码公网 IP: {', '.join(suspicious_ips[:3])}",
            })

        # 不安全 HTTP 传输
        http_matches = _REDFLAG_PATTERNS["http_insecure"].findall(readme_content)
        if http_matches:
            flags.append({
                "type": "http_insecure",
                "severity": "high",
                "detail": f"发现非加密 HTTP 传输: {len(http_matches)} 处",
            })

        # API Key 硬编码
        apikey_matches = _REDFLAG_PATTERNS["apikey_exposed"].findall(readme_content)
        if apikey_matches:
            flags.append({
                "type": "apikey_exposed",
                "severity": "critical",
                "detail": f"发现疑似硬编码 API Key/Token: {len(apikey_matches)} 处",
            })

    # 3. 无公开源码
    html_url = project.get("html_url", "")
    if not html_url or ("github.com" not in html_url and not html_url.startswith("http")):
        flags.append({
            "type": "no_source_code",
            "severity": "high",
            "detail": "无公开源码链接，无法进行安全审查",
        })

    # 4. 未验证来源
    if platform_data.get("verified") is False:
        flags.append({
            "type": "unverified_source",
            "severity": "medium",
            "detail": "来源未经平台验证",
        })

    return flags


# --- 源码级安全扫描（v4.1.0） ---
# 针对小型项目直接扫描代码文件，检测可疑 API 和脚本

_CODE_REDFLAG_PATTERNS = {
    "eval_exec": re.compile(
        r'\b(?:eval|exec)\s*\(\s*(?:input|request|os\.environ|sys\.argv|base64|compile|open)',
        re.IGNORECASE
    ),
    "obfuscated_base64": re.compile(
        r'base64\.b64decode\s*\(\s*["\'][A-Za-z0-9+/=]{50,}["\']'
    ),
    "subprocess_shell": re.compile(
        r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
        re.IGNORECASE
    ),
    "os_system": re.compile(r'os\.system\s*\(', re.IGNORECASE),
    "sensitive_path": re.compile(
        r'(?:/etc/(?:passwd|shadow)|/root/\.ssh|C:\\Windows\\System32|\.aws/credentials|\.ssh/id_rsa)',
        re.IGNORECASE
    ),
    "data_exfil": re.compile(
        r'(?:curl|wget)\s+(?:-[A-Za-z]+\s+)?(?:--data|--form|-d\s)\s*.+(?:http|https)://(?!localhost|127\.0\.0\.1)',
        re.IGNORECASE
    ),
    "import_injection": re.compile(
        r'(?:__import__|importlib\.import_module)\s*\(\s*(?:input|request|base64|eval|os\.environ)',
        re.IGNORECASE
    ),
    "tls_downgrade": re.compile(
        r'(?:X509TrustManager|SSLContext|verify\s*=\s*False|CERT_NONE|trust_all)',
        re.IGNORECASE
    ),
    "env_harvest": re.compile(
        r'os\.environ(?:\.get\(|\[)["\'](?:API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY|AWS_|OPENAI_|ANTHROPIC)',
        re.IGNORECASE
    ),
}

# 源码扫描的文件扩展名
_SCAN_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".rb", ".go", ".java", ".mjs", ".cjs"}


def scan_source_code(repo_name: str, max_files: int = 15) -> List[Dict]:
    """
    对小型项目进行源码级安全扫描（v4.1.0）
    下载关键代码文件并扫描可疑 API 调用和脚本模式

    策略：
    - 获取仓库文件树，仅扫描代码文件
    - 文件数 > 100 时跳过（大项目不适合快速扫描）
    - 最多扫描 max_files 个文件
    - 返回检测到的红旗项列表

    参考安全事件：
    - JetBrains 恶意插件（TLS降级+硬编码IP+API Key窃取）
    - WordPress 恶意插件研究（47,337个恶意插件，USENIX Security 2022）
    """
    flags = []

    # 获取仓库文件树（先尝试 main，再尝试 master）
    tree_data = github_api_request(f"/repos/{repo_name}/git/trees/main?recursive=1")
    if "error" in tree_data or "tree" not in tree_data:
        tree_data = github_api_request(f"/repos/{repo_name}/git/trees/master?recursive=1")
        if "error" in tree_data or "tree" not in tree_data:
            return []

    # 筛选代码文件
    code_files = [
        f for f in tree_data["tree"]
        if f.get("type") == "blob" and any(
            f["path"].endswith(ext) for ext in _SCAN_EXTENSIONS
        )
    ]

    # 大项目跳过源码扫描
    if len(code_files) > 100:
        return [{
            "type": "scan_skipped",
            "severity": "info",
            "detail": f"项目较大（{len(code_files)}个代码文件），跳过源码扫描"
        }]

    scanned = 0
    for file_info in code_files[:max_files]:
        path = file_info["path"]
        # 获取文件内容
        content_data = github_api_request(f"/repos/{repo_name}/contents/{path}")
        if "error" in content_data or "content" not in content_data:
            continue

        try:
            content = base64.b64decode(content_data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            continue

        scanned += 1

        # 检查源码级红旗模式
        for flag_type, pattern in _CODE_REDFLAG_PATTERNS.items():
            matches = pattern.findall(content)
            if matches:
                if flag_type in ("eval_exec", "obfuscated_base64", "import_injection", "tls_downgrade", "env_harvest"):
                    severity = "critical"
                elif flag_type in ("subprocess_shell", "os_system", "data_exfil", "sensitive_path"):
                    severity = "high"
                else:
                    severity = "medium"
                flags.append({
                    "type": f"code_{flag_type}",
                    "severity": severity,
                    "detail": f"{path}: 检测到 {flag_type} ({len(matches)}处)",
                })

        # 也应用基础红旗模式到源码
        ip_matches = _REDFLAG_PATTERNS["hardcoded_ip"].findall(content)
        suspicious_ips = [
            ip for ip in ip_matches
            if ip not in ("127.0.0.1", "0.0.0.0")
            and not ip.startswith(("192.168.", "10.", "172."))
        ]
        if suspicious_ips:
            flags.append({
                "type": "code_hardcoded_ip",
                "severity": "critical",
                "detail": f"{path}: 源码中发现硬编码公网 IP: {', '.join(suspicious_ips[:3])}",
            })

        http_matches = _REDFLAG_PATTERNS["http_insecure"].findall(content)
        if http_matches:
            flags.append({
                "type": "code_http_insecure",
                "severity": "high",
                "detail": f"{path}: 源码中使用非加密 HTTP: {len(http_matches)}处",
            })

        apikey_matches = _REDFLAG_PATTERNS["apikey_exposed"].findall(content)
        if apikey_matches:
            flags.append({
                "type": "code_apikey_exposed",
                "severity": "critical",
                "detail": f"{path}: 源码中发现疑似硬编码 API Key/Token: {len(apikey_matches)}处",
            })

    return flags


def assess_safety(project: Dict, repo_details: Dict = None) -> Dict:
    """
    6维度安全评估体系

    维度与权重：
    1. 代码透明度 (30%) - 源码是否公开可审查
    2. 来源可信度 (25%) - 是否来自已知组织/验证发布者
    3. 维护活跃度 (15%) - 最近更新时间
    4. 社区采纳度 (15%) - Star/下载量
    5. 权限透明度 (10%) - 许可证与权限声明
    6. 安全记录 (5%)  - 已知安全事件

    Red Flag 降级规则：
    - 检测到 critical 级红旗 → 总分上限 25
    - 检测到 2+ high 级红旗 → 总分上限 40
    - 检测到 1 high 级红旗 → 总分上限 55

    风险等级：
    - 🟢 低风险 (80-100): 可安全使用
    - 🟡 中风险 (60-79): 建议审查后使用
    - 🟠 高风险 (30-59): 需仔细审查
    - 🔴 极高风险 (0-29): 不建议使用
    """
    dimensions = {}
    platform_data = project.get("_platform_data", {})
    repo_name = project.get("repo_name", "")
    has_github = "github.com" in project.get("html_url", "")

    # --- 1. 代码透明度 (30%) ---
    if has_github and repo_name:
        dimensions["code_transparency"] = {
            "score": 90,
            "detail": "源码托管在 GitHub，可公开审查",
        }
    elif project.get("html_url"):
        dimensions["code_transparency"] = {
            "score": 45,
            "detail": "有项目链接但源码可能不完全公开",
        }
    else:
        dimensions["code_transparency"] = {
            "score": 15,
            "detail": "无公开源码链接，无法审查代码",
        }

    # --- 2. 来源可信度 (25%) ---
    verified = platform_data.get("verified", False)
    if verified:
        dimensions["source_credibility"] = {
            "score": 90,
            "detail": "平台验证来源",
        }
    elif has_github and repo_details:
        owner_type = repo_details.get("owner_type", "")
        owner_login = repo_details.get("owner_login", "")
        if owner_type == "Organization":
            dimensions["source_credibility"] = {
                "score": 75,
                "detail": f"来自 GitHub 组织 ({owner_login})",
            }
        else:
            dimensions["source_credibility"] = {
                "score": 55,
                "detail": f"来自 GitHub 个人账户 ({owner_login})",
            }
    elif has_github:
        dimensions["source_credibility"] = {
            "score": 50,
            "detail": "来自 GitHub 但未经平台验证",
        }
    else:
        dimensions["source_credibility"] = {
            "score": 25,
            "detail": "来源未经验证，建议谨慎",
        }

    # --- 3. 维护活跃度 (15%) ---
    if repo_details and repo_details.get("pushed_at"):
        try:
            update_date = datetime.fromisoformat(
                repo_details["pushed_at"].replace("Z", "+00:00")
            )
            days_since = (datetime.now(update_date.tzinfo) - update_date).days
            if days_since <= 30:
                score, detail = 90, f"最近 {days_since} 天内有更新"
            elif days_since <= 90:
                score, detail = 75, f"最近 {days_since} 天内有更新"
            elif days_since <= 180:
                score, detail = 55, f"已 {days_since} 天未更新"
            elif days_since <= 365:
                score, detail = 35, f"已 {days_since} 天未更新，维护可能停滞"
            else:
                score, detail = 15, f"已 {days_since} 天未更新，维护可能已停止"
            dimensions["maintenance"] = {"score": score, "detail": detail}
        except Exception:
            dimensions["maintenance"] = {"score": 50, "detail": "无法确定更新时间"}
    elif project.get("last_update"):
        dimensions["maintenance"] = {
            "score": 60,
            "detail": f"最后更新: {project['last_update']}",
        }
    else:
        dimensions["maintenance"] = {"score": 40, "detail": "无维护信息"}

    # --- 4. 社区采纳度 (15%) ---
    star_count = project.get("star_count", 0)
    downloads = platform_data.get("downloads", 0)

    if star_count or downloads:
        if star_count >= 10000:
            score = 95
        elif star_count >= 5000:
            score = 85
        elif star_count >= 1000:
            score = 75
        elif star_count >= 100:
            score = 60
        elif downloads >= 10000:
            score = 70
        elif downloads >= 1000:
            score = 55
        else:
            score = 35
        parts = []
        if star_count:
            parts.append(f"⭐{star_count}")
        if downloads:
            parts.append(f"⬇{downloads}")
        dimensions["community_adoption"] = {
            "score": score,
            "detail": " / ".join(parts),
        }
    else:
        dimensions["community_adoption"] = {
            "score": 30,
            "detail": "无社区采纳数据",
        }

    # --- 5. 权限透明度 (10%) ---
    license_name = platform_data.get("license", "")
    if not license_name and repo_details:
        license_obj = repo_details.get("license")
        if isinstance(license_obj, dict):
            license_name = license_obj.get("spdx_id", "") or license_obj.get("name", "")
        elif isinstance(license_obj, str) and license_obj and license_obj != "None":
            license_name = license_obj
    if license_name:
        license_info = _classify_license(license_name)
        dimensions["permission_transparency"] = {
            "score": license_info["score"],
            "detail": license_info["assessment"],
        }
    elif project.get("agent_integration") == "MCP":
        dimensions["permission_transparency"] = {
            "score": 60,
            "detail": "MCP 协议有标准权限模型，需检查具体实现",
        }
    else:
        dimensions["permission_transparency"] = {
            "score": 30,
            "detail": "权限需求不明确",
        }

    # --- 6. 安全记录 (5%) ---
    # 默认假设无已知问题（需外部安全数据库才能更准确）
    dimensions["security_record"] = {
        "score": 70,
        "detail": "未检测到已知安全事件（基于公开信息）",
    }

    # --- 计算加权总分 ---
    total_score = 0
    for dim, weight in _SAFETY_WEIGHTS.items():
        if dim in dimensions:
            total_score += dimensions[dim]["score"] * weight
    total_score = round(total_score)

    # --- 检测红旗项 ---
    red_flags = detect_red_flags(project, repo_details=repo_details)

    # --- 红旗项降级 ---
    if red_flags:
        critical_count = sum(1 for f in red_flags if f["severity"] == "critical")
        high_count = sum(1 for f in red_flags if f["severity"] == "high")
        if critical_count > 0:
            total_score = min(total_score, 25)
        elif high_count >= 2:
            total_score = min(total_score, 40)
        elif high_count >= 1:
            total_score = min(total_score, 55)

    # --- 风险等级 ---
    if total_score >= 80:
        risk_level, risk_badge, risk_label = "low", "🟢", "低风险"
    elif total_score >= 60:
        risk_level, risk_badge, risk_label = "medium", "🟡", "中风险"
    elif total_score >= 30:
        risk_level, risk_badge, risk_label = "high", "🟠", "高风险"
    else:
        risk_level, risk_badge, risk_label = "critical", "🔴", "极高风险"

    return {
        "safety_score": total_score,
        "risk_level": risk_level,
        "risk_badge": risk_badge,
        "risk_label": risk_label,
        "dimensions": dimensions,
        "red_flags": red_flags,
    }


def _safety_summary(safety: Dict) -> str:
    """生成紧凑安全摘要（用于搜索结果列表）"""
    badge = safety.get("risk_badge", "❓")
    score = safety.get("safety_score", 0)
    label = safety.get("risk_label", "未知")
    flags = safety.get("red_flags", [])
    flag_str = f" ⚠{len(flags)}红旗" if flags else ""
    return f"{badge} 安全{score}({label}){flag_str}"



# ============ 综合搜索（扩展） ============

def search_all_sources(query: str, language: str = None, no_api: bool = False, region: str = "all") -> Dict:
    """
    综合搜索：本地库 + GitHub API
    注意：不自动调用 Trending，Trending 是独立命令

    v3.4.0: 支持 no_api=True 强制纯本地模式；无 Token 时自动降级
    v4.2.0: 支持 region 参数过滤国内外项目
    """
    results = {
        "query": query,
        "language": language,
        "region_filter": region,
        "local_results": [],
        "github_results": [],
        "merged": [],
        "api_available": not no_api,
        "token_mode": "authenticated" if _has_github_token() else "unauthenticated",
    }

    # 1. 本地库搜索
    results["local_results"] = search_local_db(query, language=language)

    # 2. GitHub API 搜索（未强制禁用 API 时执行）
    # v4.3.0: 无 Token 时走未认证模式（60次/小时），不再完全跳过
    if results["api_available"]:
        results["github_results"] = search_github_with_fallback(query, language)
    else:
        results["github_results"] = [{"info": "no_api 模式，仅展示本地库结果"}]

    # 3. 合并去重（本地库优先）
    seen = set()
    merged = []

    for project in results["local_results"]:
        key = project.get("repo_name", "")
        if key and key not in seen:
            seen.add(key)
            merged.append(project)

    for project in results["github_results"]:
        if "error" in project:
            continue
        key = project.get("repo_name", "")
        if key and key not in seen:
            seen.add(key)
            merged.append(project)

    # v4.2.0: 区域适用性检测与过滤
    for proj in merged:
        proj["region"] = _detect_region(proj)
    if region and region != "all":
        merged = _filter_by_region(merged, region)

    # 排序：已验证优先，然后按 star 数
    # 注意：本地库项目如果没有 star_count，用 0 占位，靠 verified=True 排在前面
    merged.sort(key=lambda x: (
        not x.get("verified", False),
        x.get("star_count", 0)
    ), reverse=True)

    results["merged"] = merged[:20]
    return results


# ============ 学习导向搜索 ============

def build_learning_query(query: str, language: str = None, mode: str = "rewrite") -> str:
    """
    构建学习导向的 GitHub 搜索查询

    mode:
    - rewrite: 换语言重写 → 简单小型项目，低 star 门槛
    - contribute: 参与贡献 → 有 good-first-issue 的活跃项目
    """
    expanded = expand_keywords(query)
    parts = [f"{expanded} in:name,description,readme"]

    if language:
        parts.append(f"language:{language}")

    if mode == "rewrite":
        # 重写模式：低 star 门槛，找简单项目
        parts.append("stars:>=50")
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        parts.append(f"pushed:>{six_months_ago}")
        parts.append("archived:false")
    else:
        # 贡献模式：标准门槛 + good-first-issue topic
        parts.append("stars:>=500")
        parts.append("topic:good-first-issue")
        parts.append("archived:false")
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        parts.append(f"pushed:>{one_year_ago}")

    return " ".join(parts)


def search_learning(query: str, mode: str = "rewrite", language: str = None) -> Dict:
    """
    学习导向搜索：查找适合学习、重写或贡献的项目

    两种模式：
    - rewrite（换语言重写）：优先小型、单语言项目，可移植性 > 完整性
    - contribute（参与贡献）：优先有 good-first-issue 的活跃项目

    评分逻辑：
    - rewrite: 语言数越少越好，主语言占比越高越好，代码量越小越好
    - contribute: good-first-issue + open_issues 多 + 活跃维护

    v3.4.0: 无 Token 时仅返回本地库结果，不崩溃
    """
    results = {
        "query": query,
        "mode": mode,
        "language": language,
        "local_results": [],
        "github_results": [],
        "merged": [],
        "api_available": True,
        "token_mode": "authenticated" if _has_github_token() else "unauthenticated",
    }

    # 1. 本地库搜索
    results["local_results"] = search_local_db(query, language=language)

    # 2. GitHub API 学习模式搜索
    # v4.3.0: 无 Token 时走未认证模式（60次/小时），不再完全跳过
    if mode not in ("rewrite", "contribute"):
        results["github_results"] = [{"info": "未知学习模式，仅展示本地库结果"}]
    else:
        search_q = build_learning_query(query, language, mode)

        if mode == "rewrite":
            sort_by = "stars"  # 简单项目也有一定社区认可
        else:
            sort_by = "updated"  # 贡献模式优先看最近活跃的

        params = {"q": search_q, "sort": sort_by, "order": "desc", "per_page": 20}
        data = github_api_request("/search/repositories", params)

        if "items" in data:
            for item in data["items"]:
                project = {
                    "repo_name": item["full_name"],
                    "display_name": item["name"],
                    "about": item.get("description", ""),
                    "tags": item.get("topics", []),
                    "star_count": item["stargazers_count"],
                    "language": item.get("language", ""),
                    "status": "archived" if item.get("archived") else "active",
                    "created_at": item["created_at"][:10] if item.get("created_at") else None,
                    "last_update": item["pushed_at"][:10] if item.get("pushed_at") else None,
                    "forks_count": item.get("forks_count", 0),
                    "open_issues": item.get("open_issues_count", 0),
                    "size_kb": item.get("size", 0),
                    "homepage": item.get("homepage", ""),
                    "has_wiki": item.get("has_wiki", False),
                    "verified": False,
                    "_source": "github_learning",
                }

                # 计算学习评分
                if mode == "rewrite":
                    # 简单性评分：fork 少 + star 适中（不太大）+ 有 wiki/描述
                    forks = item.get("forks_count", 0)
                    stars = item["stargazers_count"]
                    has_desc = 1 if item.get("description") else 0
                    has_wiki = 1 if item.get("has_wiki") else 0

                    # 越小的项目越适合重写（fork和star都不太高，但有基本文档）
                    simplicity = 0
                    if forks < 100:
                        simplicity += 2
                    elif forks < 500:
                        simplicity += 1
                    if 50 <= stars < 5000:
                        simplicity += 2  # 适中规模
                    elif stars >= 5000:
                        simplicity += 1  # 大项目重写困难
                    simplicity += has_desc + has_wiki
                    project["_learning_score"] = simplicity
                    project["_learning_note"] = f"forks:{forks}, stars:{stars}, 文档:{has_desc+has_wiki}/2"
                else:
                    # 贡献友好度评分
                    has_gfi = "good-first-issue" in item.get("topics", [])
                    open_issues = item.get("open_issues_count", 0)
                    has_wiki = 1 if item.get("has_wiki") else 0

                    contrib_score = 0
                    if has_gfi:
                        contrib_score += 3
                    if open_issues > 50:
                        contrib_score += 2
                    elif open_issues > 10:
                        contrib_score += 1
                    contrib_score += has_wiki
                    project["_learning_score"] = contrib_score
                    project["_learning_note"] = f"good-first-issue:{has_gfi}, open_issues:{open_issues}"

                results["github_results"].append(project)

    # 3. 合并去重
    seen = set()
    merged = []

    for project in results["local_results"]:
        key = project.get("repo_name", "")
        if key and key not in seen:
            seen.add(key)
            # 本地库项目没有学习评分，给默认值
            project["_learning_score"] = 3
            project["_learning_note"] = "本地精选项目"
            merged.append(project)

    for project in results["github_results"]:
        if "error" in project:
            continue
        key = project.get("repo_name", "")
        if key and key not in seen:
            seen.add(key)
            merged.append(project)

    # 学习模式按 learning_score 排序（高分优先）
    merged.sort(key=lambda x: x.get("_learning_score", 0), reverse=True)

    results["merged"] = merged[:15]
    return results


# ============ 6. CLI 入口 ============

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python main.py <命令> [参数]")
        print("")
        print("命令:")
        print("  search <关键词> [语言]     - 综合搜索（本地库 + GitHub API）")
        print("  local <关键词> [语言]      - 仅搜索本地库")
        print("  github <关键词> [语言]     - 仅搜索 GitHub API")
        print("  trending [语言]            - 采集 Trending（独立命令）")
        print("  hellogithub <关键词> [期数] - 搜索 HelloGitHub 社区精选")
        print("  ruanyf <关键词> [期数]      - 搜索阮一峰周刊项目推荐")
        print("  awesome <关键词> [语言]    - 搜索 Awesome 列表")
        print("  agent <关键词> [模式]      - 搜索智能体技能/工具")
        print("    模式: all(默认) / skill(仅技能) / standalone(可独立使用) / integrate(可接入agent) / safe(仅安全)")
        print("  learning <模式> <关键词> [语言] - 学习导向搜索")
        print("  details <owner/repo>       - 查询项目详情")
        print("  analyze <owner/repo>       - 综合分析项目")
        print("  readme <owner/repo>        - 获取 README")
        print("  db-stats                   - 查看本地库统计和领域覆盖")
        print("  discover [标签]             - 按标签浏览本地库项目")
        print("  trust <owner/repo>         - 项目信任评估（Star质量/许可证/维护者/依赖安全）")
        print("")
        print("  --no-api                  - 强制纯本地模式（不调用 GitHub API）")
        print("  --region cn|global|all    - 区域过滤（v4.2.0）")
        print("    cn: 仅国内适用项目（国内用户无VPN时推荐）")
        print("    global: 仅国际适用项目")
        print("    all: 不过滤（默认）")
        print("")
        print("学习模式 (learning):")
        print("  rewrite    - 找简单项目换语言重写（可移植性优先）")
        print("  contribute - 找有 good-first-issue 的项目参与贡献")
        print("")
        print("示例:")
        print('  python main.py search "量化交易" python')
        print('  python main.py search "量化交易" python --no-api')
        print('  python main.py learning rewrite "Python的Web框架" python')
        print('  python main.py learning contribute "web framework" python')
        print('  python main.py hellogithub "推理引擎" 10')
        print('  python main.py ruanyf "截图工具" 10')
        print('  python main.py awesome "machine-learning" python')
        print('  python main.py agent "MCP server"')
        print('  python main.py agent "code review" skill')
        print('  python main.py agent "data analysis" standalone')
        print('  python main.py agent "MCP server" safe')
        print('  python main.py agent "code review" --region cn')
        print('  python main.py search "量化交易" python --region cn')
        print('  python main.py db-stats')
        print('  python main.py discover AI')
        print('  python main.py details vnpy/vnpy')
        print('  python main.py analyze langchain-ai/langchain')
        sys.exit(1)

    # 检测 --no-api 全局标志
    no_api = "--no-api" in sys.argv
    if no_api:
        sys.argv.remove("--no-api")

    # 检测 --region 全局标志（v4.2.0）
    region = "all"
    _i = 0
    while _i < len(sys.argv):
        if sys.argv[_i] == "--region" and _i + 1 < len(sys.argv):
            region = sys.argv[_i + 1]
            sys.argv.pop(_i)
            sys.argv.pop(_i)
            break
        elif sys.argv[_i].startswith("--region="):
            region = sys.argv[_i].split("=", 1)[1]
            sys.argv.pop(_i)
            break
        _i += 1

    command = sys.argv[1]

    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_all_sources(query, language, no_api=no_api, region=region)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "local":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_local_db(query, language=language)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "github":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_github_with_fallback(query, language)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "trending":
        language = sys.argv[2] if len(sys.argv) > 2 else None
        results = fetch_trending("weekly", language)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "hellogithub":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        issues = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        results = search_hellogithub(query, issues=issues)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "ruanyf":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        issues = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        results = search_ruanyf(query, issues=issues)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "awesome":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        language = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_awesome(query, language=language)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "agent":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        mode = sys.argv[3] if len(sys.argv) > 3 else "all"
        if mode not in ("all", "skill", "standalone", "integrate", "safe"):
            query = f"{query} {mode}".strip()
            mode = "all"
        results = search_agent(query, mode=mode, region=region)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "learning":
        mode = sys.argv[2] if len(sys.argv) > 2 else "rewrite"
        if mode not in ("rewrite", "contribute"):
            # 第一个参数不是模式，当作关键词处理，默认 rewrite
            query = mode
            mode = "rewrite"
            language = sys.argv[3] if len(sys.argv) > 3 else None
        else:
            query = sys.argv[3] if len(sys.argv) > 3 else ""
            language = sys.argv[4] if len(sys.argv) > 4 else None
        results = search_learning(query, mode=mode, language=language)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "details":
        repo = sys.argv[2] if len(sys.argv) > 2 else ""
        results = get_repo_details(repo)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "analyze":
        repo = sys.argv[2] if len(sys.argv) > 2 else ""
        results = analyze_project(repo)
        # v3.6.0: analyze 自动附带信任评估
        if "error" not in results:
            trust = trust_assessment(repo)
            if "error" not in trust:
                results["trust_assessment"] = {
                    "trust_score": trust["trust_score"],
                    "trust_badge": trust["trust_badge"],
                    "checks": trust["checks"],
                    "warnings": trust["warnings"],
                    "highlights": trust["highlights"],
                }
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "readme":
        repo = sys.argv[2] if len(sys.argv) > 2 else ""
        results = get_readme_content(repo)
        print(results)

    elif command == "db-stats":
        results = db_stats()
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "discover":
        tag = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        results = discover(tag=tag, limit=limit)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "trust":
        repo = sys.argv[2] if len(sys.argv) > 2 else ""
        if not repo:
            print("用法: python main.py trust <owner/repo>")
            print("示例: python main.py trust m-ahmed-elbeskeri/Starguard")
            sys.exit(1)
        results = trust_assessment(repo)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif command == "docs":
        repo = sys.argv[2] if len(sys.argv) > 2 else ""
        if not repo:
            print("用法: python main.py docs <owner/repo>")
            print("示例: python main.py docs microsoft/vscode")
            sys.exit(1)
        results = generate_docs(repo)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
