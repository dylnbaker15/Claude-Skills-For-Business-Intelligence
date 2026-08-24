# Installing the skill

A skill is a folder with a `SKILL.md` file. Installing it is copying that folder to the right place. No build step, no dependencies.

## Claude Code

| Location | Path | Loads in |
|---|---|---|
| **User** (recommended) | `~/.claude/skills/honest-dataviz/` | every project on your machine |
| **Project** | `<your-repo>/.claude/skills/honest-dataviz/` | that one repository |

### macOS / Linux

```bash
mkdir -p ~/.claude/skills
cp -R honest-dataviz ~/.claude/skills/
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills"
Copy-Item -Recurse -Force ".\honest-dataviz" "$HOME\.claude\skills\"
```

### Confirm it loaded

Start a **new** Claude Code session (skills are read at startup), then ask:

> Which skills do you have available?

`honest-dataviz` should be in the list, or invoke it directly with `/honest-dataviz`.

## Cursor

Cursor reads project rules, not a `skills/` directory, so the skill also ships in Cursor-native form:

- **`honest-dataviz/honest-dataviz.mdc`**: copy into `.cursor/rules/`.
- **`honest-dataviz/AGENTS.md`**: dropping it at your repo root also works; Cursor and several other agents read that file automatically.

Both carry the same content as `SKILL.md`. Confirm by opening a new chat and asking Cursor to describe the rules it is following.

## Any other agent

**`honest-dataviz/plain-prompt.md`** is the skill with no tool-specific framing. Paste it into your agent's system prompt, custom-instructions field, or project knowledge. This is the fallback for Windsurf, Cline, Zed, or a raw API loop.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Skill not in the list | Session started before you copied it | Start a fresh session; skills load at startup |
| Skill not in the list | Folder nested one level too deep | `SKILL.md` must be at `honest-dataviz/SKILL.md` |
| Skill loads but never triggers | The agent did not see a reason to | Ask for it by name (`/honest-dataviz`), or name a chart-building task |
| Garbled front matter | An editor reformatted the YAML | Re-copy the original file |

## Updating

Updates to the free skill land in this repo: `git pull` and re-copy the folder. The full [Kymira packs](https://kymira.ai/#pricing) ship an installer and a `kymira` CLI that handles install, status, and updates in one command.
