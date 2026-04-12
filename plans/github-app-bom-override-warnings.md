# GitHub App For BOM Override Warnings

## Summary
Build a small `Node + TypeScript` GitHub App as a containerized web service for GCP Cloud Run. It will receive GitHub pull request webhooks, process only one PR scan at a time, inspect all `pom.xml` files in the PR repository, detect BOM-managed dependencies whose versions are explicitly overridden, and publish a single GitHub check run with a warning-style result summary.

## Key Changes
- Create a minimal web app using a simple framework (`Express`) with:
  - `POST /webhooks/github` for GitHub webhook delivery
  - `GET /healthz` for liveness/readiness
- Implement GitHub App authentication and API access with app credentials and installation tokens.
- Handle `pull_request` webhook events for `opened` only.
  - Ignore unsupported actions with a fast `200` response.
- Add a single-process work controller:
  - exactly one active scan at a time
  - exactly one pending webhook job buffered in memory
  - if a new webhook arrives while one job is active and one is already pending, replace the pending job with the newest event for that repo/PR
  - return success immediately after enqueue so GitHub does not hold the connection open for the full scan
- Fetch the PR repository contents for the target SHA, then scan every `pom.xml` in the repo snapshot.
  - Prefer archive download of the PR head SHA over git clone to reduce code and runtime weight
- Maven analysis behavior:
  - parse each `pom.xml`
  - identify imported BOMs from `dependencyManagement` entries with `type=pom` and `scope=import`
  - build the managed dependency set contributed by those BOMs
  - flag dependencies that declare an explicit `<version>` when that coordinate is already BOM-managed
  - scope the rule to explicit version overrides only; do not fail on matching redeclarations or deeper effective-POM drift
  - resolve Maven properties where they are locally available in the project/BOM files being parsed
  - emit findings as warnings in the check run summary, not hard failures
- Publish one GitHub check run per scan:
  - stable check name such as `dependabom`
  - `completed` conclusion of `neutral` when warnings exist
  - `success` when no warnings are found
  - concise markdown summary listing file path, dependency coordinate, declared version, and BOM-managed version
- Add operational artifacts:
  - `Dockerfile`
  - `.env.example`
  - README with GitHub App registration steps, required webhook settings, Cloud Run deployment notes, and required Cloud Run settings (`max instances = 1`; request concurrency aligned with single-worker behavior)

## Public Interfaces / Config
- HTTP endpoints:
  - `POST /webhooks/github`
  - `GET /healthz`
- Required environment variables:
  - GitHub App ID
  - GitHub App private key
  - GitHub webhook secret
- Optional environment variables:
  - check run name
  - log level
  - queue capacity defaults kept to one pending job
- GitHub App permissions/events:
  - webhook subscription to pull requests
  - checks write permission
  - repository contents read permission
  - metadata read permission

## Test Plan
- Unit tests for Maven parsing:
  - imported BOM detection
  - explicit dependency version override detection
  - property substitution for versions
  - multi-module scanning across several `pom.xml` files
  - no finding when dependency version is omitted and BOM manages it
- Integration tests for webhook flow:
  - valid signed webhook enqueues and returns success
  - unsupported webhook action is ignored
  - check run created with `success` when no findings exist
  - check run created with `neutral` and warning summary when findings exist
- Concurrency tests:
  - one active job at a time
  - one pending job buffered
  - newer overlapping event replaces older pending event
- Smoke test for Cloud Run packaging:
  - container starts
  - health endpoint responds
  - webhook endpoint validates signature and routes job

## Assumptions And Defaults
- Initial scope is GitHub only, based on `docs/helpful_urls.txt`.
- The first version responds to PR creation (`pull_request.opened`) only, not later commits or reopen events.
- Findings are advisory warnings, not merge-blocking failures.
- The app uses in-memory queueing plus Cloud Run single-instance deployment to keep cost and complexity low.
- BOM resolution is limited to what can be derived from the fetched Maven files; no full Maven build or remote artifact resolution is planned in v1.
