from datetime import datetime, timedelta, timezone
import subprocess
from github import Auth, Github

def find_github_bom_candidates(token: str) -> None:
    min_stars = 100
    updated_within_days = 7
    default_per_page = 100
    cutoff = datetime.now(timezone.utc) - timedelta(days=updated_within_days)
    pushed_cutoff = cutoff.strftime("%Y-%m-%d")
    query = (
        f"language:Java stars:>={min_stars} pushed:>={pushed_cutoff} "
        "archived:false topic:maven"
    )

    gh = Github(auth=Auth.Token(token), per_page=default_per_page)
    repositories = gh.search_repositories(query=query, sort="updated", order="desc")
    first_page = repositories.get_page(0)

    for repo in first_page:
        print(repo.full_name)

def main() -> int:
    token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()

    find_github_bom_candidates(token)
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
