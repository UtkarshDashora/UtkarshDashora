import os
import html
import requests
from datetime import datetime, timedelta, timezone

USERNAME = "UtkarshDashora"
TOKEN = os.environ["STREAK_STATS_TOKEN"]

GRAPHQL_URL = "https://api.github.com/graphql"

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
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

today = datetime.now(timezone.utc).date()
from_date = today - timedelta(days=365)

variables = {
    "login": USERNAME,
    "from": f"{from_date}T00:00:00Z",
    "to": f"{today}T23:59:59Z",
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

response = requests.post(
    GRAPHQL_URL,
    json={"query": query, "variables": variables},
    headers=headers,
    timeout=30,
)

response.raise_for_status()

data = response.json()

if "errors" in data:
    raise RuntimeError(data["errors"])

calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

total = calendar["totalContributions"]

days = []

for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days.append({
            "date": datetime.strptime(day["date"], "%Y-%m-%d").date(),
            "count": day["contributionCount"],
        })

days.sort(key=lambda x: x["date"])

# -----------------------------
# Calculate current streak
# -----------------------------

contribution_dates = {
    day["date"]
    for day in days
    if day["count"] > 0
}

if contribution_dates:
    latest = max(contribution_dates)

    # Allow today to be empty while yesterday has contribution.
    if latest == today:
        current_date = today
    elif latest == today - timedelta(days=1):
        current_date = today - timedelta(days=1)
    else:
        current_date = None

    current_streak = 0

    if current_date:
        while current_date in contribution_dates:
            current_streak += 1
            current_date -= timedelta(days=1)
else:
    current_streak = 0


# -----------------------------
# Calculate longest streak
# -----------------------------

longest_streak = 0
running = 0
previous_date = None

for date in sorted(contribution_dates):
    if previous_date and date == previous_date + timedelta(days=1):
        running += 1
    else:
        running = 1

    longest_streak = max(longest_streak, running)
    previous_date = date


# -----------------------------
# Generate SVG
# -----------------------------

def esc(value):
    return html.escape(str(value))


svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="900"
height="260"
viewBox="0 0 900 260">

<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#161b22"/>
        <stop offset="100%" stop-color="#0d1117"/>
    </linearGradient>

    <linearGradient id="green" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#39d353"/>
        <stop offset="100%" stop-color="#26a641"/>
    </linearGradient>
</defs>

<rect
    x="0"
    y="0"
    width="900"
    height="260"
    rx="18"
    fill="url(#bg)"
    stroke="#30363d"
/>

<!-- Header -->

<text
    x="40"
    y="48"
    font-family="Arial, Helvetica, sans-serif"
    font-size="24"
    font-weight="700"
    fill="#f0f6fc">
    GitHub Contribution Streak
</text>

<text
    x="40"
    y="76"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
    fill="#8b949e">
    @{esc(USERNAME)} • Last 365 Days
</text>


<!-- Total Contributions -->

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
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
    fill="#8b949e">
    Total Contributions
</text>

<text
    x="65"
    y="184"
    font-family="Arial, Helvetica, sans-serif"
    font-size="36"
    font-weight="700"
    fill="#39d353">
    {esc(total)}
</text>


<!-- Current Streak -->

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
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
    fill="#8b949e">
    Current Streak
</text>

<text
    x="352"
    y="184"
    font-family="Arial, Helvetica, sans-serif"
    font-size="36"
    font-weight="700"
    fill="#f0f6fc">
    {esc(current_streak)}
</text>

<text
    x="352"
    y="207"
    font-family="Arial, Helvetica, sans-serif"
    font-size="13"
    fill="#8b949e">
    days
</text>


<!-- Longest Streak -->

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
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
    fill="#8b949e">
    Longest Streak
</text>

<text
    x="639"
    y="184"
    font-family="Arial, Helvetica, sans-serif"
    font-size="36"
    font-weight="700"
    fill="#f0f6fc">
    {esc(longest_streak)}
</text>

<text
    x="639"
    y="207"
    font-family="Arial, Helvetica, sans-serif"
    font-size="13"
    fill="#8b949e">
    days
</text>

</svg>
"""

os.makedirs("profile", exist_ok=True)

with open("profile/streak.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print("======================================")
print(" GitHub Streak Stats Generated")
print("======================================")
print(f"User: {USERNAME}")
print(f"Total Contributions: {total}")
print(f"Current Streak: {current_streak}")
print(f"Longest Streak: {longest_streak}")
print("Output: profile/streak.svg")
