# Hex dependency advisory review

Reviewed on 2026-10-26 against the committed dependency graph with `mix hex.audit`.
The initial graph reported 48 advisories; the targeted update leaves three
reported advisories, classified below. An audit still exits with status 1; this
is not a clean-audit claim or a suppression list.

## Runtime updates

| Package | Before | After | Symphony exposure and reason |
| --- | --- | --- | --- |
| Bandit | 1.10.3 | 1.14.0 | The optional observability listener serves HTTP and LiveView WebSockets. HTTP framing, HTTP/2 resource exhaustion, and WebSocket resource exhaustion advisories apply when the listener is enabled and reachable. 1.14.0 is the first release covering all 20 reported Bandit advisories. |
| Phoenix | 1.8.4 | 1.8.9 | LiveView uses Phoenix channels: channel-join exhaustion is relevant. Long-poll is disabled in `SymphonyElixirWeb.Endpoint`; Presence is not used, limiting the other two reported advisories. 1.8.9 patches all three. |
| Phoenix LiveView | 1.1.25 | 1.1.33 | The dashboard uses LiveView. It currently has no application redirect calls accepting external destinations, so the reported local-URL validation bypass has limited current reachability. The supported 1.1 patch fixes it without upgrading to 1.2. |
| Plug | 1.19.1 | 1.19.5 | Endpoint enables URL-encoded and multipart parsers before routing. Nested parameters and multipart headers therefore reach the affected parsers even on unsuccessful requests. The update patches all four reported advisories, including cookie attribute injection; application session attributes are static. |
| Plug Crypto | 2.1.1 | 2.2.1 | Cookie sessions use Plug Crypto. The reported secret disclosure requires wrong-typed arguments and an exposed stack trace; current signing inputs are static. The compatible update fixes argument leakage. |
| Req | 0.5.17 | 0.6.1 | Tracker clients fetch configured endpoints through Req, including redirects. A malicious or compromised endpoint can trigger automatic archive decoding/decompression. 0.6.1 is the first complete fix; 0.5 has no patched release. Multipart request encoding is not used by these clients. |
| Mint | 1.7.1 | 1.10.2 | Req uses Finch and Mint. HTTP/1 response parsing and buffering are relevant to tracker responses; HTTP/2 issues require HTTP/2 use, not the current default HTTP/1 configuration. The update fixes all 13 reported Mint advisories without a major upgrade. |
| HPAX | 1.0.3 | 1.1.0 | Bandit and Mint use the HTTP/2 header decoder. The unbounded integer-decoding advisory applies to reachable HTTP/2 peers. Bandit 1.14 requires HPAX 1.1; the security fix first shipped in 1.0.4. |
| Thousand Island | 1.4.3 | 1.6.0 | Required by Bandit 1.14, which uses the peer address captured by Thousand Island. No separate initial advisory. |

Direct requirements raise their patched lower bounds and retain the existing
Phoenix 1.8 and LiveView 1.1 release lines. Req is constrained to 0.6 patch
releases. Unrelated lock entries, including Finch, Jason, Ecto, Solid, telemetry,
and test helpers, retain their original versions.

Req 0.6 changes response defaults: JSON still decodes automatically, archive
formats no longer do, and decompression requires explicit opt-in. Symphony's
tracker clients expect JSON and do not opt into compressed responses. This is
the intended security boundary. It also affects Burrito's build-time Req usage;
release packaging requires its own release validation.

Primary references:

- [Bandit 1.14 release notes](https://github.com/mtrudel/bandit/blob/1.14.0/CHANGELOG.md)
- [Phoenix channel exhaustion](https://cna.erlef.org/osv/EEF-CVE-2026-56811.html)
- [LiveView local URL validation](https://cna.erlef.org/osv/EEF-CVE-2026-64941.html)
- [Plug nested parameter decoding](https://cna.erlef.org/osv/EEF-CVE-2026-54892.html), [multipart headers](https://cna.erlef.org/osv/EEF-CVE-2026-8468.html), [multipart length accounting](https://cna.erlef.org/osv/EEF-CVE-2026-56814.html), [cookie attributes](https://cna.erlef.org/osv/EEF-CVE-2026-56813.html)
- [Plug Crypto argument disclosure](https://cna.erlef.org/osv/EEF-CVE-2026-105963.html)
- [Req 0.6.1 release notes](https://github.com/wojtekmach/req/blob/v0.6.1/CHANGELOG.md)
- [Mint HTTP/1 framing](https://cna.erlef.org/osv/EEF-CVE-2026-94194.html), [Mint HTTP/2 header limits](https://cna.erlef.org/osv/EEF-CVE-2026-91043.html)
- [HPAX integer decoding](https://cna.erlef.org/osv/EEF-CVE-2026-58226.html)

## Remaining advisories

| Package / advisory | Classification | Disposition |
| --- | --- | --- |
| `lazy_html` 0.1.10 / CVE-2026-92106 | Test-only dependency; SVG/MathML serialization mutation XSS. Not included in the production dependency graph. Tests parse dashboard HTML rather than publish attacker-supplied serialized HTML as trusted browser content. | Retain the test helper version. A separate test-helper patch to 0.1.13 can clear this report if desired. |
| `decimal` 2.3.0 / CVE-2026-32686 | Runtime transitive dependency of Ecto and Solid. No direct application Decimal calls or Decimal config fields. Solid 1.2.2's `to_decimal/1` accepts plain decimal strings, otherwise uses `Integer.parse/1`; exponent strings do not reach `Decimal.parse/1` with an attacker-controlled exponent. | No demonstrated exponent-input route in the current application. The fix is Decimal 3.0, outside Ecto 3.13.5 and Solid 1.2.2's `~> 2.0` requirements. Avoid an unsupported override or unrelated library migration. |
| `decimal` 2.3.0 / CVE-2026-97853 | `Decimal.round/3` allocates according to its `places` argument. A custom trusted workflow can make Solid's `round` filter use tracker-controlled data as precision. Bundled workflow templates do not use numeric filters. | Conditional exposure for custom templates, not a claim that Decimal is safe. Do not derive unbounded numeric filter arguments from tracker content. A complete package fix needs Decimal 3.1.2 plus compatible Ecto/Solid upgrades and separate compatibility validation. |

Primary references: [lazy_html serialization](https://cna.erlef.org/osv/EEF-CVE-2026-92106.html),
[Decimal exponent](https://cna.erlef.org/osv/EEF-CVE-2026-32686.html),
[Decimal rounding precision](https://cna.erlef.org/osv/EEF-CVE-2026-97853.html).

Classification depends on the current call sites and bundled templates. Revisit
it when adding Decimal inputs, numeric Liquid filters, HTML serialization, or
new HTTP transports. The optional listener remains a meaningful attack surface
even when normally bound to loopback: local clients and deliberate exposure can
reach it.

## Validation

- `mix deps.get`: resolves the patched graph with unrelated lock entries unchanged.
- `mix compile --warnings-as-errors`: passes on Elixir 1.19.5 / OTP 28.5.
- Existing extensions, Linear transport, GitHub/GitLab/Asana/Jira adapter, and
  GitLab redirect tests: 56 tests, zero failures. These cover the real dashboard
  listener/LiveView, form posts, invalid hosts, and tracker JSON transport paths.
- Bounded local probes: ordinary JSON still decodes; unsolicited gzip bytes and
  archive response bytes stay encoded; excessive map and list query nesting
  raises `Plug.Conn.InvalidQueryError`, while an ordinary nested query decodes.
- `mix hex.audit`: exits 1 with exactly the three advisories documented above.
- `git diff --check`: passes.

Full repository gates are run as part of the enclosing change. No external live
tracker, destructive resource-exhaustion payload, or Burrito release build is
needed for this focused compatibility check; those are not claimed as tested.
