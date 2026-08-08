import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape

USERNAME = "Syed00000"
TOKEN = os.environ["GH_TOKEN"]
API = "https://api.github.com/graphql"


def github(query, variables):
    req = urllib.request.Request(
        API,
        data=json.dumps({
            "query": query,
            "variables": variables
        }).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": USERNAME
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())

    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=2))

    return data["data"]


# ============================================================
# USER / REPOSITORIES
# ============================================================

profile_query = """
query($login: String!) {
  user(login: $login) {
    createdAt

    publicRepositories: repositories(
      first: 1
      ownerAffiliations: OWNER
      privacy: PUBLIC
    ) {
      totalCount
    }

    privateRepositories: repositories(
      first: 1
      ownerAffiliations: OWNER
      privacy: PRIVATE
    ) {
      totalCount
    }
  }
}
"""

user = github(
    profile_query,
    {"login": USERNAME}
)["user"]

created = datetime.fromisoformat(
    user["createdAt"].replace("Z", "+00:00")
).date()

today = date.today()

public_repos = user["publicRepositories"]["totalCount"]
private_repos = user["privateRepositories"]["totalCount"]
total_repos = public_repos + private_repos


# ============================================================
# GET ALL OWNED REPOSITORIES
# ============================================================

def get_repositories(privacy):
    repositories = []
    cursor = None

    while True:
        query = """
        query(
            $login: String!,
            $cursor: String,
            $privacy: RepositoryPrivacy!
        ) {
            user(login: $login) {
                repositories(
                    first: 100
                    after: $cursor
                    ownerAffiliations: OWNER
                    privacy: $privacy
                ) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }

                    nodes {
                        name

                        languages(
                            first: 100
                            orderBy: {
                                field: SIZE
                                direction: DESC
                            }
                        ) {
                            edges {
                                size
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        result = github(
            query,
            {
                "login": USERNAME,
                "cursor": cursor,
                "privacy": privacy
            }
        )["user"]["repositories"]

        repositories.extend(result["nodes"])

        if not result["pageInfo"]["hasNextPage"]:
            break

        cursor = result["pageInfo"]["endCursor"]

    return repositories


public_repository_data = get_repositories("PUBLIC")
private_repository_data = get_repositories("PRIVATE")

all_repository_data = (
    public_repository_data +
    private_repository_data
)


# ============================================================
# LANGUAGES — PUBLIC + PRIVATE
# ============================================================

language_sizes = {}

for repo in all_repository_data:
    for edge in repo["languages"]["edges"]:

        language = edge["node"]["name"]
        size = edge["size"]

        language_sizes[language] = (
            language_sizes.get(language, 0) + size
        )


total_language_size = sum(language_sizes.values())

top_languages = sorted(
    language_sizes.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]


# ============================================================
# CONTRIBUTIONS — YEAR BY YEAR
# ============================================================

all_days = {}

all_commits = 0
all_contributions = 0
all_prs = 0
all_issues = 0
all_reviews = 0

year = created.year

while year <= today.year:

    start = date(year, 1, 1)
    end = min(date(year, 12, 31), today)

    query = """
    query(
        $login: String!,
        $from: DateTime!,
        $to: DateTime!
    ) {
        user(login: $login) {

            contributionsCollection(
                from: $from
                to: $to
            ) {

                totalCommitContributions

                totalPullRequestContributions

                totalIssueContributions

                totalPullRequestReviewContributions

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

    from_time = datetime.combine(
        start,
        datetime.min.time(),
        tzinfo=timezone.utc
    ).isoformat()

    to_time = datetime.combine(
        end + timedelta(days=1),
        datetime.min.time(),
        tzinfo=timezone.utc
    ).isoformat()

    collection = github(
        query,
        {
            "login": USERNAME,
            "from": from_time,
            "to": to_time
        }
    )["user"]["contributionsCollection"]

    all_commits += collection[
        "totalCommitContributions"
    ]

    all_prs += collection[
        "totalPullRequestContributions"
    ]

    all_issues += collection[
        "totalIssueContributions"
    ]

    all_reviews += collection[
        "totalPullRequestReviewContributions"
    ]

    all_contributions += collection[
        "contributionCalendar"
    ]["totalContributions"]

    for week in collection[
        "contributionCalendar"
    ]["weeks"]:

        for contribution_day in week[
            "contributionDays"
        ]:

            all_days[
                contribution_day["date"]
            ] = contribution_day[
                "contributionCount"
            ]

    year += 1


# ============================================================
# CURRENT STREAK
# ============================================================

current_streak = 0

probe = today

if all_days.get(today.isoformat(), 0) == 0:
    probe = today - timedelta(days=1)

while all_days.get(probe.isoformat(), 0) > 0:

    current_streak += 1

    probe -= timedelta(days=1)


# ============================================================
# LONGEST STREAK
# ============================================================

longest_streak = 0
running = 0
previous = None

for day_string in sorted(all_days):

    current = date.fromisoformat(day_string)

    count = all_days[day_string]

    if count > 0:

        if (
            previous is not None
            and current == previous + timedelta(days=1)
        ):
            running += 1
        else:
            running = 1

        longest_streak = max(
            longest_streak,
            running
        )

        previous = current

    else:

        running = 0
        previous = None


# ============================================================
# SVG
# ============================================================

WIDTH = 1000
HEIGHT = 720

svg = []

svg.append(f"""
<svg
xmlns="http://www.w3.org/2000/svg"
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}">

<rect
width="100%"
height="100%"
rx="24"
fill="#0d1117"
stroke="#30363d"/>

<text
x="48"
y="52"
font-family="Arial,sans-serif"
font-size="30"
font-weight="700"
fill="#2ea44f">
GitHub Statistics
</text>

<text
x="48"
y="82"
font-family="Arial,sans-serif"
font-size="15"
fill="#8b949e">
@{USERNAME} • Dynamic GitHub Data
</text>
""")


# ============================================================
# STAT CARDS
# ============================================================

cards = [
    ("All-time Commits", all_commits),
    ("All Contributions", all_contributions),
    ("Total Repositories", total_repos),
    ("Public Repositories", public_repos),
    ("Private Repositories", private_repos),
    ("Current Streak", f"{current_streak} days"),
    ("Longest Streak", f"{longest_streak} days"),
    ("Pull Requests", all_prs),
]

positions = [
    (48, 120),
    (280, 120),
    (512, 120),
    (744, 120),

    (48, 220),
    (280, 220),
    (512, 220),
    (744, 220),
]

for (label, value), (x, y) in zip(cards, positions):

    svg.append(f"""
<rect
x="{x}"
y="{y}"
width="200"
height="78"
rx="14"
fill="#161b22"
stroke="#30363d"/>

<text
x="{x + 16}"
y="{y + 27}"
font-family="Arial,sans-serif"
font-size="13"
fill="#8b949e">
{escape(str(label))}
</text>

<text
x="{x + 16}"
y="{y + 59}"
font-family="Arial,sans-serif"
font-size="23"
font-weight="700"
fill="#ffffff">
{escape(str(value))}
</text>
""")


# ============================================================
# TOP LANGUAGES
# ============================================================

svg.append("""
<text
x="48"
y="340"
font-family="Arial,sans-serif"
font-size="21"
font-weight="700"
fill="#ffffff">
Top Languages
</text>
""")


colors = [
    "#f1e05a",
    "#3178c6",
    "#e34c26",
    "#563d7c",
    "#3572A5",
    "#41b883",
    "#da5b0b",
    "#178600",
    "#b07219",
    "#701516",
]


# Language percentage bar

bar_x = 48
bar_y = 370
bar_width = 904
bar_height = 18

if total_language_size > 0:

    current_x = bar_x

    for index, (language, size) in enumerate(top_languages):

        width = (
            bar_width *
            size /
            total_language_size
        )

        if width <= 0:
            continue

        svg.append(f"""
<rect
x="{current_x:.2f}"
y="{bar_y}"
width="{width:.2f}"
height="{bar_height}"
fill="{colors[index % len(colors)]}"/>
""")

        current_x += width


# ============================================================
# LANGUAGE LIST
# ============================================================

for index, (language, size) in enumerate(top_languages):

    percentage = (
        (size / total_language_size) * 100
        if total_language_size > 0
        else 0
    )

    column = index % 2
    row = index // 2

    x = 48 + (column * 452)
    y = 415 + (row * 38)

    svg.append(f"""
<circle
cx="{x + 7}"
cy="{y - 5}"
r="6"
fill="{colors[index % len(colors)]}"/>

<text
x="{x + 22}"
y="{y}"
font-family="Arial,sans-serif"
font-size="15"
fill="#ffffff">
{escape(language)}
</text>

<text
x="{x + 410}"
y="{y}"
text-anchor="end"
font-family="Arial,sans-serif"
font-size="15"
fill="#8b949e">
{percentage:.2f}%
</text>
""")


# ============================================================
# FOOTER
# ============================================================

svg.append(f"""
<text
x="48"
y="695"
font-family="Arial,sans-serif"
font-size="13"
fill="#8b949e">
Issues: {all_issues} • Reviews: {all_reviews} • Languages: Public + Private
</text>

</svg>
""")


# ============================================================
# WRITE FILE
# ============================================================

os.makedirs("assets", exist_ok=True)

with open(
    "assets/github-stats.svg",
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(svg))


print("==========================================")
print("       GITHUB STATS GENERATED")
print("==========================================")
print("Total repositories :", total_repos)
print("Public repositories:", public_repos)
print("Private repositories:", private_repos)
print("All-time commits   :", all_commits)
print("All contributions  :", all_contributions)
print("Current streak     :", current_streak)
print("Longest streak     :", longest_streak)
print("Pull requests      :", all_prs)
print("Issues             :", all_issues)
print("Reviews            :", all_reviews)
print("Top languages      :", top_languages)
print("==========================================")
