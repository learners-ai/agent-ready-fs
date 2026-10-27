# Agent-readiness report — [domain]

**Scanned:** [date, UTC] · **Firm type:** [segment] · **Tool:** agent-ready-fs [version], one pass

## Verdict

[One or two sentences: can agents find and read the site, and the single most important fix.]

| Layer | Score | What it covers |
|---|---|---|
| Find | [ ] /100 | Robots.txt, firewall, sitemap, AI Catalog |
| Read | [ ] /100 | Initial HTML, status codes, links, llms.txt, JSON-LD, pricing |
| Act | [ ] /100 | API contract, OAuth metadata, MCP |
| **Overall** | **[ ] /100** | 40% find, 40% read, 20% act (this plugin's weighting) |

**Read basics:** [pass / fail] — agent gets in · robots.txt allows search and user agents · answer in the initial HTML · real 404.

## Checks

| Layer | Check | Spec | Strength | Result | Detail |
|---|---|---|---|---|---|
| … | … | … | … | … | … |

## Fix list (most impact first)

1. **[Fix]** — why it matters · usual owner · effort (low / medium / high)
2. …

## Draft llms.txt

```
# [Firm name]
> [One-line description from the site's own words]

## Products
- [Page title](https://…): [describe]

## Rates and fees
- …

## Help and contact
- …
```

## robots.txt snippet

```
User-agent: *
Disallow: [low-value paths only]

Sitemap: https://[domain]/sitemap.xml
```

## Bot-policy memo

[Filled from bot-policy-template.md]

## Caveats

- One pass on one day, from one machine. Firewalls judge where a request comes from as well as its user agent, so a verified agent from a major AI provider may be treated differently.
- The score is this plugin's weighting and is not comparable with other scanners.
- This report is not legal or compliance advice, and passing these checks does not make a site compliant with any rule.

---
Built by Learners.ai on the open AgentReady spec. Questions or a second pair of eyes: https://www.learners.ai
