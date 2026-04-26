# Python CLI for GitHub Java Repo Scanning

## Summary
Build a one-shot Python CLI that queries GitHub for candidate Java repositories, filters to repos updated within the last 7 days and with at least 100 stars, downloads and analyzes Maven `pom.xml` files plus imported BOMs, and emits structured JSON plus a concise console summary. The scanner should continue paging through GitHub search results until it finds enough qualifying repositories to satisfy `--max-repos`, or until there are no more candidate repositories to inspect.

The qualifying rule for a BOM-managed dependency override is: a project locally declares a dependency version even though an imported BOM already manages that same `groupId:artifactId`. External BOM artifacts should be resolved by downloading their POMs from Maven repositories and storing them in a folder relative to the project root as a cache.

## Key Changes
- Create a Python package with a CLI entrypoint such as `python -m dependabom scan` or an installed `dependabom` command.
- Add modules for:
  - GitHub discovery: search repositories with `language:Java`, `stars:>=100`, `pushed:>=<today-7d>`, pagination, and rate-limit aware fetching; continue searching until enough matching repos are found or the result set is exhausted.
  - Repo fetch: pom.xml for candidate default branches instead of cloning full git history.
  - Maven parsing: parse all `pom.xml` files, collect properties, parents, modules, `dependencyManagement`, and imported BOM references.
  - BOM resolution: resolve BOM imports from either repo-local POMs or downloaded remote BOM POMs; cache remote BOM POMs in a folder relative to the project root.
  - Override detection: flag dependencies with explicit `<version>` where a resolved BOM manages the same coordinate.
  - Reporting: write JSON results and print per-repo/pass-fail counts plus top findings.
- Keep the first version static-analysis only:
  - no `mvn dependency:tree`
  - no full effective-POM build
- Treat a repository as matching only if all of these are true:
  - GitHub search conditions match
  - at least one `pom.xml` exists
  - at least one BOM import is referenced with `type=pom` and `scope=import`
  - at least one BOM-managed explicit version override finding exists

## Interfaces / Types
- CLI:
  - `scan` command
  - options for `--days 7`, `--min-stars 100`, `--max-repos`, `--output <path>`, `--github-token-env`
- Environment:
  - required GitHub token via env var, default `GITHUB_TOKEN`
  - remote BOM fetches use Maven Central by default
- JSON output shape:
  - scan metadata: timestamp, query inputs, repo counts, skipped/error counts
  - per-repo result: `owner`, `name`, `html_url`, `stars`, `pushed_at`, `default_branch`
  - Maven summary: `pom_count`, `bom_import_count`, `resolved_bom_count`
  - findings array with `pom_path`, dependency coordinate, declared version, managing BOM coordinate, managed version, and resolution source (`local` or `remote`)
  - errors/warnings for unresolved BOMs or parse failures
- Internal defaults:
  - namespace-aware XML parsing
  - property interpolation only from values discoverable in parsed POMs/parents/BOMs
  - remote BOM fetches cached by Maven coordinate and version in a folder relative to the project root

## Test Plan
- Unit tests for Maven parsing:
  - detect BOM imports from `dependencyManagement`
  - resolve BOM-managed versions from repo-local BOMs
  - resolve BOM-managed versions from remote BOM POM fixtures
  - property substitution for versions and BOM coordinates
  - detect explicit version override only when BOM manages the same coordinate
  - ignore dependencies without local `<version>`
- Integration-style tests with fixtures:
  - multi-module Maven repo with a local BOM import and one override
  - repo with only external BOM import and one override
  - repo with BOM import but no override
  - repo with malformed or partially resolvable POMs
- GitHub client tests:
  - query construction for rolling 7-day window and star threshold
  - pagination handling
  - rate-limit / API error behavior
- CLI tests:
  - writes JSON file
  - prints summary
  - non-zero exit only for fatal scan-level failures, not for normal "no matches" results

## Assumptions
- The app is a batch CLI, not a GitHub App or background service.
- "Updated in the last week" means `pushed_at >= now - 7 days` at execution time.
- GitHub repo discovery uses the GitHub API, not local mirrors.
- BOM-managed explicit version override is the authoritative v1 definition of the override condition.
- External BOM resolution is allowed via HTTP fetch from Maven repositories.
- Repositories with unresolved BOMs remain in the report with warnings, but only fully evidenced matches are included in the final "qualified repos" set.
