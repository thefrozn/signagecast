# SignageCast with Claude and other AI assistants (MCP)

[← README](../README.md) · [manual](MANUAL.md) · [layout format](LAYOUT-FORMAT.md) · [Deutsch](#deutsch-kurz)

SignageCast has an **MCP server** ([Model Context Protocol](https://modelcontextprotocol.io)). An assistant such as
Claude (Claude Desktop, Claude Code), Cursor or VS Code can then manage the content directly: build and change
layouts, look at a preview picture, put a layout on a TV, send a ticker message or an announcement, upload pictures,
manage streams and data sources – in plain language, e.g. *“Make a calm layout for the waiting room with our logo and
the opening hours as ticker, show me a preview, then put it on the TV in the waiting room from 8 to 18 o'clock.”*

## Connect a computer (since 0.40) – in the admin, home network only

**Settings → AI assistants → Connect a computer**: give the computer a name, choose the program and whether it may
change content or only read, click *Connect*.

| Program | What you get | Connection |
|---|---|---|
| **Claude Desktop** | A file `signagecast-<name>.mcpb` is downloaded – double-click it (or drag it into Settings → Extensions) and choose *Install*. Start it within one hour. | HTTPS; the file trusts only the certificate of *this* SignageCast. It holds a one-time code, no permanent key: on its first start it fetches its own key and keeps it in `~/.signagecast/` on that computer. |
| **Claude Code** | A command to copy: `claude mcp add --transport http signagecast http://<IP>:8890/mcp --header "Authorization: Bearer sc_…"` | HTTP in the home network with the computer's own key |
| **Cursor** | A button *Open in Cursor* (install link) and the entry for `mcp.json` | as Claude Code |
| **VS Code** | A command `code --add-mcp '{…}'` and the entry for `mcp.json` (Windows PowerShell swallows quotes – use the entry there) | as Claude Code |

- **Every computer has its own access.** The list shows name, program, right and when it was last used.
  **Remove** cuts it off immediately – the assistant on that computer gets “not connected” from then on.
- No computer connected = the interface is off (`/mcp` answers 404).
- The key for Claude Code, Cursor and VS Code is shown **only once**; SignageCast keeps only a checksum of it. Lost it?
  Remove the computer and connect it again.
- It runs on the port of the announcement panel (8890), which understands http and https. Nothing is opened to the
  internet – do not forward this port on your router.
- Claude Code, Cursor and VS Code reject self-made certificates, so they talk plain HTTP in the home network (like the
  panel). In a network you do not trust, use Claude Desktop or SSH (below).
- The certificate is created once (10 years) in `/var/lib/signagecast/tls/`. Set up anew or restored on another
  machine? Connect the Claude Desktop computers again (the list of computers is not part of the backup on purpose).

## Alternative: over SSH (since 0.39)

The assistant starts the MCP server on the SignageCast machine over SSH: `ssh <user>@<host> signagecast-mcp`. No
port, no key in SignageCast – whoever may log in with SSH may use it.

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
the host: `ssh -T user@host docker exec -i signagecast signagecast-mcp`. Connecting a computer in the admin works in
the container too (port 8890 must be published, as for the panel).

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

A computer with the right **only read** sees only the reading tools (status, lists, layouts, preview, log).

**Deliberately not possible:** updates, backups and restore, players and their terminal, Home Assistant connection,
passwords, keys and tokens, notifications, connecting further computers. Secret headers of data sources are shown as
••••.

## Safety

- Every change appears in System → **Log** as “MCP *computer*” (or “MCP *user*” over SSH); every layout change keeps
  a version (undo with `restore_layout_version` or in the admin). Connecting and removing computers is logged too.
- The tools tell the assistant which ones only read and which ones change or delete something, so it can ask you first.
- Wrong keys or codes: one second delay each, more than 10 per minute from one address → blocked for a minute.
- Requests from web pages in a browser are refused (header `Origin`), so a web page cannot use your assistant's access.
- Content that the assistant reads (data sources, web pages, stream titles) can contain text that tries to give it
  instructions. Let it ask before changes, give computers that only need to look the right *only read*, and check the
  log now and then.
- Pictures are fetched only from http/https addresses, JPG/PNG up to 10 MB.
- The preview uses a short-lived headless browser at low priority, one picture at a time; it never loads YouTube.

## Deutsch (kurz)

SignageCast hat eine **MCP-Schnittstelle**: Claude, Cursor, VS Code oder ein anderer Assistent verwaltet die Inhalte
direkt – Layouts bauen und ändern, Vorschaubild ansehen, Layout einem Fernseher zuweisen (auch Zeitplan, Karussell),
Laufschrift, Layout auf Zeit, Durchsage, Bilder hochladen, Streams und Datenquellen.

**Seit 0.40 per Klick im Heimnetz:** Einstellungen → **KI-Assistenten** → *Computer verbinden*: Name, Programm und Recht
(*Inhalte ändern* oder *nur lesen*) wählen.
- **Claude Desktop:** Datei `.mcpb` wird heruntergeladen – doppelt anklicken, *Installieren*, innerhalb einer Stunde
  starten. Verschlüsselt (HTTPS), die Datei vertraut nur diesem SignageCast und enthält keinen dauerhaften Schlüssel.
- **Claude Code / Cursor / VS Code:** fertiger Befehl bzw. Link mit eigenem Schlüssel je Computer (nur einmal angezeigt),
  im Heimnetz unverschlüsselt wie das Pult.
- **Entfernen** in der Liste sperrt den Computer sofort. Ohne verbundenen Computer ist die Schnittstelle aus.
- Port 8890 (wie das Pult) – nicht ins Internet weiterleiten.

**Alternativ per SSH** ohne Schlüssel in SignageCast: `ssh tvadmin@<IP> signagecast-mcp` (vorher einmal
`ssh-copy-id tvadmin@<IP>`). Claude Code: `claude mcp add signagecast -- ssh -T tvadmin@<IP> signagecast-mcp`.
Docker: `docker exec -i signagecast signagecast-mcp`.

Nicht möglich: Updates, Sicherungen, Player/Terminal, HA-Verbindung, Passwörter und Schlüssel, weitere Computer
verbinden. Jede Änderung steht im Protokoll („MCP *Computer*“), jede Layout-Änderung hinterlässt eine Version.
