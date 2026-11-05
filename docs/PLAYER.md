# Raspberry Pi as player

[← README](../README.md) · [installation](INSTALL.md) · [hardware](HARDWARE.md) · *Deutsch weiter unten*

A Raspberry Pi at the TV shows the finished SignageCast stream via HDMI – also on TVs whose browser cannot play it, or
on monitors without any smart function. SignageCast itself keeps running on your server (x86); the Pi only plays.
You create a ready SD card image in the admin and manage all Pis there – no command line, no keyboard at the Pi.

> **New in 0.23 and still experimental.** Image building, download and management are tested; playback, Wi-Fi setup
> and HDMI-CEC on real Pis not yet on every model. Feedback in an [issue](https://github.com/thefrozn/signagecast/issues)
> helps a lot (“works on Pi 4 with TV X”).

## What you need

| | |
|---|---|
| **Pi 5, Pi 4, Pi 400** (also CM4) | up to **4K** – the TV in SignageCast can stay on H.265 / 4K |
| **Pi 3, Zero 2 W** | **Full HD with H.264 only** – set the TV in SignageCast to codec *H.264* and resolution *Full HD* |
| SD card | 8 GB or more, brand card (A1/A2) |
| Power supply | the **official** one – cheap ones cause under-voltage (the admin warns) |
| HDMI cable | Pi 4/5: micro HDMI, Zero 2 W: mini HDMI |
| On your computer | [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [balenaEtcher](https://etcher.balena.io/) |

The Pis reach the server on the **webhook port 8890**. Native installations (Proxmox, Debian) need nothing extra; with
**Docker / QNAP / Synology** add `- "8890:8890"` under `ports:` (or `-p 8890:8890`).

## Step by step

1. Admin → **TVs → Players (Raspberry Pi)** → **Download player image** (once, about 700 MB; checked with the project's
   signature).
2. **Add player:** name (e.g. *Waiting room*), the TV it shows, the model, and the network: **LAN cable** or **Wi-Fi**
   (name and password – or a saved one). Click **Create and download image**.
3. Open **Raspberry Pi Imager** → choose your device → operating system: at the bottom **Use custom** → the downloaded
   `signagecast-player-….img.gz` → your SD card → *Next*. When asked about **OS customisation: No** – everything is
   already in the image. (balenaEtcher: choose file, choose card, *Flash*.)
4. Put the card into the Pi, HDMI to the TV, power on. The first start takes **2–3 minutes** (the Pi restarts once to
   switch on write protection). Then the picture appears and the player shows up as *online* in the admin.

**No network?** If the Pi does not find the Wi-Fi (wrong password, other place), after 2 minutes it opens its own Wi-Fi
**SignageCast-<name>** and shows a **QR code** on the TV. Scan it with your phone, the setup page opens by itself
(otherwise open `http://10.42.0.1`), choose your Wi-Fi and enter the password. Every 5 minutes the Pi tries the known
networks again – after a power cut the router is often slower than the Pi.

## In the admin

- **Status** per Pi: online/offline, model, IP, Wi-Fi and signal, screen name, video (codec, resolution, hardware
  decoding), temperature, last system update; warnings for under-voltage, heat, missing HDMI and settings that do not
  fit (e.g. Pi 3 with H.265 or 4K). A notification is sent when a Pi has not reported for 5 minutes.
- **Buttons:** screenshot, show name (30 s on the TV – find the right Pi), TV on/off via HDMI-CEC, restart player,
  restart Pi, system update now, fetch log.
- **Settings:** name, TV, rotation (0/90/180/270°), output resolution, volume, *switch the TV on and off by schedule*
  (when the TV's layout is “black”, via HDMI-CEC – enable CEC on the TV: Samsung *Anynet+*, LG *SimpLink*, Sony
  *Bravia Sync*), write protection, weekly system updates (Sunday 3 am), hardware or CPU decoding.
- **Change Wi-Fi:** the Pi tries the new network; if it cannot reach the server with it, it goes back to the old one.
  Previous networks stay as fallback.
- **Download image again** for a new card (same key – an old card keeps working). **Remove** makes the key invalid.

## Direct mode (since 0.24, experimental)

Under *Settings → Display* a Pi 4 or Pi 5 can show the TV page **itself** instead of the stream: Chromium runs in the
kiosk shell `cage` (no desktop) and opens the page from your server. Text and ticker are sharp, there is no stream
delay, and the server does not need to render or encode anything for this Pi. Sound (radio, announcements, gong) comes
from the Pi's HDMI.

- The Pi draws in **Full HD** (a 4K TV upscales); *Output 4K* forces 4K, which is usually too much for the Pi.
- **Pi 3 and Zero 2 W** always use the stream (not enough memory); the setting is hidden for them.
- Videos and cameras are decoded by the Pi – they may stutter, especially H.264 on the Pi 5 (no hardware decoder).
- **Fallback:** if the browser crashes or the page does not load three times within 10 minutes, the Pi shows the
  stream for one hour; the admin shows a note. *Restart player* tries direct mode again right away.
- Images created **before 0.24** have no browser – the admin says so; download and flash a new image.
- Security: the Pi opens `http://<server>:8890/anzeige/<key>`. The key is derived from the device key and only gives
  access to the page of **its own TV** (no admin API; only the cameras in that TV's layout). Removing the Pi makes it
  invalid at once.

## How it works (short)

- The image is the official **Raspberry Pi OS Lite (64 bit)** plus `mpv`, `qrencode`, `overlayroot`, for direct mode
  `chromium`, `cage`, `seatd`, `grim`, `wlr-randr`, and the player
  (`player/agent.py`), built by GitHub Actions for every release (`player/bauen.sh`). The admin writes the device file
  (server address, device key, Wi-Fi) into a placeholder on the boot partition while you download – no mounting, so it
  works in Docker and on a NAS too.
- **Pull only:** the Pi reports every 15 s to `http://<server>:8890/player/…` and picks up settings and commands. No
  port is open on the Pi (except port 80 for the setup page while its own hotspot runs).
- Every request and every answer is signed with the device key (HMAC-SHA256); the key itself never travels over the
  network. The Wi-Fi password is not stored in plain text – only the WPA key derived from it (on the card and, if you
  choose so, in the admin; backups contain it only “with credentials”).
- **Write protection** (on by default): the system runs in memory, the SD card is not written – power cuts do no harm.
  Everything that must survive a restart is in `signagecast.json` on the boot partition. System updates switch
  write protection off for a moment and restart twice.
- The player software updates itself from your server; a new image is only needed for a new Raspberry Pi OS.

## If something does not work

| Problem | Solution |
|---|---|
| “Server not reachable” on the TV | Port 8890 published (Docker/NAS)? Under *Advanced* the server address must be the IP in your home network. |
| QR code appears again after setup | Wrong Wi-Fi password – scan again. 5 GHz-only networks: Pi 3 B and Zero 2 W only support 2.4 GHz. |
| Black screen, Pi online | Check *Video* in the admin; Pi 3/Zero 2 W: set the TV to H.264 / Full HD; try *Video decoding: CPU only*. |
| Under-voltage warning | Use the official power supply and a short cable. |
| TV on/off does nothing | Enable CEC on the TV; some TVs only switch on via CEC from standby, not when fully off. |
| Direct mode: stream instead of page | Note in the admin: image before 0.24 (flash a new one) or fallback after browser problems (*Restart player*). |

---

# Deutsch: Raspberry Pi als Player

Ein Raspberry Pi am Fernseher zeigt den fertigen SignageCast-Stream per HDMI – auch an Fernsehern, deren Browser ihn
nicht abspielt, oder an Monitoren ohne Smart-Funktion. SignageCast läuft weiter auf deinem Server (x86), der Pi spielt
nur ab. Das fertige Image für die SD-Karte erstellst du in der Verwaltung und verwaltest dort alle Pis – ohne
Kommandozeile, ohne Tastatur am Pi.

> **Neu in 0.23 und noch experimentell.** Image-Bau, Download und Verwaltung sind getestet, Wiedergabe, WLAN-Einrichtung
> und HDMI-CEC auf echten Pis noch nicht auf jedem Modell. Rückmeldungen in einem
> [Issue](https://github.com/thefrozn/signagecast/issues) helfen sehr („läuft auf Pi 4 mit Fernseher X“).

## Was du brauchst

| | |
|---|---|
| **Pi 5, Pi 4, Pi 400** (auch CM4) | bis **4K** – der Fernseher in SignageCast kann auf H.265 / 4K bleiben |
| **Pi 3, Zero 2 W** | **nur Full HD mit H.264** – den Fernseher in SignageCast auf Codec *H.264* und Auflösung *Full HD* stellen |
| SD-Karte | ab 8 GB, Markenkarte (A1/A2) |
| Netzteil | das **offizielle** – billige führen zu Unterspannung (die Verwaltung warnt) |
| HDMI-Kabel | Pi 4/5: Micro-HDMI, Zero 2 W: Mini-HDMI |
| Am Computer | [Raspberry Pi Imager](https://www.raspberrypi.com/software/) oder [balenaEtcher](https://etcher.balena.io/) |

Die Pis erreichen den Server über den **Webhook-Port 8890**. Native Installationen (Proxmox, Debian) brauchen nichts
weiter; bei **Docker / QNAP / Synology** unter `ports:` die Zeile `- "8890:8890"` ergänzen (bzw. `-p 8890:8890`).

## Schritt für Schritt

1. Verwaltung → **Fernseher → Player (Raspberry Pi)** → **Player-Image laden** (einmalig, etwa 700 MB; mit der Signatur
   des Projekts geprüft).
2. **Player hinzufügen:** Name (z. B. *Wartezimmer*), welcher Fernseher gezeigt wird, Modell und Netzwerk: **LAN-Kabel**
   oder **WLAN** (Name und Passwort – oder ein gespeichertes). **Image erstellen und herunterladen** klicken.
3. **Raspberry Pi Imager** öffnen → Gerät wählen → Betriebssystem: ganz unten **Eigenes Image** (Use custom) → die
   heruntergeladene `signagecast-player-….img.gz` → SD-Karte → *Weiter*. Frage nach **OS-Anpassungen: Nein** – alles
   steht schon im Image. (balenaEtcher: Datei wählen, Karte wählen, *Flash*.)
4. Karte in den Pi, HDMI an den Fernseher, Strom an. Der erste Start dauert **2–3 Minuten** (der Pi startet einmal neu,
   um den Schreibschutz einzuschalten). Dann erscheint das Bild, und der Player steht in der Verwaltung auf *online*.

**Kein Netz?** Findet der Pi das WLAN nicht (falsches Passwort, anderer Ort), öffnet er nach 2 Minuten ein eigenes WLAN
**SignageCast-<Name>** und zeigt auf dem Fernseher einen **QR-Code**. Mit dem Handy scannen – die Einrichtungsseite
öffnet sich von selbst (sonst `http://10.42.0.1` aufrufen) –, WLAN wählen, Passwort eingeben. Alle 5 Minuten versucht
der Pi die bekannten WLANs erneut – nach einem Stromausfall ist der Router oft langsamer als der Pi.

## In der Verwaltung

- **Status** je Pi: online/offline, Modell, IP, WLAN und Signal, Name des Bildschirms, Video (Codec, Auflösung,
  Hardware-Dekodierung), Temperatur, letztes Systemupdate; Warnungen bei Unterspannung, Hitze, fehlendem HDMI und
  unpassenden Einstellungen (z. B. Pi 3 mit H.265 oder 4K). Meldet sich ein Pi 5 Minuten nicht, kommt eine Benachrichtigung.
- **Knöpfe:** Bildschirmfoto, Name anzeigen (30 s auf dem Fernseher – den richtigen Pi finden), TV ein/aus per HDMI-CEC,
  Player neu starten, Pi neu starten, Systemupdate jetzt, Protokoll holen.
- **Einstellungen:** Name, Fernseher, Drehung (0/90/180/270°), Ausgabe-Auflösung, Lautstärke, *Fernseher nach Zeitplan
  ein- und ausschalten* (wenn das Layout des Fernsehers „schwarz“ ist, per HDMI-CEC – CEC am Fernseher einschalten:
  Samsung *Anynet+*, LG *SimpLink*, Sony *Bravia Sync*), Schreibschutz, wöchentliche Systemupdates (So 3 Uhr), Hardware-
  oder CPU-Dekodierung.
- **WLAN ändern:** Der Pi probiert das neue WLAN aus; erreicht er den Server damit nicht, kehrt er zum alten zurück.
  Bisherige WLANs bleiben als Ersatz.
- **Image erneut herunterladen** für eine neue Karte (gleicher Schlüssel – eine alte Karte läuft weiter). **Entfernen**
  macht den Schlüssel ungültig.

## Direktmodus (seit 0.24, experimentell)

Unter *Einstellungen → Anzeige* zeigt ein Pi 4 oder Pi 5 die TV-Seite **selbst** statt des Streams: Chromium läuft im
Kiosk-Rahmen `cage` (ohne Desktop) und öffnet die Seite von deinem Server. Schrift und Laufband sind gestochen scharf,
es gibt keine Stream-Verzögerung, und der Server muss für diesen Pi nichts zeichnen oder kodieren. Der Ton (Radio,
Durchsagen, Gong) kommt aus dem HDMI des Pi.

- Der Pi zeichnet in **Full HD** (ein 4K-Fernseher rechnet hoch); *Ausgabe 4K* erzwingt 4K, das ist für den Pi meist zu viel.
- **Pi 3 und Zero 2 W** zeigen immer den Stream (zu wenig Speicher); die Einstellung ist dort ausgeblendet.
- Videos und Kameras dekodiert der Pi – sie können ruckeln, vor allem H.264 auf dem Pi 5 (ohne Hardware-Dekoder).
- **Rückfall:** Stürzt der Browser ab oder lädt die Seite dreimal in 10 Minuten nicht, zeigt der Pi eine Stunde lang den
  Stream; die Verwaltung zeigt einen Hinweis. *Player neu starten* versucht den Direktmodus sofort wieder.
- Images von **vor 0.24** haben keinen Browser – die Verwaltung sagt das; neues Image herunterladen und flashen.
- Sicherheit: Der Pi öffnet `http://<Server>:8890/anzeige/<Schlüssel>`. Der Schlüssel ist aus dem Geräteschlüssel
  abgeleitet und gibt nur die Seite **seines Fernsehers** frei (keine Verwaltungs-API; nur die Kameras aus dessen
  Layout). Entfernen macht ihn sofort ungültig.

## Technik (kurz)

- Das Image ist das offizielle **Raspberry Pi OS Lite (64 bit)** mit `mpv`, `qrencode`, `overlayroot`, für den
  Direktmodus `chromium`, `cage`, `seatd`, `grim`, `wlr-randr`, und dem Player
  (`player/agent.py`), gebaut von GitHub Actions zu jedem Release (`player/bauen.sh`). Die Verwaltung schreibt die
  Gerätedatei (Server-Adresse, Geräteschlüssel, WLAN) beim Herunterladen in einen Platzhalter auf der Boot-Partition –
  ohne Einhängen, darum geht es auch im Docker-Container und auf dem NAS.
- **Nur Abholen:** Der Pi meldet sich alle 15 s unter `http://<Server>:8890/player/…` und holt Einstellungen und Befehle.
  Am Pi ist kein Port offen (außer Port 80 für die Einrichtungsseite, solange sein eigener Hotspot läuft).
- Jede Anfrage und jede Antwort ist mit dem Geräteschlüssel signiert (HMAC-SHA256); der Schlüssel selbst geht nie übers
  Netz. Das WLAN-Passwort steht nirgends im Klartext – nur der daraus abgeleitete WPA-Schlüssel (auf der Karte und, wenn
  du es wählst, in der Verwaltung; Sicherungen enthalten ihn nur „mit Zugangsdaten“).
- **Schreibschutz** (Standard): Das System läuft im Arbeitsspeicher, die SD-Karte wird nicht beschrieben – Stromausfälle
  schaden nicht. Was einen Neustart überstehen muss, steht in `signagecast.json` auf der Boot-Partition. Systemupdates
  schalten den Schreibschutz kurz aus und starten zweimal neu.
- Die Player-Software aktualisiert sich von deinem Server; ein neues Image braucht es nur für ein neues Raspberry Pi OS.

## Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| „Server nicht erreichbar“ auf dem Fernseher | Port 8890 freigegeben (Docker/NAS)? Unter *Erweitert* muss die Server-Adresse die IP im Heimnetz sein. |
| QR-Code erscheint nach der Einrichtung wieder | WLAN-Passwort falsch – erneut scannen. Reine 5-GHz-Netze: Pi 3 B und Zero 2 W können nur 2,4 GHz. |
| Schwarzes Bild, Pi online | In der Verwaltung *Video* ansehen; Pi 3/Zero 2 W: Fernseher auf H.264 / Full HD; *Video-Dekodierung: nur CPU* probieren. |
| Warnung Unterspannung | Offizielles Netzteil und kurzes Kabel nehmen. |
| TV ein/aus tut nichts | CEC am Fernseher einschalten; manche Fernseher lassen sich per CEC nur aus dem Standby einschalten. |
| Direktmodus: Stream statt Seite | Hinweis in der Verwaltung: Image von vor 0.24 (neues flashen) oder Rückfall nach Browser-Problemen (*Player neu starten*). |
