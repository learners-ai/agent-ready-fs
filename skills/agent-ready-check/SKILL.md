---
name: agent-ready-check
description: >
  This skill should be used when the user asks whether a website is ready for AI agents — "is our site agent ready",
  "agent readiness check", "can ChatGPT or Claude read our website", "run the AgentReady checks", "check our robots.txt
  for AI bots", "do we need an llms.txt", "why do AI assistants get our rates wrong", "write a bot policy for AI crawlers" —
  especially for a bank, credit union, insurer, insurance broker or agency, or wealth/asset manager. It runs one light
  pass over a site the user owns or is authorized to test, scores it on the AgentReady v2.0 find / read / act layers plus
  financial-services checks, and returns a ranked fix list, a draft llms.txt, a robots.txt snippet and a one-page bot
  policy for compliance and security.
metadata:
  version: "0.1.0"
---

# Agent-ready check for financial services

Tell the user, in plain words, whether AI agents can find, read and act on their website, what to fix first, and who in a regulated firm should own the decision. Follow the steps in order.

## 1. Scope and permission (always first)

1. Get the domain and the firm type: bank, credit union, insurer, broker or agency, wealth or asset manager, or other.
2. Ask the user to confirm they own the site or are authorized to test it. The script makes about 15–20 ordinary GET requests, one pass, and stores nothing — say so.
3. If they are not authorized, stop. Offer to explain the checks in `references/agentready-map.md` instead, so they can ask the site owner to run it.
4. Never retry a blocked request with a different user agent, IP or header to get past a firewall. A block is a finding, not an obstacle.

## 2. Run the scan

Run the bundled script from this skill's base directory (shown when the skill loads):

```bash
python3 "<skill base dir>/scripts/check.py" <domain> --segment <bank|credit-union|insurer|broker|wealth|other> --json agent-ready-<domain>.json
```

- Standard library only; Python 3.8+. It sends the agent test that agentready.org prescribes (user agent `Claude-User/1.0`) and a desktop-browser request for comparison.
- Exit code 2 or a `fatal` field means the site could not be reached; report the error and stop.
- No shell or no network (some chat sandboxes): say which checks could not run, then do what is possible with a web-fetch tool — robots.txt, /llms.txt, /sitemap.xml and the homepage — and mark everything else "not tested". Never guess a result.

## 3. Read the result

The JSON has `checks` (each with layer, spec ID, strength, status, detail, fix), `scores` and `facts`. Statuses: `pass`, `partial`, `fail`, `info` (no score impact), `na` (not testable).

Interpret with `references/agentready-map.md` (what each check means and how to fix it) and `references/fs-checks.md` (what matters for banks, credit unions, insurers and wealth firms). Key readings:

- **Agent blocked but robots.txt allows agents** → the firewall and the policy disagree. In a regulated firm this is an ownership gap: marketing or web usually owns robots.txt, security owns the bot manager.
- **`ua_discrimination` true** → the site served a desktop browser but refused the declared agent. That is a deliberate rule somewhere; find out whose.
- **A firewall block from a cloud machine** may not apply to a verified agent coming from a major AI provider's published IP ranges. Say this whenever reporting a block.
- **Pricing check** → for banks and credit unions, rates in the HTML matter most: pricing is where agents' answers from other sources are least accurate. For insurers and brokers, quote-based pricing is expected; check that the site explains plainly how pricing works.

## 4. Write the report

Build it with `references/report-template.md` and save it as `agent-ready-report-<domain>.md`. Include:

1. **Scorecard** — find, read and act scores and the overall score. State that this is the plugin's own weighting (MUST 3, SHOULD 2, MAY 1; overall = 40% find, 40% read, 20% act), not the spec's and not comparable with other scanners.
2. **Read basics** — pass or fail on the four MUST checks: agent gets in, robots.txt allows search and user agents, answer in the initial HTML, real 404.
3. **Fix list** ranked by impact, then effort: MUST failures first, then pricing and llms.txt, then act-layer items. One line each: what, why, who usually owns it (web, security, compliance, product).
4. **Draft llms.txt** (step 5).
5. **robots.txt snippet** (step 6).
6. **Bot-policy memo** (step 7).
7. **Caveats**: one pass on one day; firewalls judge source IPs as well as user agents; not legal or compliance advice; passing these checks does not make a site compliant with any rule.

Then summarize in chat in 5–8 lines: the overall score, the read-basics verdict, the top three fixes, and where the files are.

## 5. Draft llms.txt

Follow the AgentReady shape: an H1 with the firm's name, a one-line `>` summary, then `##` sections with described links. Use only pages that exist in `top_links` from the scan and their link text. Write descriptions only from what the page title or link text says; mark anything else `[describe]` for the user to fill. Never invent products, rates, fees or claims. For FS sites, prefer sections such as Products, Rates and fees, Help and claims, Locations and contact, Disclosures.

## 6. robots.txt snippet

Default to one wildcard rule for all agents plus the sitemap line. If the firm decides to opt out of AI training, add explicit `Disallow: /` groups for training crawlers only (GPTBot, ClaudeBot, Google-Extended) and keep search and user-initiated agents allowed. Warn that a more specific group overrides `*`, so existing named groups must be audited.

## 7. Bot-policy memo

Fill `references/bot-policy-template.md` with the scan's facts and leave the decisions as checkboxes for the firm. It is for the compliance, security and marketing owners to agree and sign. Do not make the decisions for them.

## Rules

- Scan only the one domain the user named and confirmed. One pass. No circumvention.
- Report what was measured; mark untested items "not tested".
- Do not describe any result as "compliant" or give legal advice.
- Keep the user's data in the files you write; do not send it anywhere.
