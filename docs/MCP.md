# SignageCast with Claude and other AI assistants (MCP)

[← README](../README.md) · [manual](MANUAL.md) · [layout format](LAYOUT-FORMAT.md) · [Deutsch](#deutsch-kurz)

Since 0.39 SignageCast has an **MCP server** ([Model Context Protocol](https://modelcontextprotocol.io)). An assistant
such as Claude (Claude Code, Claude Desktop) can then manage the content directly: build and change layouts, look at a
preview picture, put a layout on a TV, send a ticker message or an announcement, upload pictures, manage streams and
data sources – in plain language, e.g. *“Make a calm layout for the waiting room with our logo and the opening hours
as ticker, show me a preview, then put it on the TV in the waiting room from 8 to 18 o'clock.”*

## How it connects

The assistant starts the MCP server **over SSH** on the SignageCast machine: `ssh <user>@<host> signagecast-mcp`.
There is no new port and no token – whoever may log in with SSH may use it. The server talks to SignageCast exactly
like the admin page does (only on the machine itself).

1. Allow SSH login with a key for a user on the SignageCast machine, e.g. `tvadmin`
   (Proxmox/Debian: `ssh-copy-id tvadmin@<IP>` once from the computer the assistant runs on).
2. Check: `ssh tvadmin@<IP> signagecast-mcp` waits for input – end it with Ctrl+D.
3. Add the server to the assistant:

**Claude Code**

```bash
claude mcp add signagecast -- ssh -T tvadmin@<IP> signagecast-mcp
```

**Claude Desktop** (`claude_desktop_config.json`)

```json
{"mcpServers": {"signagecast": {"command": "ssh", "args": ["-T", "tvadmin@<IP>", "signagecast-mcp"]}}}
```

**Docker / Podman:** on the host of the container `docker exec -i signagecast signagecast-mcp`
(command `docker`, arguments `["exec", "-i", "signagecast", "signagecast-mcp"]`); from another computer via SSH to
the host: `ssh -T user@host docker exec -i signagecast signagecast-mcp`.

## What the assistant can do

| Tool | What it does |
|---|---|
| `status` | Version, internet, every TV with its current layout, playback, picture check; open problems |
| `list_tvs`, `list_layouts`, `get_layout` | TVs with layout, schedule, carousel; layouts with element types and where they are used |
| `get_layout_format` | The [layout format](LAYOUT-FORMAT.md) – the assistant reads it before building |
| `save_layout` | Create a layout or replace one; invalid parts are repaired and listed, the old version is kept |
| `delete_layout`, `list_layout_versions`, `restore_layout_version` | Delete unused layouts, undo changes, bring back deleted ones |
| `preview` | Picture (960 × 540) of a TV page – as it is now, or with any layout without changing anything (the video window is a placeholder) |
| `set_tv_layout`, `set_tv_schedule`, `set_tv_carousel` | What a TV shows and when |
| `send_ticker`, `end_ticker` | Ticker message along the bottom (optionally red) |
| `show_layout_for_a_while`, `end_layout_for_a_while` | Another layout for N minutes, then back by itself |
| `announce` | Announcement in the middle of the screen, optionally read aloud |
| `upload_picture`, `list_media`, `set_media`, `delete_media` | Pictures for layouts (logo, background) and own media for the video window |
| `list_streams`, `add_stream`, `update_stream`, `remove_stream` | Live cams |
| `list_sources`, `get_source_data`, `add_source_from_curl` | Own data sources and their values |
| `get_log` | Change log |

**Deliberately not possible:** updates, backups and restore, players and their terminal, Home Assistant connection,
passwords, keys and tokens, notifications. Secret headers of data sources are shown as ••••.

## Safety

- Every change appears in System → **Log** as “MCP *user*”; every layout change keeps a version (undo with
  `restore_layout_version` or in the admin).
- The tools tell the assistant which ones only read and which ones change or delete something, so it can ask you first.
- Pictures are fetched only from http/https addresses, JPG/PNG up to 10 MB.
- The preview uses a short-lived headless browser at low priority, one picture at a time; it never loads YouTube.

## Deutsch (kurz)

Seit 0.39 hat SignageCast eine **MCP-Schnittstelle**: Claude oder ein anderer Assistent verwaltet die Inhalte direkt –
Layouts bauen und ändern, Vorschaubild ansehen, Layout einem Fernseher zuweisen (auch Zeitplan, Karussell),
Laufschrift, Layout auf Zeit, Durchsage, Bilder hochladen, Streams und Datenquellen. Anbindung **per SSH** ohne neuen
Port und ohne Token: `ssh tvadmin@<IP> signagecast-mcp` (vorher einmal `ssh-copy-id tvadmin@<IP>`).
Claude Code: `claude mcp add signagecast -- ssh -T tvadmin@<IP> signagecast-mcp`. Docker:
`docker exec -i signagecast signagecast-mcp`. Nicht möglich: Updates, Sicherungen, Player/Terminal, HA-Verbindung,
Passwörter und Schlüssel. Jede Änderung steht im Protokoll („MCP *Benutzer*“), jede Layout-Änderung hinterlässt eine
Version.
