#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
from datetime import datetime, date

TOKEN = os.getenv("METRICS_TOKEN") or os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("Error: No METRICS_TOKEN or GITHUB_TOKEN environment variable found.")
    sys.exit(1)

GRAPHQL_URL = "https://api.github.com/graphql"

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
    login
    name
    createdAt
    location
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
    repositories(first: 100, after: $cursor, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        isPrivate
        isFork
        owner {
          login
        }
        viewerPermission
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

def graphql_request(cursor=None):
    payload = json.dumps({"query": QUERY, "variables": {"cursor": cursor}}).encode("utf-8")
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
        return json.loads(res.read().decode("utf-8"))

def calculate_streak(weeks):
    all_days = []
    for week in weeks:
        for day in week.get("contributionDays", []):
            all_days.append({
                "date": day["date"],
                "count": day["contributionCount"]
            })
    
    # Sort by date
    all_days.sort(key=lambda d: d["date"])
    
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    today_str = date.today().isoformat()
    
    # Calculate longest streak
    for day in all_days:
        if day["count"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Calculate current streak backwards from today/yesterday
    # Reverse days
    rev_days = list(reversed(all_days))
    started = False
    for day in rev_days:
        if not started:
            # allow today to be 0 if today has no commits yet, check yesterday
            if day["date"] == today_str and day["count"] == 0:
                continue
            if day["count"] > 0:
                started = True
                current_streak += 1
            else:
                break
        else:
            if day["count"] > 0:
                current_streak += 1
            else:
                break
                
    return current_streak, max(longest_streak, current_streak)

def fetch_data():
    languages_total = {}
    lang_color_map = {}
    has_next = True
    cursor = None
    
    public_count = 0
    private_count = 0
    collab_count = 0
    
    user_info = {}
    weeks_data = []
    total_contributions = 0

    while has_next:
        result = graphql_request(cursor)
        if "errors" in result:
            print("GraphQL errors:", result["errors"])
            break

        viewer = result.get("data", {}).get("viewer", {})
        if not user_info:
            user_info = {
                "login": viewer.get("login"),
                "name": viewer.get("name") or viewer.get("login"),
                "createdAt": viewer.get("createdAt"),
                "location": viewer.get("location") or "Indonesia"
            }
            cal = viewer.get("contributionsCollection", {}).get("contributionCalendar", {})
            total_contributions = cal.get("totalContributions", 0)
            weeks_data = cal.get("weeks", [])

        repo_data = viewer.get("repositories", {})
        nodes = repo_data.get("nodes", [])

        for repo in nodes:
            if repo.get("isFork"):
                continue

            is_private = repo.get("isPrivate", False)
            owner = repo.get("owner", {}).get("login", "")
            
            # Categorize repo
            if owner.lower() == user_info["login"].lower():
                if is_private:
                    private_count += 1
                else:
                    public_count += 1
            else:
                collab_count += 1

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

        page_info = repo_data.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

    curr_streak, long_streak = calculate_streak(weeks_data)

    stats = {
        "user": user_info,
        "total_contributions": total_contributions,
        "current_streak": curr_streak,
        "longest_streak": long_streak,
        "public_repos": public_count,
        "private_repos": private_count,
        "collab_repos": collab_count,
        "languages": languages_total,
        "colors": lang_color_map
    }
    return stats

def generate_profile_card_svg(stats):
    user = stats["user"]
    total_contrib = stats["total_contributions"]
    pub = stats["public_repos"]
    priv = stats["private_repos"]
    collab = stats["collab_repos"]
    
    # Calculate account age
    created_year = 2021
    if user.get("createdAt"):
        created_year = int(user["createdAt"][:4])
    years_ago = max(1, datetime.now().year - created_year)

    width = 700
    height = 200
    bg = "#1a1b27"
    title_color = "#70a5fd"
    val_color = "#38bdae"
    icon_color = "#bf91f3"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">
  <rect x="1" y="1" rx="6" ry="6" width="{width - 2}" height="{height - 2}" fill="{bg}" stroke="#24283b" stroke-width="1" />
  
  <text x="32" y="42" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="20px" font-weight="700">{user['login']} ({user['name']})</text>
  
  <g transform="translate(32, 70)">
    <!-- Contributions -->
    <g transform="translate(0, 0)">
      <circle cx="6" cy="6" r="5" fill="{icon_color}" />
      <text x="22" y="10" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14px" font-weight="500">{total_contrib:,} Contributions in last year</text>
    </g>

    <!-- Repos detail: Public, Private, Collaborator -->
    <g transform="translate(0, 30)">
      <circle cx="6" cy="6" r="5" fill="{icon_color}" />
      <text x="22" y="10" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14px" font-weight="500">{pub} Public • {priv} Private • {collab} Collaborator Repos</text>
    </g>

    <!-- Joined age -->
    <g transform="translate(0, 60)">
      <circle cx="6" cy="6" r="5" fill="{icon_color}" />
      <text x="22" y="10" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14px" font-weight="500">Joined GitHub {years_ago} years ago</text>
    </g>

    <!-- Location -->
    <g transform="translate(0, 90)">
      <circle cx="6" cy="6" r="5" fill="{icon_color}" />
      <text x="22" y="10" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="14px" font-weight="500">{user['location']}</text>
    </g>
  </g>
  
  <!-- Right badge: Ecosystem Breakdown -->
  <g transform="translate(420, 35)">
    <rect width="245" height="135" rx="6" fill="#13141f" stroke="#24283b" stroke-width="1" />
    <text x="20" y="30" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px" font-weight="700">REPOSITORY ACCESS MATRIX</text>
    
    <text x="20" y="60" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px">Public Repositories</text>
    <text x="210" y="60" text-anchor="end" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px" font-weight="700">{pub}</text>

    <text x="20" y="85" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px">Private Repositories</text>
    <text x="210" y="85" text-anchor="end" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px" font-weight="700">{priv}</text>

    <text x="20" y="110" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px">Collaborator / Orgs</text>
    <text x="210" y="110" text-anchor="end" fill="{val_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="13px" font-weight="700">{collab}</text>
  </g>
</svg>"""

def generate_streak_svg(stats):
    total_contrib = stats["total_contributions"]
    curr = stats["current_streak"]
    longest = stats["longest_streak"]

    width = 370
    height = 200
    bg = "#1a1b27"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">
  <rect x="0.5" y="0.5" rx="5" ry="5" width="{width - 1}" height="{height - 1}" fill="{bg}" stroke="#24283b" stroke-width="1" />
  
  <text x="25" y="35" fill="#7aa2f7" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="16px" font-weight="700">Contribution Streak (Real)</text>
  
  <!-- Total -->
  <g transform="translate(60, 75)">
    <text x="0" y="25" text-anchor="middle" fill="#7aa2f7" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="24px" font-weight="700">{total_contrib:,}</text>
    <text x="0" y="48" text-anchor="middle" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11px">Total (1 Year)</text>
  </g>

  <!-- Current -->
  <g transform="translate(185, 75)">
    <text x="0" y="25" text-anchor="middle" fill="#bf91f3" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="24px" font-weight="700">{curr}</text>
    <text x="0" y="48" text-anchor="middle" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11px">Current Days</text>
  </g>

  <!-- Longest -->
  <g transform="translate(310, 75)">
    <text x="0" y="25" text-anchor="middle" fill="#38bdae" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="24px" font-weight="700">{longest}</text>
    <text x="0" y="48" text-anchor="middle" fill="#c0caf5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="11px">Longest Days</text>
  </g>

  <g transform="translate(25, 160)">
    <rect width="320" height="20" rx="4" fill="#13141f" />
    <text x="160" y="14" text-anchor="middle" fill="#7aa2f7" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="10px">✓ Computed across Public, Private &amp; Org Work</text>
  </g>
</svg>"""

def generate_languages_svg(lang_data, colors):
    bg_color = "#1a1b27"
    title_color = "#7aa2f7"
    text_color = "#c0caf5"

    width = 340
    items_to_show = lang_data[:6]
    height = 55 + (len(items_to_show) * 40) + 15

    svg_items = []
    y_offset = 0

    for idx, (lang, data) in enumerate(items_to_show):
        color = colors.get(lang) or LANG_COLORS.get(lang) or "#7aa2f7"
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
  <rect x="0.5" y="0.5" rx="5" ry="5" width="{width - 1}" height="{height - 1}" fill="{bg_color}" stroke="#24283b" stroke-width="1" />
  <g transform="translate(25, 35)">
    <text x="0" y="0" fill="{title_color}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif" font-size="16px" font-weight="700">Most Used Languages</text>
  </g>
  <g transform="translate(25, 50)">
{all_items_str}
  </g>
</svg>"""
    return svg_content

def main():
    stats = fetch_data()
    totals = stats["languages"]
    colors = stats["colors"]
    total_bytes = sum(totals.values())

    sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    lang_data = []
    output_json = {
        "user": stats["user"],
        "summary": {
            "total_contributions": stats["total_contributions"],
            "current_streak": stats["current_streak"],
            "longest_streak": stats["longest_streak"],
            "public_repos": stats["public_repos"],
            "private_repos": stats["private_repos"],
            "collab_repos": stats["collab_repos"]
        },
        "total_bytes": total_bytes,
        "languages": []
    }

    for lang, byte_count in sorted_langs:
        pct = (byte_count / total_bytes) * 100 if total_bytes > 0 else 0
        output_json["languages"].append({
            "name": lang,
            "bytes": byte_count,
            "percentage": round(pct, 2),
            "color": colors.get(lang) or LANG_COLORS.get(lang) or "#7aa2f7"
        })
        lang_data.append((lang, {"bytes": byte_count, "percentage": pct}))

    # 1. Output metrics.json
    with open("metrics.json", "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)
    print("Saved metrics.json")

    # 2. Output profile_card.svg (includes Public, Private, Collaborator counts)
    profile_svg = generate_profile_card_svg(stats)
    with open("profile_card.svg", "w", encoding="utf-8") as f:
        f.write(profile_svg)
    print("Saved profile_card.svg")

    # 3. Output streak.svg (calculated including private/collab streak)
    streak_svg = generate_streak_svg(stats)
    with open("streak.svg", "w", encoding="utf-8") as f:
        f.write(streak_svg)
    print("Saved streak.svg")

    # 4. Output languages.svg
    langs_svg = generate_languages_svg(lang_data, colors)
    with open("languages.svg", "w", encoding="utf-8") as f:
        f.write(langs_svg)
    print("Saved languages.svg")

if __name__ == "__main__":
    main()
