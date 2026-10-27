# agent-ready-fs

A free, open-source Claude plugin that checks whether a financial firm's website is ready for AI agents.

When a customer asks ChatGPT, Claude or Perplexity about your rates, fees, coverage or advisers, the agent tries to read your site first. If it can't, it answers anyway, from someone else's page. This plugin tells you whether agents can **find**, **read** and **act** on your site, what to fix first, and who in a regulated firm should own the decision.

It follows the open [AgentReady spec](https://www.agentready.org) (v2.0) and adds checks for banks, credit unions, insurers, brokers and agencies, and wealth and asset managers.

## What it checks

| Layer | Checks | Financial-services extras |
|---|---|---|
| Find | robots.txt rules for training, search and user-initiated agents; the firewall's answer to an agent request versus a browser; sitemap; AI Catalog | Whether robots.txt and the firewall agree, and whether anyone made an explicit AI decision |
| Read | Answer in the initial HTML; real 404s; homepage links; llms.txt; JSON-LD | Rates, fees and pricing readable as text; schema types for banks, credit unions, insurers and advisers |
| Act | OpenAPI; OAuth discovery metadata; MCP discovery | Which jobs agents should finish, and which must stay behind strong auth |

## What you get

- A score for each layer and an overall score
- A pass/fail on the four "read basics"
- A fix list ranked by impact and effort, with the usual owner for each item
- A draft `llms.txt` built only from pages that exist on your site
- A `robots.txt` snippet
- A one-page AI-agent access policy for marketing, security and compliance to agree and sign

## Install

**Claude Code**

```
/plugin marketplace add learners-ai/agent-ready-fs
/plugin install agent-ready-fs@learners-ai
```

**Claude desktop app:** download `agent-ready-fs.plugin` from the [latest release](https://github.com/learners-ai/agent-ready-fs/releases/latest) and add it as a plugin.

Then ask: *"Is example-bank.com agent ready? We're a credit union."*

## How it runs

- One light pass: about 15–20 ordinary GET requests to the one domain you name, with a short pause between them.
- It asks you to confirm you own the site or are authorized to test it, and stops if you aren't.
- It sends the test the AgentReady spec prescribes (user agent `Claude-User/1.0`) plus one desktop-browser request for comparison. It never retries a blocked request with a different identity.
- Nothing is stored or sent anywhere. Results are written to files in your working folder.
- Python 3.8+ standard library only. Read every line in `skills/agent-ready-check/scripts/check.py` before you run it — that's the point of open code.

## Limits

- One pass, one day, one machine. Firewalls judge where a request comes from as well as its user agent, so a verified agent from a major AI provider may be treated differently from your test.
- The score is this plugin's own weighting (MUST 3, SHOULD 2, MAY 1; overall 40% find, 40% read, 20% act). It is not the spec's and not comparable with other scanners.
- MCP discovery paths are still settling, so "no MCP found" means "not discoverable at the usual paths".
- Not legal or compliance advice. Passing these checks does not make a site compliant with any rule.

## About

Built by [Learners.ai](https://www.learners.ai), a HubSpot Platinum partner that builds CRM and AI systems for insurance, banking and wealth management. We ran these checks on 161 US and Canadian financial-services websites in October 2026 and published the aggregate results; this plugin lets you run the same checks on your own site.

AgentReady is an independent open spec maintained by its contributors; this plugin is not affiliated with or endorsed by them.

Licence: MIT. Security issues: please report them privately (see [SECURITY.md](SECURITY.md)).
