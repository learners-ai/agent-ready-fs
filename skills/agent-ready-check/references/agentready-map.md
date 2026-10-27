# What each check means (mapped to AgentReady v2.0)

AgentReady (agentready.org) is an open, MIT-licensed spec for what a site should ship so AI agents can find it, read it and act on it. Strengths: **MUST** = agents fail without it, **SHOULD** = measurably shapes agent behaviour, **MAY** = emerging convention. This plugin is independent of the spec's authors.

## Find

| Check id | Spec | Strength | Passes when | How to fix |
|---|---|---|---|---|
| agent-access | AR-FIND-01 | MUST | The homepage answers 2xx with real content to a request whose user agent is `Claude-User/1.0` (the spec's own test) | Let verified agents through the bot manager by the providers' published IP ranges or Web Bot Auth signatures. Throttle with 429 + Retry-After instead of a challenge page |
| robots-agents | AR-FIND-01 | MUST | robots.txt does not block search crawlers (OAI-SearchBot, Claude-SearchBot, PerplexityBot) or user-initiated fetchers (ChatGPT-User, Claude-User, Perplexity-User) at `/` | One wildcard rule for all agents; block low-value paths only; never list secret paths |
| robots-decision | governance | FS | robots.txt names AI crawlers, showing someone made a decision | Informational. Record who decided the training / search / user-agent policy |
| policy-vs-firewall | AR-FIND-01 | FS | robots.txt and the firewall give the agent the same answer | One owner for both, or a written rule that keeps them aligned |
| sitemap | AR-FIND-03 | SHOULD | /sitemap.xml exists or robots.txt has a Sitemap line | Publish it; agents rarely fetch it, but search indexes do |
| ai-catalog | AR-FIND-04 | MAY | /.well-known/ai-catalog.json exists, ideally linked with `<link rel="ai-catalog">` | List agent-facing resources (docs, llms.txt, API, MCP) and link the file from the homepage head |

## Read

| Check id | Spec | Strength | Passes when | How to fix |
|---|---|---|---|---|
| initial-html | AR-READ-01 | MUST | ≥ 150 words of visible homepage text before JavaScript runs, no meta-refresh hop | Server-render or prerender; a fetch-only agent never runs your scripts |
| status-codes | AR-READ-02 | MUST | A made-up path returns 404 or 410 | Stop returning 200 "not found" pages and redirect-to-homepage for missing paths |
| homepage-links | AR-READ-03 | SHOULD | ≥ 10 distinct internal links in the raw HTML | Real `<a href>` links to products, rates or pricing, help and contact |
| llms-txt | AR-READ-07 | SHOULD | /llms.txt exists, starts with an H1, lists ≥ 3 described links, and is linked from the homepage | Lean described index; link it from the footer or `<link rel="alternate">` — files nothing points to are files nothing fetches |
| json-ld | AR-READ-08 | SHOULD | JSON-LD on the homepage, with a schema.org financial type for FS firms | Organization + BankOrCreditUnion / InsuranceAgency / FinancialService; repeat key facts in visible text |
| markdown-mirror | AR-READ-09 | MAY | A `text/markdown` alternate is advertised | Optional; fix the HTML first |
| pricing-in-html | AR-READ-11 | SHOULD | Rate, fee or price figures appear as text on the homepage or a linked pricing page | Publish current rates, fees and plan terms as text, not only in a calculator, image, ZIP-code form or script |

## Act (applies when agents should complete tasks, not only read)

| Check id | Spec | Strength | Passes when | How to fix |
|---|---|---|---|---|
| openapi | AR-ACT-02 | SHOULD | OpenAPI at /openapi.json or /.well-known/openapi.json | Public API with operation IDs, typed errors, versioning, documented rate limits |
| auth-metadata | AR-ACT-01 | SHOULD | OAuth / OpenID discovery metadata at the root | OAuth 2.0 with RFC 8414 / RFC 9728 metadata and PKCE for user-delegated access |
| mcp | AR-ACT-10 | MUST if agents should act | An MCP discovery file at a well-known path | Expose the jobs agents should finish through an MCP server gated by OAuth; list it in the MCP Registry. The path conventions are still moving, so a "fail" here can mean "not discoverable", not "absent" |

## Scoring used by this plugin

Weights: MUST 3, SHOULD 2, MAY 1, FS 1; pass 1, partial 0.5, fail 0; `info` and `na` excluded. Layer score = weighted share passed. Overall = 40% find + 40% read + 20% act. This is our weighting, not the spec's, and it is not comparable with other scanners (ora.ai, is-agentic.com, Mintlify, AXIS).

## Evidence worth quoting (as of October 2026)

- Ora research, "AX is the New AEO" (8 Oct 2026; 1,056 business sites): when an agent can't read a site it answers anyway from other pages; those answers were 3.7× as likely to contain none of the facts asked for; pricing answers were accurate 60% of the time from the firm's own site vs 37% from elsewhere.
- AgentReady v2.0 (Oct 2026): 6% of ~127,000 sites scanned by Ora grade B or above.
- Ora, "The state of agent readiness" (Apr 2026): 3% of scanned products ship a spec-grade MCP server.
- Learners.ai scan of 161 US and Canadian financial-services sites (27 Oct 2026): 12% blocked or challenged an agent request, and 16 of those 20 had a robots.txt that let agents in; 75% passed the read basics; 1 published an AI Catalog.

Re-check figures against the sources before quoting them publicly.
