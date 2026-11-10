# Players at another site (Tailscale / Headscale)

[← README](../README.md) · [players](PLAYER.md) · [manual](MANUAL.md) · [Deutsch](#deutsch-kurz)

A Raspberry Pi or PC player at **another place** – a second office, a holiday flat, a branch – shows its TV like a
player at home. It reaches SignageCast through [Tailscale](https://tailscale.com) or through
[Headscale](https://headscale.net) (the same clients, with a control server you run yourself). No port is opened on
any router, no SSH is needed.

**How it works:** a player always asks the server itself (every 15 s) – it never needs an open port. At another site
it only needs a way *to* the server: on its first start it joins your tailnet with a **one-time key** and then talks to
SignageCast at its tailnet address. Display, commands and the **terminal** (remote maintenance) run unchanged.

| | |
|---|---|
| Image | Only the image for **one device** (not the pairing-code image for several) |
| Key | Single use, pre-approved, with a tag (`tag:signagecast-player`), valid 7 days; deleted from the device file after joining |
| Remove | *Remove* in the admin also deletes the device from the tailnet (and withdraws an unused key) |
| Mode | **Direct mode** recommended – the TV page and data go through the tunnel, YouTube comes straight from the local internet. Stream mode works too, but needs several Mbit/s upload at your place all the time (more through relays) |

## 1. Tailscale on the SignageCast server

SignageCast itself has to be in the tailnet. Note its address with `tailscale ip -4` (100.x.y.z).

**Debian / Proxmox container** (the official packages of Tailscale):

```bash
curl -fsSL https://pkgs.tailscale.com/stable/debian/trixie.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/debian/trixie.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt-get update && sudo apt-get install -y tailscale
```

In a Proxmox container without `/dev/net/tun` (the default), let Tailscale run in user space – incoming connections to
port 8890 still work:

```bash
sudo sed -i 's/^FLAGS=.*/FLAGS="--tun=userspace-networking"/' /etc/default/tailscaled
sudo systemctl restart tailscaled
```

Then log in – with a tag, so that the key of the server does not expire:

```bash
sudo tailscale up --advertise-tags=tag:signagecast-server
# Headscale: sudo tailscale up --login-server https://headscale.example.org --advertise-tags=tag:signagecast-server
tailscale ip -4
```

**Docker / Podman / NAS:** install Tailscale on the **host** (QNAP and Synology have a Tailscale package). The
published port 8890 is then reachable at the tailnet address of the host. In the admin enter that address.

## 2. Access for SignageCast

SignageCast creates the one-time keys and deletes removed players through the API.

- **Tailscale:** in the admin console first add the tags to the access rules (`tagOwners`, see 3.), then
  *Settings → OAuth clients* (newer consoles: *Trust credentials*) → new OAuth client with the scopes
  **Auth Keys: Write** and **Devices Core: Write** and the tag `tag:signagecast-player`.
- **Headscale:** `headscale apikeys create --expiration 365d`. The user ID is optional (`headscale users list`); the
  tag must be allowed in the Headscale policy (`tagOwners`).

In SignageCast: **Settings → Remote sites** → service, the tailnet address of SignageCast, the access data, the tag →
*Save* → *Check connection* (shows how many devices are in the tailnet and whether SignageCast was found).

The access data is kept only in `/var/lib/signagecast/fernnetz.json` (readable only by the service). It is shown as
•••• in the admin, it is **not** part of backups and not available to AI assistants (MCP). After a restore on another
machine enter it again.

## 3. Access rule (ACL)

The page shows a suggestion: players may only reach SignageCast on port 8890 (and the stream port), nothing else in
your network.

```json
{
  "tagOwners": {"tag:signagecast-player": ["autogroup:admin"], "tag:signagecast-server": ["autogroup:admin"]},
  "acls": [{"action": "accept", "src": ["tag:signagecast-player"], "dst": ["100.x.y.z:8890,8888"]}]
}
```

**Careful:** as soon as there is an `acls` section, the default rule “everyone may reach everything” is gone. Put your
existing rules (for your own devices, e.g. `{"action": "accept", "src": ["autogroup:member"], "dst": ["*:*"]}`) in
as well.

## 4. Create the player

*Players → Add player* (or *Image again* on an existing card) → tick **At another site (through Tailscale)** → create
and write the image as usual. Take the player to its site and switch it on: Wi-Fi as usual (hotspot and QR code if
needed). Within about a minute it joins the tailnet; its card shows the tailnet address and whether the connection is
**direct** or goes **through a relay**.

Removing the player deletes it from the tailnet as well. If that fails (access data changed, service not reachable)
the admin says so – delete it in the tailnet by hand. The player can no longer fetch anything anyway: its SignageCast
key is invalid at once.

## Safety

- The one-time key is in the image for at most 7 days; after joining it is deleted from the device. A new image for the
  same device withdraws the previous, unused key. The key itself is never stored in SignageCast or shown in the log.
- On the player Tailscale sends **no logs** to Tailscale (`--no-logs-no-support`) and accepts **no DNS and no routes**
  from the tailnet. Its state stays on the boot/data partition, so the player stays logged in after restarts and with
  write protection.
- Traffic is end-to-end encrypted (WireGuard), also through the relays of Tailscale.
- Tailscale on the player is updated with a new image (the system is write-protected).

## Limits

- Images before 0.41 have no Tailscale – create a new image.
- Pairing-code images (one image for several devices) cannot be used at another site – there would have to be a
  reusable key in them.
- The free plan of Tailscale is enough for a few devices; Headscale has no limits.

## Deutsch (kurz)

**Player an einem anderen Standort** (Praxis, Ferienwohnung, Filiale) erreichen SignageCast über **Tailscale** oder
**Headscale** (selbst betrieben). Kein Port am Router, kein SSH. Der Player fragt wie immer selbst beim Server an – jetzt
über dessen Tailnet-Adresse; Anzeige, Befehle und das Terminal laufen unverändert.

1. **Tailscale auf dem SignageCast-Server** (Befehle oben). Proxmox-Container ohne `/dev/net/tun`:
   `FLAGS="--tun=userspace-networking"` in `/etc/default/tailscaled`. Anmelden mit
   `tailscale up --advertise-tags=tag:signagecast-server`, Adresse mit `tailscale ip -4`. Docker/NAS: Tailscale auf
   dem Host.
2. **Zugang:** Tailscale – OAuth-Client mit *Auth Keys: Write* und *Devices Core: Write*, Tag `tag:signagecast-player`;
   Headscale – `headscale apikeys create`. In SignageCast: **Einstellungen → Fernstandorte** → speichern →
   *Verbindung prüfen*. Die Zugangsdaten liegen nur in `fernnetz.json` (Rechte 600), nicht in Sicherungen, nicht im MCP.
3. **Zugriffsregel** aus der Seite übernehmen – Player dürfen nur SignageCast erreichen. Achtung: Ein Abschnitt `acls`
   ersetzt „alle dürfen alles“, eigene Regeln mit hineinnehmen.
4. **Player anlegen** mit Häkchen **An einem anderen Standort** – nur Image je Gerät. Einmal-Schlüssel (7 Tage, nach dem
   Beitritt gelöscht). **Entfernen** löscht den Player auch aus dem Tailnet.

Empfehlung: **Direktmodus** – durch den Tunnel gehen nur Seite und Daten, YouTube kommt vor Ort aus dem Internet.
Images vor 0.41 haben kein Tailscale (neues Image erstellen).
