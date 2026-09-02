# Claude skills for business intelligence, certified

**Every figure reconciles to a total the file itself asserts.** A free skill and the
full doctrine from [Kymira](https://kymira.ai) that teach Claude Code and Cursor to
build charts, dashboards and reports on your own exports, name what the file cannot
prove instead of shipping it as a number, and refuse to guess.

[![The live demo: an intranet where every figure reconciles to source](docs/demo-overview.png)](https://kymira.ai/demo/)

*A [live demo report](https://kymira.ai/demo/) built with the full skill set: every check ties to the file it came from, on fictional data.*

## Install

One command, for Claude Code, Cursor, Codex and the other agents the `skills` CLI supports:

```bash
npx skills add dylnbaker15/Claude-Skills-For-Business-Intelligence
```

Or copy the folder yourself. A skill is a folder with a `SKILL.md` in it, so
installing is a copy. No build step, no dependencies.

**Claude Code**

```bash
git clone https://github.com/dylnbaker15/claude-skills-for-business-intelligence.git
mkdir -p ~/.claude/skills
cp -R claude-skills-for-business-intelligence/honest-dataviz ~/.claude/skills/
```

Start a **new** session (skills load at startup) and ask "which skills do you have
available?". `honest-dataviz` should be in the list.

**Cursor**

Cursor reads project rules rather than a skills folder, so the skill also ships as a
`.mdc` rule. From the clone above, inside the project you want it in:

```bash
mkdir -p .cursor/rules
cp honest-dataviz/honest-dataviz.mdc .cursor/rules/
```

`honest-dataviz/AGENTS.md` at your repo root works too, and
`honest-dataviz/plain-prompt.md` is the same content with no tool-specific framing,
for Windsurf, Cline, Zed, or a raw API loop. [INSTALL.md](INSTALL.md) covers each
route, Windows included.

**As a Claude Code plugin**

```
/plugin marketplace add dylnbaker15/Claude-Skills-For-Business-Intelligence
/plugin install kymira-certified-bi@kymira
```

Install by exactly one route. Two copies of the same skill both try to trigger.

## What's in this repo

- **[`honest-dataviz/`](honest-dataviz/SKILL.md)**, the free skill: charts and
  dashboards that read at a glance, survive a colour-blind reviewer, and never imply
  more certainty than the data has. Every rule in it was bought with a measured
  failure in a production reporting engine. None is taste.
- **[`DOCTRINE.md`](DOCTRINE.md)**, the eleven principles of certified BI, published
  in full. The one-sentence version: reconcile every figure to what the source
  asserts about itself, and refuse to guess, out loud.
- **[`doctrine_gate.py`](doctrine_gate.py)**, the gate: a plain script that reads a
  finished artifact and fails the build when a principle is broken.
- **[`INSTALL.md`](INSTALL.md)**, every install route in about a minute, plus
  troubleshooting.

## Try it with one prompt

**Start on a real export from your own business**, not a sample. Drop the file into a
project that contains `DOCTRINE.md`, then:

> Here is a raw export from my business: [the file]. Read DOCTRINE.md and use the
> honest-dataviz skill, then build me a single-file HTML dashboard from this export.
> Rules: every figure must reconcile to totals the file itself asserts, show the
> reconciliation, and if the file cannot prove a number, name that on the page
> instead of shipping it. Refuse to guess.

The difference shows up immediately: the agent hunts for what the file asserts about
itself before it types a single figure, and tells you what it cannot prove.

## Six ways a number goes wrong

**These are observed failures, not hypotheticals**, each one caught in our own audits
of agent-built reports and each one now the reason a rule exists.

| Failure mode | What we saw |
|---|---|
| The 100x slip that ties perfectly | A price entered as 5900.00 instead of 59.00 multiplies through every subtotal consistently, so every reconciliation passes while the headline triples. |
| The filename that lies about the period | A file called Q2 carrying July rows. Headline the file and the quarter is wrong. |
| The join that quietly covers 62% | A reference join drops a third of the rows and the report says nothing, because nothing asked. |
| Two churn definitions, 3.4 points apart | Two teams, one word, different denominators, both defensible, and a leadership deck that mixes them. |
| The verify script that silently did nothing | The agent wrote itself a verification script, it no-op'd, and everything passed. |
| The certified page that opens as garbage | No charset declaration, so every heading renders as mojibake in the recipient's browser. |

Fifty-one of them, grouped by family and each tied to the principle that addresses
it, are catalogued at [kymira.ai/failure-modes](https://kymira.ai/failure-modes). The
eleven principles are at [kymira.ai/doctrine](https://kymira.ai/doctrine), and this
skill has its own page at
[kymira.ai/skills/honest-dataviz](https://kymira.ai/skills/honest-dataviz).

## Why "certified"

A model on its own writes a clever first draft, confident everywhere: it guesses a
total when the file states none, and presents every figure with equal confidence.
These skills came from building a real reporting system that was broken on purpose
across thirteen audit rounds and rebuilt until it stopped shipping a single number it
could not prove. The doctrine in this repo is that system's constitution.

## Free versus paid

**This repo is the free tier and it is not a teaser**: the skill here is the complete
file, the same content the paid packs install under a namespaced name, MIT licensed,
nothing gated. The packs add the rest of the system.

| | Free, this repo | Core, $199 | Everything, $349 |
|---|---|---|---|
| Skills | `honest-dataviz` | The 13 craft skills, versioned | All 22 skills |
| The doctrine, 11 principles | Yes | Yes | Yes |
| Report templates | | | 12 |
| Metric Library | | | 351 definitions, every fork worked |
| Format Library | | | 47 export shapes, every trap named |
| Installer and the `kymira` CLI | | Yes | Yes |
| License | MIT | Personal | Personal |

Both packs are a one-time purchase with lifetime updates. All sales are final; the
free skill and the full doctrine cost nothing, so judge the quality here first.
Details at [kymira.ai/get?tier=free](https://kymira.ai/get?tier=free), the road from
raw export to a report your team runs on at
[your first week](https://kymira.ai/first-week.html), and what is being built next on
[the roadmap](https://kymira.ai/roadmap.html).

## FAQ

**Is the free skill cut down?**
No. It is the complete file, the same content the paid packs install, under MIT. The
doctrine is published in full for the same reason: the method is checkable or it is
worth nothing.

**Does it work outside Claude Code?**
Yes. The skill ships in four shapes in this repo: `SKILL.md` for Claude Code, a
`.mdc` rule for Cursor, `AGENTS.md` for agents that read that file, and
`plain-prompt.md` for anything with a system prompt.

**Where does my data go?**
Nowhere. These are plain text files that run inside your own agent on your own
machine. There is no server, no telemetry, and no network call in the skill.

**Will a better model make this unnecessary?**
The guarantees here are process, not model behaviour. Reconciliation runs as code
that re-runs, and a gate that fails closed cannot be talked out of by a smarter
model.

**How do I get updates?**
Updates to the free skill land in this repo: `git pull` and re-copy the folder, or
re-run the `npx skills add` command. Watch the repo to see them land. The zip at
[kymira.ai/get?tier=free](https://kymira.ai/get?tier=free) always carries the current
version, and needs no email.

**I installed a Kymira pack. Do I remove this?**
Yes, remove this copy first. The packs ship their own namespaced version
(`kymira-honest-dataviz`) and two copies will both try to trigger.

## License

Everything in this repo is [MIT licensed](LICENSE). Cite it with the metadata in
[CITATION.cff](CITATION.cff); [llms.txt](llms.txt) is the index for agents.
