#!/usr/bin/env python3
"""agent-ready-fs: one light agent-readiness pass over a single website.

Checks follow the open AgentReady spec (v2.0, agentready.org) in three layers -
find, read, act - plus financial-services extras (rates and fees in the HTML,
financial schema types, robots.txt vs firewall agreement).

Usage:
    python3 check.py example.com [--segment bank|credit-union|insurer|broker|wealth|other]
                                 [--agent-ua "Claude-User/1.0"] [--json out.json]

Makes roughly 15-20 GET requests to the one domain given, follows redirects,
stores nothing, and prints a JSON result to stdout (and to --json if given).
Run it only on a site you own or are authorized to test.
Standard library only (Python 3.8+).
"""
import argparse
import json
import re
import ssl
import sys
import time
import uuid
from html.parser import HTMLParser
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, HTTPSHandler

VERSION = "0.1.0"
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
DEFAULT_AGENT_UA = "Claude-User/1.0"  # the test agentready.org prescribes: curl -iL -A 'Claude-User/1.0'
TIMEOUT = 20
MAX_BYTES = 3_000_000
PAUSE = 0.4  # seconds between requests: one light pass

ROBOT_GROUPS = {
    "training": ["GPTBot", "ClaudeBot", "Google-Extended"],
    "search": ["OAI-SearchBot", "Claude-SearchBot", "PerplexityBot"],
    "user": ["ChatGPT-User", "Claude-User", "Perplexity-User"],
    "control": ["Googlebot", "Bingbot"],
}
AI_AGENT_RE = re.compile(r"(?im)^\s*user-agent\s*:\s*(gptbot|chatgpt|oai-searchbot|claude|anthropic|perplexity|google-extended|ccbot|applebot-extended|meta-externalagent|bytespider)")
CHALLENGE_MARKERS = ["cf-chl", "challenge-platform", "just a moment", "attention required", "access denied",
                     "pardon our interruption", "_incapsula_resource", "px-captcha", "request unsuccessful",
                     "are you a robot", "you have been blocked", "captcha"]
PCT_RE = re.compile(r"\b\d{1,2}\.\d{1,3}\s?%")
MONEY_RE = re.compile(r"\$\s?\d[\d,]*(\.\d{2})?")
FS_SCHEMA = ["BankOrCreditUnion", "InsuranceAgency", "FinancialService", "FinancialProduct", "BankAccount",
             "DepositAccount", "LoanOrCredit", "MortgageLoan", "InvestmentOrDeposit", "InvestmentFund",
             "PaymentCard", "CreditCard", "AccountingService", "PaymentService", "CurrencyConversionService"]
PRICING_WORDS = {
    "bank": r"rates?|apy|apr|cd|certificates?|savings|fees?",
    "credit-union": r"rates?|apy|apr|certificates?|dividends?|savings|fees?",
    "wealth": r"fees?|pricing|commissions?|costs?|expense ratio",
    "insurer": r"rates?|pricing|cost|quote|premium",
    "broker": r"pricing|cost|quote|premium|fees?",
    "other": r"pricing|prices?|rates?|fees?|plans?",
}


class _NoRedirectCap(HTTPRedirectHandler):
    max_redirections = 10


def make_opener():
    ctx = ssl.create_default_context()
    return build_opener(HTTPSHandler(context=ctx), _NoRedirectCap())


OPENER = make_opener()


def fetch(url, ua, method="GET"):
    req = Request(url, method=method, headers={
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    t0 = time.time()
    out = {"url": url, "status": None, "final": url, "ctype": "", "server": "", "text": "", "err": None}
    try:
        resp = OPENER.open(req, timeout=TIMEOUT)
        body = resp.read(MAX_BYTES)
        out.update(status=resp.status, final=resp.geturl(), ctype=resp.headers.get("Content-Type", ""),
                   server=resp.headers.get("Server", ""), link_header=resp.headers.get("Link", ""))
    except HTTPError as e:
        body = e.read(MAX_BYTES) if hasattr(e, "read") else b""
        out.update(status=e.code, final=e.geturl() or url, ctype=e.headers.get("Content-Type", "") if e.headers else "",
                   server=e.headers.get("Server", "") if e.headers else "")
    except (URLError, TimeoutError, ssl.SSLError, ConnectionError, OSError) as e:
        body = b""
        out["err"] = type(e).__name__ + ": " + str(getattr(e, "reason", e))[:120]
    charset = "utf-8"
    m = re.search(r"charset=([\w-]+)", out["ctype"] or "", re.I)
    if m:
        charset = m.group(1)
    try:
        out["text"] = body.decode(charset, errors="replace")
    except LookupError:
        out["text"] = body.decode("utf-8", errors="replace")
    out["secs"] = round(time.time() - t0, 2)
    time.sleep(PAUSE)
    return out


class Page(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg", "iframe"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.in_head = False
        self.parts, self.links, self.head_links = [], [], []
        self.h1 = 0
        self.jsonld, self._ld, self._in_ld = [], [], False
        self.meta_refresh = False
        self._a = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "head":
            self.in_head = True
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_ld, self._ld = True, []
        if tag in self.SKIP:
            self.depth += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            self.meta_refresh = True
        if tag == "link":
            self.head_links.append({k: (v or "") for k, v in a.items()})
        if tag == "a" and a.get("href"):
            self._a = [a.get("href"), ""]

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        if tag == "script" and self._in_ld:
            self.jsonld.append("".join(self._ld))
            self._in_ld = False
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        if tag == "a" and self._a:
            self.links.append((self._a[0], re.sub(r"\s+", " ", self._a[1]).strip()))
            self._a = None

    def handle_data(self, data):
        if self._in_ld:
            self._ld.append(data)
            return
        if not self.depth and not self.in_head:
            self.parts.append(data)
            if self._a is not None:
                self._a[1] += data

    @property
    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def parse(html):
    p = Page()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return p


def blocked(resp, words):
    ok = resp["status"] is not None and 200 <= resp["status"] < 300
    low = (resp["text"] or "")[:200000].lower()
    marker = next((m for m in CHALLENGE_MARKERS if m in low), None)
    return (not ok) or (words < 80 and marker is not None), marker


def schema_types(blobs):
    types = set()
    for b in blobs:
        for t in re.findall(r'"@type"\s*:\s*(\[[^\]]*\]|"[^"]+")', b):
            for name in re.findall(r'"([^"]+)"', t):
                types.add(name.split("/")[-1])
    return sorted(types)


def check(status, layer, cid, spec, strength, title, detail, fix=""):
    return {"id": cid, "layer": layer, "spec": spec, "strength": strength, "title": title,
            "status": status, "detail": detail, "fix": fix}


def run(domain, segment, agent_ua):
    domain = re.sub(r"^https?://", "", domain.strip()).strip("/").split("/")[0]
    res = {"tool": "agent-ready-fs", "version": VERSION, "domain": domain, "segment": segment,
           "agent_ua": agent_ua, "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "checks": [], "facts": {}}
    C = res["checks"]
    start = f"https://{domain}/"
    home_a = fetch(start, agent_ua)
    if home_a["status"] is None and not domain.startswith("www."):
        start = f"https://www.{domain}/"
        home_a = fetch(start, agent_ua)
    home_b = fetch(start, BROWSER_UA)
    pa, pb = parse(home_a["text"]), parse(home_b["text"])
    a_words, b_words = len(pa.text.split()), len(pb.text.split())
    a_blocked, a_marker = blocked(home_a, a_words)
    b_blocked, _ = blocked(home_b, b_words)
    final = home_a["final"] if home_a["status"] else (home_b["final"] or start)
    u = urlparse(final)
    origin = f"{u.scheme}://{u.netloc}"
    res["facts"].update(origin=origin, home_status_agent=home_a["status"], home_status_browser=home_b["status"],
                        home_words_agent=a_words, home_words_browser=b_words, server=home_a["server"] or home_b["server"],
                        challenge_marker=a_marker, error=home_a["err"])
    page = pa if not a_blocked else pb
    html = home_a["text"] if not a_blocked else home_b["text"]

    # ---- FIND ----
    if home_a["status"] is None and home_b["status"] is None:
        res["fatal"] = f"could not reach {domain}: {home_a['err']}"
        return res
    if not a_blocked:
        C.append(check("pass", "find", "agent-access", "AR-FIND-01", "MUST", "An AI agent gets in",
                       f"homepage answered {home_a['status']} to an agent request ({agent_ua})"))
    else:
        disc = not b_blocked
        C.append(check("fail", "find", "agent-access", "AR-FIND-01", "MUST", "An AI agent gets in",
                       f"agent request got {home_a['status'] or home_a['err']}" + (f" ({a_marker})" if a_marker else "")
                       + ("; the same page loaded for a desktop browser, so the firewall singles out agents" if disc else "; a desktop-browser request was blocked too"),
                       "Let verified agents through the bot manager by the providers' published IP ranges or Web Bot Auth signatures; throttle with 429 + Retry-After instead of a challenge page."))
    res["facts"]["ua_discrimination"] = a_blocked and not b_blocked

    r = fetch(origin + "/robots.txt", agent_ua)
    robots = {"status": r["status"]}
    rp = None
    if r["status"] == 200 and "<html" not in r["text"][:500].lower():
        rp = robotparser.RobotFileParser()
        rp.parse(r["text"].splitlines())
        robots["names_ai_agents"] = bool(AI_AGENT_RE.search(r["text"]))
        robots["sitemap_lines"] = re.findall(r"(?im)^\s*sitemap\s*:\s*(\S+)", r["text"])
        for grp, uas in ROBOT_GROUPS.items():
            robots[grp] = {ua: rp.can_fetch(ua, origin + "/") for ua in uas}
    elif r["status"] is not None and 400 <= r["status"] < 500 and r["status"] not in (401, 403, 429):
        robots["state"] = "no robots.txt (everything allowed)"
    else:
        robots["state"] = f"unreadable ({r['status'] or r['err']})"
    res["facts"]["robots"] = robots
    if rp:
        blocked_groups = [g for g in ("search", "user") if any(v is False for v in robots[g].values())]
        train_block = any(v is False for v in robots["training"].values())
        if blocked_groups:
            C.append(check("fail", "find", "robots-agents", "AR-FIND-01", "MUST", "robots.txt lets search and user-initiated agents in",
                           f"blocks {', '.join(blocked_groups)} agents at /",
                           "Write one wildcard rule for all agents; block only low-value paths. Training crawlers can be opted out separately."))
        else:
            C.append(check("pass", "find", "robots-agents", "AR-FIND-01", "MUST", "robots.txt lets search and user-initiated agents in",
                           "search and user-initiated agents allowed at /" + ("; training crawlers opted out" if train_block else "")))
        C.append(check("pass" if robots["names_ai_agents"] else "info", "find", "robots-decision", "governance", "FS",
                       "robots.txt shows a deliberate AI decision",
                       ("names AI crawlers explicitly" if robots["names_ai_agents"] else "no AI crawler named; AI agents fall under the default rule")
                       + ("; training crawlers blocked" if train_block else "; training crawlers allowed"),
                       "Not a spec failure. In a regulated firm, record who decided the training, search and user-agent policy (see the bot-policy memo)."))
        if a_blocked and not blocked_groups:
            C.append(check("fail", "find", "policy-vs-firewall", "AR-FIND-01", "FS", "robots.txt and the firewall agree",
                           "robots.txt lets agents in but the firewall turned the agent away",
                           "Give one owner both the robots.txt policy and the bot-manager rule, and align them."))
        elif not a_blocked:
            C.append(check("pass", "find", "policy-vs-firewall", "AR-FIND-01", "FS", "robots.txt and the firewall agree",
                           "robots.txt and the firewall both let the agent in"))
    else:
        C.append(check("partial" if "no robots" in robots.get("state", "") else "fail", "find", "robots-agents", "AR-FIND-01", "MUST",
                       "robots.txt lets search and user-initiated agents in", robots.get("state", ""),
                       "Publish a robots.txt with one wildcard rule and a Sitemap line."))

    sm = fetch(origin + "/sitemap.xml", agent_ua)
    has_sm = sm["status"] == 200 and ("<urlset" in sm["text"][:5000] or "<sitemapindex" in sm["text"][:5000])
    has_sm = has_sm or bool(robots.get("sitemap_lines"))
    C.append(check("pass" if has_sm else "fail", "find", "sitemap", "AR-FIND-03", "SHOULD", "Sitemap published",
                   "sitemap.xml found" if has_sm else "no sitemap.xml and no Sitemap line in robots.txt",
                   "Publish /sitemap.xml and reference it from robots.txt."))

    cat = fetch(origin + "/.well-known/ai-catalog.json", agent_ua)
    cat_ok = False
    if cat["status"] == 200:
        try:
            json.loads(cat["text"])
            cat_ok = True
        except ValueError:
            pass
    cat_linked = any("ai-catalog" in (l.get("rel", "") + l.get("href", "")) for l in page.head_links)
    C.append(check("pass" if cat_ok else "fail", "find", "ai-catalog", "AR-FIND-04", "MAY", "AI Catalog published and linked",
                   ("found" + (" and linked from the homepage head" if cat_linked else ", but not linked from the homepage head")) if cat_ok else "no /.well-known/ai-catalog.json",
                   "List every agent-facing resource in /.well-known/ai-catalog.json and link it: <link rel=\"ai-catalog\" href=\"/.well-known/ai-catalog.json\">."))

    # ---- READ ----
    words = len(page.text.split())
    if a_blocked and b_blocked:
        C.append(check("na", "read", "initial-html", "AR-READ-01", "MUST", "The answer is in the initial HTML", "not testable: both requests were blocked"))
    else:
        st = "pass" if words >= 150 and not page.meta_refresh else ("partial" if words >= 60 else "fail")
        C.append(check(st, "read", "initial-html", "AR-READ-01", "MUST", "The answer is in the initial HTML",
                       f"{words} words of visible text before JavaScript; {page.h1} h1" + ("; meta refresh redirect" if page.meta_refresh else ""),
                       "Server-render or prerender the homepage and key pages so the text is in the first HTML response."))

    nf = fetch(origin + "/agent-ready-check-" + uuid.uuid4().hex[:10], agent_ua)
    if nf["status"] in (404, 410):
        st, det = "pass", f"missing page returned {nf['status']}"
    elif nf["status"] is not None and 200 <= nf["status"] < 300:
        st, det = "fail", "missing page returned 200 (soft 404): agents can't tell a dead link from a live page"
    else:
        st, det = ("na" if a_blocked else "fail"), f"missing page returned {nf['status'] or nf['err']}"
    C.append(check(st, "read", "status-codes", "AR-READ-02", "MUST", "Missing pages return a real 404", det,
                   "Return 404 (or 410) for missing paths, or a redirect to a true replacement."))

    host = urlparse(origin).netloc.replace("www.", "")
    internal = []
    for href, text in page.links:
        full = urljoin(final, href)
        pu = urlparse(full)
        if pu.scheme in ("http", "https") and pu.netloc.replace("www.", "").endswith(host):
            internal.append((full.split("#")[0], text))
    uniq = {l for l, _ in internal}
    res["facts"]["homepage_internal_links"] = len(uniq)
    C.append(check("pass" if len(uniq) >= 10 else ("partial" if uniq else "fail"), "read", "homepage-links", "AR-READ-03", "SHOULD",
                   "Homepage links to the pages that answer", f"{len(uniq)} distinct internal links in the raw HTML",
                   "Put real <a href> links to products, rates or pricing, help and contact in the server-rendered homepage."))

    lt = fetch(origin + "/llms.txt", agent_ua)
    body = lt["text"].lstrip()
    llms_ok = lt["status"] == 200 and urlparse(lt["final"]).path.lower().endswith("llms.txt") and not body[:1] == "<" and len(body) > 20
    llms_linked = "llms.txt" in html
    if llms_ok:
        has_h1 = body.startswith("# ")
        n_links = len(re.findall(r"\]\(([^)\s]+)\)", body))
        st = "pass" if has_h1 and n_links >= 3 and llms_linked else "partial"
        det = f"found ({n_links} links{', H1 present' if has_h1 else ', no H1 title'}; {'linked from the homepage' if llms_linked else 'not linked from the homepage'})"
    else:
        st, det = "fail", f"no llms.txt ({lt['status'] or lt['err']})"
    res["facts"]["llms_txt"] = llms_ok
    C.append(check(st, "read", "llms-txt", "AR-READ-07", "SHOULD", "llms.txt published and linked", det,
                   "Publish a lean, described index of key pages at /llms.txt and link it from the homepage (footer or <link rel=\"alternate\">)."))

    types = schema_types(page.jsonld)
    fs_types = [t for t in types if t in FS_SCHEMA]
    res["facts"]["jsonld_types"] = types
    if page.jsonld:
        st = "pass" if fs_types or segment == "other" else "partial"
        det = f"JSON-LD types: {', '.join(types) or 'none parsed'}" + ("" if fs_types or segment == "other" else "; no financial type (e.g. BankOrCreditUnion, InsuranceAgency, FinancialService)")
    else:
        st, det = "fail", "no JSON-LD on the homepage"
    C.append(check(st, "read", "json-ld", "AR-READ-08", "SHOULD", "JSON-LD with the right financial schema type", det,
                   "Add Organization plus the matching schema.org financial type on the homepage, and repeat key facts in visible text."))

    md_alt = any("text/markdown" in l.get("type", "") for l in page.head_links)
    C.append(check("pass" if md_alt else "info", "read", "markdown-mirror", "AR-READ-09", "MAY", "Markdown mirrors advertised",
                   "markdown alternate linked" if md_alt else "none advertised (optional; fix the HTML first)"))

    # pricing / rates (AR-READ-11), segment-aware
    kw = re.compile(r"\b(" + PRICING_WORDS.get(segment, PRICING_WORDS["other"]) + r")\b", re.I)
    cands = []
    home_path = urlparse(final).path.rstrip("/")
    for full, text in internal:
        path = urlparse(full).path.lower()
        if path.rstrip("/") == home_path:
            continue
        short_text = text if text and len(text.split()) <= 6 else ""
        if kw.search(short_text) or kw.search(path.replace("-", " ").replace("/", " ")):
            score = 2 if re.search(r"rates?|pricing|fees?", (text or "") + path, re.I) else 1
            cands.append((score, full, text))
    cands = sorted({c[1]: c for c in cands}.values(), key=lambda c: -c[0])[:2]
    home_figs = len(PCT_RE.findall(page.text)) + len(MONEY_RE.findall(page.text))
    pricing = {"homepage_figures": home_figs, "pages": []}
    for _, url, text in cands:
        pr = fetch(url, agent_ua)
        pp = parse(pr["text"])
        figs = len(PCT_RE.findall(pp.text)) + len(MONEY_RE.findall(pp.text))
        pricing["pages"].append({"url": pr["final"], "link_text": text, "status": pr["status"],
                                 "words": len(pp.text.split()), "figures": figs})
    res["facts"]["pricing"] = pricing
    readable = home_figs >= 2 or any(p["figures"] >= 2 and p["status"] == 200 for p in pricing["pages"])
    if segment in ("insurer", "broker") and not readable:
        st, det = "info", "no prices in the HTML; expected for quote-based insurance, but say plainly how pricing works (factors, minimums, how to get a quote)"
    elif readable:
        st, det = "pass", "rate, fee or price figures found in the raw HTML" + (f" ({pricing['pages'][0]['url']})" if pricing["pages"] else " on the homepage")
    elif cands:
        st, det = "fail", "pricing/rates page found but no figures in the raw HTML (loaded by script or behind a form?): " + ", ".join(p["url"] for p in pricing["pages"])
    else:
        st, det = "fail", "no rates, fees or pricing link in the server-rendered homepage"
    C.append(check(st, "read", "pricing-in-html", "AR-READ-11", "SHOULD", "Rates, fees or pricing readable as text", det,
                   "Publish current rates, fees and plan terms as text in the HTML of a first-party page, not only in a calculator, image, ZIP-code form or script."))

    # ---- ACT ----
    oa = None
    for path in ("/openapi.json", "/.well-known/openapi.json"):
        x = fetch(origin + path, agent_ua)
        if x["status"] == 200 and '"openapi"' in x["text"][:2000]:
            oa = path
            break
    dev_link = next((l for l, t in internal if re.search(r"developer|/api\b|api docs", (l + " " + (t or "")).lower())), None)
    C.append(check("pass" if oa else ("partial" if dev_link else "fail"), "act", "openapi", "AR-ACT-02", "SHOULD",
                   "Public API with a machine-readable contract",
                   f"OpenAPI at {oa}" if oa else (f"developer link found ({dev_link}) but no OpenAPI at the usual paths" if dev_link else "no OpenAPI found at the usual paths"),
                   "If agents should complete tasks, publish an API with OpenAPI (operation IDs, typed errors, documented rate limits)."))
    meta = []
    for path in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-authorization-server", "/.well-known/openid-configuration"):
        x = fetch(origin + path, agent_ua)
        if x["status"] == 200 and x["text"].lstrip().startswith("{"):
            meta.append(path)
    C.append(check("pass" if meta else "fail", "act", "auth-metadata", "AR-ACT-01", "SHOULD", "Auth an agent can finish (OAuth metadata)",
                   ("found " + ", ".join(meta)) if meta else "no OAuth / OpenID discovery metadata at the root",
                   "For user-delegated access, OAuth 2.0 with discoverable metadata (RFC 8414, RFC 9728) and PKCE."))
    mcp = None
    for path in ("/.well-known/mcp.json", "/.well-known/mcp/server-card.json"):
        x = fetch(origin + path, agent_ua)
        if x["status"] == 200 and x["text"].lstrip().startswith("{"):
            mcp = path
            break
    C.append(check("pass" if mcp else "fail", "act", "mcp", "AR-ACT-10", "MUST (if agents should act)", "An MCP server or CLI agents can act through",
                   f"MCP metadata at {mcp}" if mcp else "no MCP discovery file found (a server may exist elsewhere; check the MCP Registry)",
                   "Decide which jobs agents should finish (quote, claim status, appointment, document request) and expose them through an MCP server gated by OAuth."))

    # ---- SCORE (our weighting, not the spec's) ----
    w = {"MUST": 3, "SHOULD": 2, "MAY": 1, "FS": 1, "MUST (if agents should act)": 3}
    val = {"pass": 1.0, "partial": 0.5, "fail": 0.0}
    scores = {}
    for layer in ("find", "read", "act"):
        rows = [c for c in C if c["layer"] == layer and c["status"] in val]
        tot = sum(w.get(c["strength"], 1) for c in rows)
        scores[layer] = round(100 * sum(w.get(c["strength"], 1) * val[c["status"]] for c in rows) / tot) if tot else None
    parts = [(scores["find"], 0.4), (scores["read"], 0.4), (scores["act"], 0.2)]
    have = [(s, k) for s, k in parts if s is not None]
    scores["overall"] = round(sum(s * k for s, k in have) / sum(k for _, k in have)) if have else None
    musts = [c for c in C if c["strength"] == "MUST" and c["layer"] in ("find", "read")]
    scores["read_basics_pass"] = all(c["status"] == "pass" for c in musts) and bool(musts)
    res["scores"] = scores
    res["top_links"] = [{"url": l, "text": t} for l, t in list(dict.fromkeys(internal))[:40] if t][:25]
    res["requests_made"] = "about 15-20, one pass"
    return res


def main():
    ap = argparse.ArgumentParser(description="Agent-readiness check for one website (AgentReady v2.0 + financial-services checks).")
    ap.add_argument("domain")
    ap.add_argument("--segment", default="other", choices=["bank", "credit-union", "insurer", "broker", "wealth", "other"])
    ap.add_argument("--agent-ua", default=DEFAULT_AGENT_UA)
    ap.add_argument("--json", help="also write the result to this file")
    a = ap.parse_args()
    res = run(a.domain, a.segment, a.agent_ua)
    out = json.dumps(res, indent=2)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            fh.write(out)
    print(out)
    return 0 if "fatal" not in res else 2


if __name__ == "__main__":
    sys.exit(main())
