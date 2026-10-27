# AI agent access policy — [Firm name]

**Prepared:** [date] · **Site:** [domain] · **Based on:** agent-readiness scan of [date]

## 1. What we found

- AI agent request to the homepage: [allowed / blocked / challenged] ([status]).
- Desktop browser request to the same page: [allowed / blocked].
- robots.txt: training crawlers [allowed / blocked]; search crawlers [allowed / blocked]; user-initiated agents [allowed / blocked]; AI crawlers named explicitly: [yes / no].
- robots.txt and the firewall [agree / disagree].
- Rates, fees or pricing readable as text: [yes / no / not applicable].

## 2. Decisions

| # | Decision | Options | Our choice |
|---|---|---|---|
| 1 | AI training crawlers (GPTBot, ClaudeBot, Google-Extended) | Allow · Block | [ ] |
| 2 | AI search crawlers (OAI-SearchBot, Claude-SearchBot, PerplexityBot) | Allow · Block | [ ] |
| 3 | User-initiated agents (ChatGPT-User, Claude-User, Perplexity-User) | Allow · Block | [ ] |
| 4 | Firewall treatment of verified AI agents | Allow by published IP ranges / Web Bot Auth · Rate-limit with 429 · Challenge · Block | [ ] |
| 5 | Paths agents must never fetch (login, account, application flows) | List | [ ] |
| 6 | Content agents may quote (rates, fees, product terms, disclosures) | List pages | [ ] |
| 7 | Jobs agents may complete, if any | None yet · List | [ ] |

## 3. Controls

- robots.txt and the bot-manager rule are changed together, by [owner], with [approver] signing off.
- Agent traffic is logged and reviewed [monthly / quarterly]; spikes and blocks are reported to [owner].
- Rates and fees pages carry an as-of date and their disclosures in the same HTML.
- The policy is reviewed every [6] months or when a major AI provider changes its crawlers.

## 4. Sign-off

| Role | Name | Date |
|---|---|---|
| Marketing / web | | |
| Security (CISO) | | |
| Compliance | | |

*Prepared with the agent-ready-fs plugin. Not legal advice.*
