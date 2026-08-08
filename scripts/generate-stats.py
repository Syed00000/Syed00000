import os
import urllib.request
import json

USERNAME = "Syed00000"
TOKEN = os.environ["GH_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    login

    repositories(
      first: 1
      ownerAffiliations: OWNER
      privacy: PUBLIC
    ) {
      totalCount
    }

    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions

      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "login": USERNAME
    }
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME
    },
    method="POST"
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read())

user = result["data"]["user"]

repos = user["repositories"]["totalCount"]

commits = user["contributionsCollection"]["totalCommitContributions"]

prs = user["contributionsCollection"]["totalPullRequestContributions"]

issues = user["contributionsCollection"]["totalIssueContributions"]

reviews = user["contributionsCollection"]["totalPullRequestReviewContributions"]

contributions = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]

svg = f"""<svg width="900" height="250"
viewBox="0 0 900 250"
xmlns="http://www.w3.org/2000/svg">

<rect width="900" height="250" rx="20"
fill="#0d1117"
stroke="#30363d"/>

<text x="40" y="50"
font-family="Arial"
font-size="26"
font-weight="bold"
fill="#2ea44f">
GitHub Statistics
</text>

<text x="40" y="82"
font-family="Arial"
font-size="15"
fill="#8b949e">
@{USERNAME} • Automatically Updated
</text>

<text x="55" y="135"
font-family="Arial"
font-size="15"
fill="#8b949e">
Projects
</text>

<text x="55" y="170"
font-family="Arial"
font-size="28"
font-weight="bold"
fill="#ffffff">
{repos}
</text>

<text x="240" y="135"
font-family="Arial"
font-size="15"
fill="#8b949e">
Commits
</text>

<text x="240" y="170"
font-family="Arial"
font-size="28"
font-weight="bold"
fill="#ffffff">
{commits}
</text>

<text x="425" y="135"
font-family="Arial"
font-size="15"
fill="#8b949e">
Contributions
</text>

<text x="425" y="170"
font-family="Arial"
font-size="28"
font-weight="bold"
fill="#ffffff">
{contributions}
</text>

<text x="650" y="135"
font-family="Arial"
font-size="15"
fill="#8b949e">
Pull Requests
</text>

<text x="650" y="170"
font-family="Arial"
font-size="28"
font-weight="bold"
fill="#ffffff">
{prs}
</text>

<text x="40" y="220"
font-family="Arial"
font-size="13"
fill="#8b949e">
Issues: {issues} • Reviews: {reviews}
</text>

</svg>
"""

os.makedirs("assets", exist_ok=True)

with open("assets/github-stats.svg", "w", encoding="utf-8") as file:
    file.write(svg)

print("GitHub stats generated successfully.")
