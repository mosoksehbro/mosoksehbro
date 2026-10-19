#!/usr/bin/env python3
import os
import sys
import json
import urllib.request

TOKEN = os.getenv("METRICS_TOKEN") or os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("Error: No METRICS_TOKEN or GITHUB_TOKEN environment variable found.")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"

# GitHub language colors fallback
LANG_COLORS = {
    "Go": "#00ADD8",
    "PHP": "#4F5D95",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "Python": "#3572A5",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Rust": "#DEA584",
    "Java": "#B07219",
    "C": "#555555",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Ruby": "#701516",
    "Dart": "#00B4AB",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Shell": "#89E051",
    "Vue": "#41B883",
    "Dockerfile": "#384D54",
    "SQL": "#E38C00"
}

IGNORED_LANGUAGES = {"Blade", "HTML", "CSS", "Smarty"}

QUERY = """
query($cursor: String) {
  viewer {
    repositories(first: 100, after: $cursor, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        isFork
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
"""

def fetch_all_languages():
    languages_total = {}
    lang_color_map = {}
    has_next = True
    cursor = None
    total_repos = 0

    while has_next:
        variables = {"cursor": cursor}
        payload = json.dumps({"query": QUERY, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(
            GRAPHQL_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "mosoksehbro-metrics"
            }
        )

        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode("utf-8"))

        if "errors" in result:
            print("GraphQL errors:", result["errors"])
            break

        data = result.get("data", {}).get("viewer", {}).get("repositories", {})
        nodes = data.get("nodes", [])
        total_repos += len(nodes)

        for repo in nodes:
            # We skip forks to measure only your original/collaborated code
            if repo.get("isFork"):
                continue

            lang_edges = repo.get("languages", {}).get("edges", [])
            for edge in lang_edges:
                name = edge["node"]["name"]
                size = edge["size"]
                color = edge["node"].get("color")

                if name in IGNORED_LANGUAGES:
                    continue

                languages_total[name] = languages_total.get(name, 0) + size
                if color and name not in lang_color_map:
                    lang_color_map[name] = color

        page_info = data.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

    print(f"Scanned {total_repos} repositories across public, private, and collaborated.")
    return languages_total, lang_color_map

def generate_svg(languages_pct, lang_color_map):
    # Tokyo night theme colors
    bg_color = "#1a1b27"
    title_color = "#7aa2f7"
    text_color = "#c0caf5"

    width = 340
    # Dynamic height based on number of languages
    items_to_show = languages_pct[:6]
    height = 55 + (len(items_to_show) * 40) + 15

    svg_items = []
    y_offset = 0

    for idx, (lang, data) in enumerate(items_to_show):
        color = lang_color_map.get(lang) or LANG_COLORS.get(lang) or "#7aa2f7"
        pct_str = f"{data['percentage']:.2f}%"
        width_bar = max(4, int(205 * (data['percentage'] / 100)))

        item_svg = f"""
    <g transform="translate(0, {y_offset})">
      <text x="2" y="15" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11px" font-weight="500">{lang}</text>
      <text x="225" y="34" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11px" font-weight="400">{pct_str}</text>
      <svg width="205" x="0" y="25">
        <rect rx="4" ry="4" x="0" y="0" width="205" height="7" fill="#24283b" />
        <rect rx="4" ry="4" x="0" y="0" width="{width_bar}" height="7" fill="{color}" />
      </svg>
    </g>"""
        svg_items.append(item_svg)
        y_offset += 40

    all_items_str = "\n".join(svg_items)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">
  <rect x="0.5" y="0.5" rx="5" ry="5" width="{width - 1}" height="{height - 1}" fill="{bg_color}" />
  <g transform="translate(25, 35)">
    <text x="0" y="0" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="16px" font-weight="700">Most Used Languages</text>
  </g>
  <g transform="translate(25, 50)">
{all_items_str}
  </g>
</svg>"""
    return svg_content

def main():
    totals, colors = fetch_all_languages()
    total_bytes = sum(totals.values())

    if total_bytes == 0:
        print("No language data found.")
        sys.exit(0)

    # Calculate percentages
    sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    lang_data = []
    output_json = {
        "total_bytes": total_bytes,
        "languages": []
    }

    for lang, byte_count in sorted_langs:
        pct = (byte_count / total_bytes) * 100
        output_json["languages"].append({
            "name": lang,
            "bytes": byte_count,
            "percentage": round(pct, 2),
            "color": colors.get(lang) or LANG_COLORS.get(lang) or "#7aa2f7"
        })
        lang_data.append((lang, {"bytes": byte_count, "percentage": pct}))

    # 1. Save JSON
    with open("languages.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    print("Saved languages.json")

    # 2. Generate and save SVG
    svg_output = generate_svg(lang_data, colors)
    with open("languages.svg", "w", encoding="utf-8") as f:
        f.write(svg_output)
    print("Saved languages.svg")

if __name__ == "__main__":
    main()
