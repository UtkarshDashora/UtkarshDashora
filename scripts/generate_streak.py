import os
import requests
from datetime import datetime, timedelta, timezone

USERNAME = "UtkarshDashora"
TOKEN = os.environ["STREAK_STATS_TOKEN"]

API_URL = "https://api.github.com/graphql"

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=365)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    login
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

variables = {
    "login": USERNAME,
    "from": f"{start}T00:00:00Z",
    "to": f"{today}T23:59:59Z"
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "UtkarshDashora-Streak-Stats"
}

response = requests.post(
    API_URL,
    headers=headers,
    json={
        "query": query,
        "variables": variables
    },
    timeout=30
)

print("HTTP STATUS:", response.status_code)

data = response.json()

print("API RESPONSE:")
print(data)

if response.status_code != 200:
    raise RuntimeError(f"GitHub API error: {response.status_code}")

if "errors" in data:
    raise RuntimeError(data["errors"])

user = data["data"]["user"]

if user is None:
    raise RuntimeError(
        f"GitHub user '{USERNAME}' could not be found."
    )

calendar = user["contributionsCollection"]["contributionCalendar"]

total = calendar["totalContributions"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": datetime.strptime(
                day["date"], "%Y-%m-%d"
            ).date(),
            "count": day["contributionCount"]
        })

days.sort(key=lambda x: x["date"])

# -----------------------------
# Current streak
# -----------------------------

dates = {
    d["date"]
    for d in days
    if d["count"] > 0
}

current_streak = 0

if dates:

    check_date = today

    if check_date not in dates:
        check_date = today - timedelta(days=1)

    while check_date in dates:
        current_streak += 1
        check_date -= timedelta(days=1)


# -----------------------------
# Longest streak
# -----------------------------

longest_streak = 0
running = 0
previous = None

for date in sorted(dates):

    if previous and date == previous + timedelta(days=1):
        running += 1
    else:
        running = 1

    longest_streak = max(longest_streak, running)
    previous = date


# -----------------------------
# SVG
# -----------------------------

svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="900"
height="260"
viewBox="0 0 900 260">

<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#161b22"/>
        <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>
</defs>

<rect
    width="900"
    height="260"
    rx="18"
    fill="url(#bg)"
    stroke="#30363d"
/>

<text
    x="40"
    y="50"
    font-family="Arial"
    font-size="25"
    font-weight="bold"
    fill="#f0f6fc">
    GitHub Contribution Streak
</text>

<text
    x="40"
    y="78"
    font-family="Arial"
    font-size="14"
    fill="#8b949e">
    @{USERNAME} • Last 365 Days
</text>

<!-- Total -->

<rect
    x="40"
    y="105"
    width="245"
    height="115"
    rx="14"
    fill="#21262d"
    stroke="#30363d"
/>

<text
    x="65"
    y="140"
    font-family="Arial"
    font-size="15"
    fill="#8b949e">
    Total Contributions
</text>

<text
    x="65"
    y="185"
    font-family="Arial"
    font-size="36"
    font-weight="bold"
    fill="#39d353">
    {total}
</text>

<!-- Current -->

<rect
    x="327"
    y="105"
    width="245"
    height="115"
    rx="14"
    fill="#21262d"
    stroke="#30363d"
/>

<text
    x="352"
    y="140"
    font-family="Arial"
    font-size="15"
    fill="#8b949e">
    Current Streak
</text>

<text
    x="352"
    y="185"
    font-family="Arial"
    font-size="36"
    font-weight="bold"
    fill="#f0f6fc">
    {current_streak}
</text>

<text
    x="352"
    y="207"
    font-family="Arial"
    font-size="13"
    fill="#8b949e">
    days
</text>

<!-- Longest -->

<rect
    x="614"
    y="105"
    width="245"
    height="115"
    rx="14"
    fill="#21262d"
    stroke="#30363d"
/>

<text
    x="639"
    y="140"
    font-family="Arial"
    font-size="15"
    fill="#8b949e">
    Longest Streak
</text>

<text
    x="639"
    y="185"
    font-family="Arial"
    font-size="36"
    font-weight="bold"
    fill="#f0f6fc">
    {longest_streak}
</text>

<text
    x="639"
    y="207"
    font-family="Arial"
    font-size="13"
    fill="#8b949e">
    days
</text>

</svg>
"""

os.makedirs("profile", exist_ok=True)

with open("profile/streak.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print()
print("====================================")
print("GitHub Streak Stats")
print("====================================")
print(f"Username           : {USERNAME}")
print(f"Total Contributions: {total}")
print(f"Current Streak     : {current_streak}")
print(f"Longest Streak     : {longest_streak}")
print("====================================")
