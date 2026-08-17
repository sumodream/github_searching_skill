#!/usr/bin/env python3
"""
雷达图对比生成器 — 格式F
接收项目数据 JSON，生成独立 HTML 文件（内嵌 SVG 雷达图）。
无外部依赖，纯 Python + SVG。

用法:
  python scripts/radar_chart.py --data '<json>' --output /path/to/output.html
  python scripts/radar_chart.py --data-file /path/to/data.json --output /path/to/output.html

输入 JSON 格式:
[
  {
    "display_name": "项目名",
    "repo_name": "owner/repo",
    "star_count": 33000,
    "age_days": 4100,
    "star_per_day": 8.05,
    "status": "active",
    "last_update": "2026-06-10",
    "docker_support": true,
    "install_methods": ["pip", "docker"],
    "tags": ["金融", "量化交易", "python库"],
    "scene": "适用场景描述",
    "learning_cost": "低",
    "has_wiki": false,
    "about": "项目简介..."
  },
  ...
]
"""

import json
import math
import os
import sys
import argparse
from datetime import datetime, timezone


# ── 评分维度计算 ──────────────────────────────────────────────

def score_community(star_count, star_per_day, last_update_str):
    """社区活跃度 (0-10): stars + 增速 + 更新频率"""
    s = 0
    # stars (log scale)
    if star_count and star_count > 0:
        s += min(4, math.log10(max(star_count, 1)) - 2)  # 1K=1, 10K=2, 100K=3, +cap
    # star_per_day
    if star_per_day and star_per_day > 0:
        if star_per_day > 20: s += 3
        elif star_per_day > 10: s += 2.5
        elif star_per_day > 5: s += 2
        elif star_per_day > 1: s += 1
        else: s += 0.5
    # last_update recency
    try:
        update_dt = datetime.strptime(last_update_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_ago = (datetime.now(timezone.utc) - update_dt).days
        if days_ago < 30: s += 3
        elif days_ago < 90: s += 2
        elif days_ago < 180: s += 1
        elif days_ago < 365: s += 0.5
    except (ValueError, TypeError):
        s += 1  # unknown, give average
    return round(min(10, max(0, s)), 1)


def score_features(tags, scene):
    """功能覆盖 (0-10): 标签数量 + 场景描述"""
    s = 0
    tag_count = len(tags) if tags else 0
    if tag_count >= 8: s += 5
    elif tag_count >= 5: s += 4
    elif tag_count >= 3: s += 3
    elif tag_count >= 1: s += 2
    if scene and len(scene) > 5: s += 3
    # description length bonus
    s += 2  # baseline
    return round(min(10, max(0, s)), 1)


def score_ease(learning_cost, docker_support, install_methods):
    """上手友好度 (0-10): 学习成本 + 安装便利"""
    s = 5  # baseline
    cost = (learning_cost or "").lower()
    if any(w in cost for w in ["低", "简单", "easy", "beginner", "low", "入门"]): s += 3
    elif any(w in cost for w in ["中", "moderate", "medium", "中等"]): s += 1
    elif any(w in cost for w in ["高", "难", "hard", "复杂", "difficult", "high", "advanced"]): s -= 2
    if docker_support: s += 1
    if install_methods and len(install_methods) >= 2: s += 1
    return round(min(10, max(0, s)), 1)


def score_docs(has_wiki, about, install_methods):
    """文档质量 (0-10): wiki + 描述完整度 + 安装说明"""
    s = 3  # baseline (README almost always exists)
    if has_wiki: s += 2
    if about and len(about) > 30: s += 2
    elif about and len(about) > 10: s += 1
    if install_methods and len(install_methods) > 0: s += 3
    return round(min(10, max(0, s)), 1)


def score_maintenance(status, last_update_str, star_per_day):
    """维护状态 (0-10): 活跃度 + 更新频率"""
    s = 0
    if status and status.lower() not in ("archived", "deprecated", "deleted"):
        s += 4
    try:
        update_dt = datetime.strptime(last_update_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_ago = (datetime.now(timezone.utc) - update_dt).days
        if days_ago < 30: s += 4
        elif days_ago < 90: s += 3
        elif days_ago < 180: s += 2
        elif days_ago < 365: s += 1
    except (ValueError, TypeError):
        s += 1
    if star_per_day and star_per_day > 5: s += 2
    elif star_per_day and star_per_day > 1: s += 1
    return round(min(10, max(0, s)), 1)


DIMENSIONS = [
    ("社区活跃度", "community"),
    ("功能覆盖", "features"),
    ("上手友好度", "ease"),
    ("文档质量", "docs"),
    ("维护状态", "maintenance"),
]


def compute_scores(project):
    """计算单个项目的五维评分"""
    return {
        "community": score_community(
            project.get("star_count", 0),
            project.get("star_per_day", 0),
            project.get("last_update", ""),
        ),
        "features": score_features(
            project.get("tags", []),
            project.get("scene", ""),
        ),
        "ease": score_ease(
            project.get("learning_cost", ""),
            project.get("docker_support", False),
            project.get("install_methods", []),
        ),
        "docs": score_docs(
            project.get("has_wiki", False),
            project.get("about", ""),
            project.get("install_methods", []),
        ),
        "maintenance": score_maintenance(
            project.get("status", ""),
            project.get("last_update", ""),
            project.get("star_per_day", 0),
        ),
    }


# ── SVG 生成 ──────────────────────────────────────────────

COLORS = [
    ("#4F8EF7", "#4F8EF733"),  # Blue
    ("#FF6B6B", "#FF6B6B33"),  # Red
    ("#51CF66", "#51CF6633"),  # Green
]

def _point_on_axis(cx, cy, radius, angle):
    """计算轴上某角度的点坐标"""
    return (cx + radius * math.cos(angle), cy + radius * math.sin(angle))


def generate_svg(projects_data, scores_list, width=600, height=560):
    """生成雷达图 SVG 字符串"""
    cx, cy = width / 2, height / 2 - 10
    max_r = min(width, height) / 2 - 80
    n = len(DIMENSIONS)
    angle_step = 2 * math.pi / n
    start_angle = -math.pi / 2  # 第一个轴朝上

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
                 f'style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;">')

    # Background
    lines.append(f'<rect width="{width}" height="{height}" fill="#FAFBFC" rx="12"/>')

    # Grid circles (0, 2, 4, 6, 8, 10)
    for level in range(1, 6):
        r = max_r * level / 5
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="#E5E7EB" stroke-width="0.8"/>')
        # Level label
        val = level * 2
        lx = cx + 5
        ly = cy - r + 3
        lines.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#9CA3AF" font-size="9">{val}</text>')

    # Axis lines + labels
    for i, (label, key) in enumerate(DIMENSIONS):
        angle = start_angle + i * angle_step
        ex, ey = _point_on_axis(cx, cy, max_r, angle)
        lines.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#D1D5DB" stroke-width="0.8"/>')
        # Label
        label_r = max_r + 30
        lx, ly = _point_on_axis(cx, cy, label_r, angle)
        anchor = "middle"
        if lx < cx - 10: anchor = "end"
        elif lx > cx + 10: anchor = "start"
        dy_offset = 4
        if ly < cy - 10: dy_offset = -4
        lines.append(f'<text x="{lx:.1f}" y="{ly + dy_offset:.1f}" text-anchor="{anchor}" '
                     f'fill="#374151" font-size="13" font-weight="500">{label}</text>')

    # Data polygons
    for pi, scores in enumerate(scores_list):
        stroke_color, fill_color = COLORS[pi % len(COLORS)]
        points = []
        for i, (label, key) in enumerate(DIMENSIONS):
            angle = start_angle + i * angle_step
            val = scores.get(key, 0)
            r = max_r * val / 10
            px, py = _point_on_axis(cx, cy, r, angle)
            points.append(f"{px:.1f},{py:.1f}")

        points_str = " ".join(points)
        lines.append(f'<polygon points="{points_str}" fill="{fill_color}" stroke="{stroke_color}" '
                     f'stroke-width="2" stroke-linejoin="round"/>')

        # Data point dots + value labels
        for i, (label, key) in enumerate(DIMENSIONS):
            angle = start_angle + i * angle_step
            val = scores.get(key, 0)
            r = max_r * val / 10
            px, py = _point_on_axis(cx, cy, r, angle)
            lines.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{stroke_color}"/>')
            # Value label offset
            offset_r = 12
            vlx, vly = _point_on_axis(cx, cy, r + offset_r, angle)
            lines.append(f'<text x="{vlx:.1f}" y="{vly + 3:.1f}" text-anchor="middle" '
                         f'fill="{stroke_color}" font-size="10" font-weight="600">{val:.1f}</text>')

    # Legend
    legend_y = height - 30
    legend_x_start = width / 2 - len(projects_data) * 80
    for pi, proj in enumerate(projects_data):
        stroke_color, _ = COLORS[pi % len(COLORS)]
        lx = legend_x_start + pi * 160
        name = proj.get("display_name", proj.get("repo_name", f"项目{pi+1}"))
        if len(name) > 15: name = name[:14] + "…"
        lines.append(f'<rect x="{lx:.1f}" y="{legend_y - 8}" width="12" height="12" rx="2" fill="{stroke_color}"/>')
        lines.append(f'<text x="{lx + 16:.1f}" y="{legend_y + 2}" fill="#374151" font-size="12">{name}</text>')

    lines.append('</svg>')
    return "\n".join(lines)


def generate_html(projects_data, scores_list):
    """生成完整 HTML 文件"""
    svg = generate_svg(projects_data, scores_list)

    # Score table
    table_rows = []
    for pi, proj in enumerate(projects_data):
        stroke_color, _ = COLORS[pi % len(COLORS)]
        name = proj.get("display_name", proj.get("repo_name", f"项目{pi+1}"))
        scores = scores_list[pi]
        row = f'<tr><td style="color:{stroke_color};font-weight:600">{name}</td>'
        for label, key in DIMENSIONS:
            val = scores.get(key, 0)
            bar_w = val * 10
            bar_color = "#4F8EF7" if val >= 7 else "#F59E0B" if val >= 4 else "#EF4444"
            row += (f'<td>'
                    f'<div style="display:flex;align-items:center;gap:6px">'
                    f'<div style="width:60px;height:6px;background:#E5E7EB;border-radius:3px;overflow:hidden">'
                    f'<div style="width:{bar_w}%;height:100%;background:{bar_color};border-radius:3px"></div>'
                    f'</div>'
                    f'<span style="font-size:12px;color:#6B7280">{val:.1f}</span>'
                    f'</div></td>')
        row += '</tr>'
        table_rows.append(row)

    table_header = '<tr><th style="text-align:left;padding:8px">项目</th>'
    for label, key in DIMENSIONS:
        table_header += f'<th style="padding:8px;font-size:12px">{label}</th>'
    table_header += '</tr>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>项目雷达图对比</title>
<style>
body {{ margin: 0; padding: 20px; background: #FAFBFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
.container {{ max-width: 700px; margin: 0 auto; }}
h2 {{ text-align: center; color: #1F2937; font-size: 18px; margin-bottom: 4px; }}
.subtitle {{ text-align: center; color: #9CA3AF; font-size: 12px; margin-bottom: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
th, td {{ border-bottom: 1px solid #E5E7EB; text-align: center; }}
th {{ color: #6B7280; font-weight: 500; }}
.note {{ text-align: center; color: #9CA3AF; font-size: 11px; margin-top: 16px; }}
</style>
</head>
<body>
<div class="container">
<h2>📊 项目雷达图对比</h2>
<p class="subtitle">评分基于 Star、更新频率、标签覆盖、学习成本、文档等维度自动计算</p>
<div style="text-align:center">{svg}</div>
<table>
<thead>{table_header}</thead>
<tbody>{"".join(table_rows)}</tbody>
</table>
<p class="note">数据来源: GitHub API + 本地精选库 · 评分仅供参考，0-10 分制</p>
</div>
</body>
</html>"""
    return html


# ── 主流程 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="生成项目雷达图对比 HTML")
    parser.add_argument("--data", type=str, help="项目数据 JSON 字符串")
    parser.add_argument("--data-file", type=str, help="项目数据 JSON 文件路径")
    parser.add_argument("--output", type=str, required=True, help="输出 HTML 文件路径")
    args = parser.parse_args()

    # 读取数据
    if args.data:
        projects = json.loads(args.data)
    elif args.data_file:
        with open(args.data_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
    else:
        print("错误: 必须提供 --data 或 --data-file", file=sys.stderr)
        sys.exit(1)

    if not projects or len(projects) < 2:
        print("错误: 至少需要 2 个项目才能生成雷达图", file=sys.stderr)
        sys.exit(1)

    if len(projects) > 3:
        projects = projects[:3]
        print("警告: 最多支持 3 个项目对比，已截取前 3 个", file=sys.stderr)

    # 计算评分
    scores_list = [compute_scores(p) for p in projects]

    # 生成 HTML
    html = generate_html(projects, scores_list)

    # 写入文件
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    # 输出评分摘要 JSON（给 Agent 读取）
    summary = {
        "output_file": args.output,
        "projects": [
            {
                "display_name": p.get("display_name", p.get("repo_name", "")),
                "scores": s,
            }
            for p, s in zip(projects, scores_list)
        ],
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
