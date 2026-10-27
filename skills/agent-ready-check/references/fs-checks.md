# Financial-services reading of the results

Use this to explain why each finding matters to a bank, credit union, insurer, broker or agency, or wealth firm. Keep claims factual; never call a result "compliant".

## 1. The policy and the firewall must agree

- robots.txt is usually owned by marketing or the web team; the bot manager (Cloudflare, Akamai, Imperva and similar) by security. They drift apart.
- A firewall that blocks a declared AI agent while robots.txt invites it means nobody owns the decision. In a regulated firm, record the decision and its owner.
- Firewalls also weigh where a request comes from. A verified agent from a major AI provider may pass where a test from a cloud server is blocked, so always ask the security team what the bot manager does with verified AI agents.

## 2. Decide training, search and user-initiated agents separately

| Crawler job | Examples | What blocking it does |
|---|---|---|
| Training | GPTBot, ClaudeBot, Google-Extended | Opts content out of model training; no effect on answers today |
| Search index | OAI-SearchBot, Claude-SearchBot, PerplexityBot | Drops the firm from AI search results and citations |
| User-initiated | ChatGPT-User, Claude-User, Perplexity-User | Stops an agent from reading the page a customer asked about; the agent then answers from other sites |

A firm can opt out of training and still be found and read. Write that as an explicit choice.

## 3. Rates, fees and terms are the pricing page

- For banks and credit unions, deposit and loan rates are pricing. Agents answer pricing questions worst when they can't read the firm's own page, so rates hidden behind a ZIP-code form, a calculator or a script get replaced by an aggregator's or a news site's figure.
- Wealth firms: advisory fees, account minimums, fund expense ratios and commission schedules.
- Insurers and brokers: prices are usually quote-based. Publish plainly how pricing works (rating factors, minimum premiums, how to get a quote, appetite by line) so an agent doesn't invent it.
- Keep rate tables dated ("rates as of …") and in visible text, with the disclosures next to them.

## 4. Schema types to use

`Organization` plus the closest financial type: `BankOrCreditUnion`, `InsuranceAgency`, `FinancialService`; products as `FinancialProduct`, `DepositAccount`, `LoanOrCredit`, `MortgageLoan`, `InvestmentFund`, `CreditCard`. Repeat any fact that matters (rates, fees, licence numbers, NMLS ID, routing number where public) in visible text, because many agents read the text, not the script blocks.

## 5. What agents should and shouldn't do (act layer)

- Good first jobs to expose: find a branch or adviser, book an appointment, check a claim's status, request a document, start a quote, look up current rates.
- Keep anything that moves money, changes an account or binds coverage behind strong user-delegated auth (OAuth with PKCE), with logging and human confirmation.
- Whatever the agent can act on usually lives in the CRM and the core systems (core banking, the agency management system, policy admin, custodian). The website is only the front door.

## 6. Who owns what

| Item | Usual owner | Sign-off |
|---|---|---|
| robots.txt and llms.txt | Marketing / web | Compliance |
| Bot manager and WAF rules | Security / IT | CISO |
| Rates, fees and disclosures in HTML | Product / marketing | Compliance |
| JSON-LD and site structure | Web | Marketing |
| APIs, OAuth, MCP | Engineering / IT | CISO, risk |
