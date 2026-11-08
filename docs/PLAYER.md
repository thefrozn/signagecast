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
| Memory (RAM) | stream: **1 GB** is enough (Zero 2 W: 512 MB) · [direct mode](#direct-mode-since-024-experimental): **at least 2 GB, better 4 GB** |
| SD card | 8 GB or more, brand card (A1/A2) |
| Power supply | the **official** one – cheap ones cause under-voltage (the admin warns) |
| HDMI cable | Pi 4/5: micro HDMI, Zero 2 W: mini HDMI |
| On your computer | [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [balenaEtcher](https://etcher.balena.io/) |

The Pis reach the server on the **webhook port 8890**. Native installations (Proxmox, Debian) need nothing extra; with
**Docker / QNAP / Synology** add `- "8890:8890"` under `ports:` (or `-p 8890:8890`).

## Step by step

1. Admin → **TVs → Players** → **Download player image** (once, about 850 MB; checked with the project's
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

## One image for several Pis (pairing code, since 0.25)

Instead of one image per screen you can flash **the same image onto any number of cards**:

1. Under **Pair a player**, choose the network and click **Download image for several devices**
   (`signagecast-player-kopplung.img.gz` – server address and Wi-Fi, but no key).
2. Flash it as above, Pi to the TV, power on. After the start the TV shows **“Code: 123 456”**.
3. In the admin under **Pair a player** enter the code, a name and the TV → **Pair**. A few seconds later the Pi shows the
   picture; from then on it is an ordinary player (settings, buttons, *Download image again*).

The admin shows how many Pis are currently showing a code (model and IP, never the code). A code is valid for 10
minutes, then the Pi shows a new one. Security: the Pi and the server negotiate the key with Diffie-Hellman (RFC 3526,
2048 bit); the code is derived from it. Someone in the network who intercepts the exchange would get a different code –
so only the Pi whose code you read off the TV gets paired, and the key never travels over the network. At most 20
open and 60 new requests per hour. Pairing needs an image from 0.25 on.

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
- **Memory:** at least **2 GB**, better **4 GB** – especially with videos, cameras, web pages or 4K output. With write
  protection the system runs in memory, so the browser's cache (up to 64 MB) and profile are kept there too. A Pi with
  less than 2 GB reports its memory, and its card shows a note; direct mode stays allowed. These are estimates, not yet
  measured on real Pis.
- Videos and cameras are decoded by the Pi – they may stutter, especially H.264 on the Pi 5 (no hardware decoder).
- **Fallback:** if the browser crashes or the page does not load three times within 10 minutes, the Pi shows the
  stream for one hour; the admin shows a note. *Restart player* tries direct mode again right away.
- Images created **before 0.24** have no browser – the admin says so; download and flash a new image.
- Security: the Pi opens `http://<server>:8890/anzeige/<key>`. The key is derived from the device key and only gives
  access to the page of **its own TV** (no admin API; only the cameras in that TV's layout). Removing the Pi makes it
  invalid at once.

## Remote maintenance – terminal in the browser (since 0.33)

*Experimental: tested with a simulated Pi (the real agent code), not yet on a real Pi.*

A Pi card in the admin can open a **terminal** to the Pi: a root shell in the browser, drawn with xterm.js like the
terminal in Cockpit – `top`, `nano`, tab completion, copy and paste, the size follows the window.

- **Off by default.** The Pi only accepts a session if *it* allows it: tick *Allow remote maintenance* when creating
  the image (also for the image for several Pis), or switch it on/off on the Pi's **setup page** (hotspot, see above).
  Even someone who takes over the server cannot get onto Pis that do not allow it – the Pi checks this itself.
- **No open port, no SSH:** the Pi learns about a session at its next report (up to 15 s) and then talks to the server
  through two signed requests of its own. Input and output are **encrypted** (port 8890 is plain HTTP): key derived
  from the device key, SHAKE-256 key stream with a fresh nonce per message; request signatures protect against changes,
  sequence numbers against replayed requests.
- **Limits:** a session ends after 10 minutes without input and after 60 minutes at the latest (server and Pi both check),
  and when the admin window is closed. One session per Pi.
- **Visible:** the TV shows *Remote maintenance active* meanwhile (stream mode: mpv overlay; direct mode: the TV page).
- **Log:** every session (who, when, how long, why it ended) – shown in the Pi's card, kept in
  `/var/lib/signagecast/fernwartung.json`. Input and output are **not** logged (passwords could end up there).
- **Write protection:** with write protection on, changes are gone after a restart – the terminal says so; switch it
  off in the Pi's settings first if a change must stay.
- Without new image: Pis update their agent from the server by themselves; switch remote maintenance on via the setup
  page or write a new image with the box ticked.

## PC as player (since 0.36, experimental)

*Tested in a UEFI virtual machine with Secure Boot (image build, boot, direct mode, stream, pairing, USB data partition,
remote maintenance); not yet on many real PCs. Feedback helps.*

An ordinary **PC, mini PC or thin client** (x86-64) becomes a player: it starts from a **USB stick** without touching
its disk and shows the TV page itself in **direct mode** (default for PCs) – sharp, without delay, and the server
encodes nothing for it. Everything else works as with a Pi: settings, screenshot, remote maintenance, pairing code,
fallback to the stream.

| | |
|---|---|
| Computer | 64-bit with **UEFI** (roughly 2013 or newer). **Secure Boot may stay on** (Debian's signed shim, GRUB and kernel). No legacy BIOS. |
| Memory | **at least 4 GB** |
| Graphics | **Intel or AMD**: videos decoded in hardware (VAAPI). NVIDIA works, videos then on the CPU. |
| USB stick | 4 GB or more |
| Network | LAN cable (nothing to set up) or Wi-Fi (hotspot setup as with the Pi, if the Wi-Fi card can do it) |

1. Admin → **TVs → Players** → **PC image: Download** (once, about 750 MB; checked with the project's signature).
2. **Add player** → model **PC** → choose the format:
   - **USB stick (.img.gz)** – write with balenaEtcher, Raspberry Pi Imager (*Use custom*) or Rufus (choose *DD image*).
     The PC keeps pairing, Wi-Fi and player updates on the stick.
   - **ISO (.iso)** – for Ventoy, CD or a virtual machine. Same system; changes made on the device only last until the
     next restart (the settings come from the server anyway).
3. Plug in the stick, connect the screen, start from USB (boot menu usually F12, F11, F8 or Esc). First start 1–2 min.

**One image for several PCs:** *Pair a player* → *For: PC* – as with the Pi, every PC shows a code.

**Differences to the Pi:** the system is a **live system** – always write-protected, power cuts do no harm. There are
**no system updates**: new software (also browser security fixes) comes with a new image – *Download image again*, rewrite
the stick. The player software itself updates from your server as usual. Usually **no HDMI-CEC** (TV on/off). The
picture can go to any connector (HDMI, DisplayPort, DVI, VGA); sound goes to the HDMI/DisplayPort output with a screen.

**How it is built:** Debian 13 (amd64) with live-boot, built by GitHub Actions with every release
(`player/pc/bauen.sh`, SBOM next to it). One file is both an ISO and a USB image: ISO9660 with the system and the
placeholder `signagecast.json`, partition 2 the EFI system partition, partition 3 a small FAT partition `SCDATEN` for
the player's data. No desktop, no SSH, no login on the console.

## Browser device – link only (since 0.36)

For devices that already have a browser – smart TV, Fire TV stick, a PC with a ready kiosk live CD (e.g. Porteus Kiosk)
or just a browser in full screen. *Add player* → model **Browser device** → *Create link*. The admin shows a secret link
`http://<server>:8890/anzeige/<key>` that shows exactly this TV – set it as the start page.

- “Online” means: the page fetches its data (every 15 s). A notification comes after 5 minutes without (as with the Pi).
- No image, no screenshot, no fallback to the stream, no remote maintenance.
- The link only opens this TV's page, never the admin. Treat it like a password; port 8890 is unencrypted HTTP – only
  in your own network. *Create new link* makes the old one invalid immediately, *Remove* as well.

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
| Arbeitsspeicher (RAM) | Stream: **1 GB** reicht (Zero 2 W: 512 MB) · [Direktmodus](#direktmodus-seit-024-experimentell): **mindestens 2 GB, besser 4 GB** |
| SD-Karte | ab 8 GB, Markenkarte (A1/A2) |
| Netzteil | das **offizielle** – billige führen zu Unterspannung (die Verwaltung warnt) |
| HDMI-Kabel | Pi 4/5: Micro-HDMI, Zero 2 W: Mini-HDMI |
| Am Computer | [Raspberry Pi Imager](https://www.raspberrypi.com/software/) oder [balenaEtcher](https://etcher.balena.io/) |

Die Pis erreichen den Server über den **Webhook-Port 8890**. Native Installationen (Proxmox, Debian) brauchen nichts
weiter; bei **Docker / QNAP / Synology** unter `ports:` die Zeile `- "8890:8890"` ergänzen (bzw. `-p 8890:8890`).

## Schritt für Schritt

1. Verwaltung → **Fernseher → Player** → **Player-Image laden** (einmalig, etwa 850 MB; mit der Signatur
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

## Ein Image für mehrere Pis (Kopplungscode, seit 0.25)

Statt eines Images je Bildschirm kannst du **dasselbe Image auf beliebig viele Karten** schreiben:

1. Unter **Player koppeln** das Netzwerk wählen und **Image für mehrere Geräte herunterladen** klicken
   (`signagecast-player-kopplung.img.gz` – Server-Adresse und WLAN, aber kein Schlüssel).
2. Wie oben flashen, Pi an den Fernseher, Strom an. Nach dem Start zeigt der Fernseher **„Code: 123 456“**.
3. In der Verwaltung unter **Player koppeln** Code, Name und Fernseher eingeben → **Koppeln**. Wenige Sekunden später zeigt
   der Pi das Bild; danach ist er ein ganz normaler Player (Einstellungen, Knöpfe, *Image erneut herunterladen*).

Die Verwaltung zeigt, wie viele Pis gerade einen Code anzeigen (Modell und IP, nie den Code). Ein Code gilt 10 Minuten,
dann zeigt der Pi einen neuen. Sicherheit: Pi und Server handeln den Schlüssel per Diffie-Hellman aus (RFC 3526,
2048 Bit), der Code ist daraus abgeleitet. Wer sich im Netz dazwischenschiebt, bekäme einen anderen Code – gekoppelt
wird nur der Pi, dessen Code du vom Fernseher abliest, und der Schlüssel geht nie übers Netz. Höchstens 20 offene und
60 neue Anfragen je Stunde. Die Kopplung braucht ein Image ab 0.25.

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
- **Arbeitsspeicher:** mindestens **2 GB**, besser **4 GB** – vor allem mit Videos, Kameras, Webseiten oder 4K-Ausgabe.
  Mit Schreibschutz läuft das System im Arbeitsspeicher, also liegen auch Cache (bis 64 MB) und Profil des Browsers dort.
  Ein Pi mit weniger als 2 GB meldet seinen Speicher, seine Karte zeigt dann einen Hinweis; der Direktmodus bleibt
  erlaubt. Die Werte sind geschätzt, auf echten Pis noch nicht gemessen.
- Videos und Kameras dekodiert der Pi – sie können ruckeln, vor allem H.264 auf dem Pi 5 (ohne Hardware-Dekoder).
- **Rückfall:** Stürzt der Browser ab oder lädt die Seite dreimal in 10 Minuten nicht, zeigt der Pi eine Stunde lang den
  Stream; die Verwaltung zeigt einen Hinweis. *Player neu starten* versucht den Direktmodus sofort wieder.
- Images von **vor 0.24** haben keinen Browser – die Verwaltung sagt das; neues Image herunterladen und flashen.
- Sicherheit: Der Pi öffnet `http://<Server>:8890/anzeige/<Schlüssel>`. Der Schlüssel ist aus dem Geräteschlüssel
  abgeleitet und gibt nur die Seite **seines Fernsehers** frei (keine Verwaltungs-API; nur die Kameras aus dessen
  Layout). Entfernen macht ihn sofort ungültig.

## Fernwartung – Terminal im Browser (seit 0.33)

*Experimentell: mit einem simulierten Pi (echter Agent-Code) getestet, noch nicht auf einem echten Pi.*

In der Karte eines Pi öffnet *Terminal* eine **Shell (root) auf dem Pi im Browser**, gezeichnet mit xterm.js wie das
Terminal in Cockpit – `top`, `nano`, Tab-Ergänzung, Kopieren und Einfügen, die Größe folgt dem Fenster.

- **Ab Werk aus.** Der Pi lässt eine Sitzung nur zu, wenn *er* es erlaubt: beim Erstellen des Images *Fernwartung
  erlauben* ankreuzen (auch beim Image für mehrere Pis) oder auf der **Einrichtungsseite** des Pi (Hotspot, siehe oben)
  ein- und ausschalten. Auch wer den Server übernimmt, kommt so nicht auf Pis, die es nicht erlauben – das prüft der Pi selbst.
- **Kein offener Port, kein SSH:** Der Pi erfährt bei seiner nächsten Meldung (bis zu 15 s) von der Sitzung und spricht
  dann über zwei eigene, signierte Anfragen mit dem Server. Ein- und Ausgabe sind **verschlüsselt** (Port 8890 ist
  unverschlüsseltes HTTP): Schlüssel aus dem Geräteschlüssel abgeleitet, SHAKE-256 als Schlüsselstrom mit neuer Nonce
  je Nachricht; die Signaturen schützen vor Veränderung, laufende Nummern vor wieder eingespielten Anfragen.
- **Grenzen:** Eine Sitzung endet nach 10 Minuten ohne Eingabe und spätestens nach 60 Minuten (prüfen Server und Pi),
  außerdem, wenn das Fenster in der Verwaltung zu ist. Eine Sitzung je Pi.
- **Sichtbar:** Auf dem Fernseher steht solange *Fernwartung aktiv* (Stream: Einblendung von mpv; Direktmodus: die TV-Seite).
- **Protokoll:** jede Sitzung (wer, wann, wie lange, warum beendet) – in der Karte des Pi, gespeichert in
  `/var/lib/signagecast/fernwartung.json`. Ein- und Ausgaben werden **nicht** mitgeschrieben (dort könnten Passwörter stehen).
- **Schreibschutz:** Ist er an, sind Änderungen nach einem Neustart weg – das Terminal sagt es; soll etwas bleiben,
  vorher in den Einstellungen des Pi ausschalten.
- Ohne neues Image: Die Pis holen sich den neuen Agent selbst vom Server; Fernwartung dann über die Einrichtungsseite
  einschalten oder ein neues Image mit Haken schreiben.

## PC als Player (seit 0.36, experimentell)

*Getestet in einer virtuellen Maschine mit UEFI und Secure Boot (Image-Bau, Start, Direktmodus, Stream, Kopplung,
Datenpartition auf dem Stick, Fernwartung); noch nicht auf vielen echten PCs. Rückmeldungen helfen.*

Ein normaler **PC, Mini-PC oder Thin Client** (x86-64) wird zum Player: Er startet vom **USB-Stick**, ohne seine
Festplatte anzufassen, und zeigt die TV-Seite im **Direktmodus** selbst (Standard bei PCs) – gestochen scharf, ohne
Verzögerung, und der Server kodiert für ihn nichts. Alles andere wie beim Pi: Einstellungen, Bildschirmfoto,
Fernwartung, Kopplungscode, Rückfall auf den Stream.

| | |
|---|---|
| Rechner | 64 Bit mit **UEFI** (etwa ab 2013). **Secure Boot darf an bleiben** (signierter shim, GRUB und Kernel von Debian). Kein altes BIOS. |
| Arbeitsspeicher | **mindestens 4 GB** |
| Grafik | **Intel oder AMD**: Videos per Hardware (VAAPI). NVIDIA geht, Videos dann per CPU. |
| USB-Stick | ab 4 GB |
| Netz | LAN-Kabel (nichts einzurichten) oder WLAN (Hotspot-Einrichtung wie beim Pi, wenn die WLAN-Karte das kann) |

1. Verwaltung → **Fernseher → Player** → **PC-Image laden** (einmalig etwa 750 MB, mit der Signatur des Projekts geprüft).
2. **Player hinzufügen** → Modell **PC** → Format wählen:
   - **USB-Stick (.img.gz)** – mit balenaEtcher, Raspberry Pi Imager („Eigenes Image“) oder Rufus („DD-Image“) schreiben.
     Der PC merkt sich Kopplung, WLAN und Updates des Players auf dem Stick.
   - **ISO (.iso)** – für Ventoy, CD oder eine virtuelle Maschine. Dasselbe System; am Gerät Geändertes gilt nur bis
     zum Neustart (die Einstellungen kommen ohnehin vom Server).
3. Stick einstecken, Bildschirm anschließen, vom USB-Stick starten (Startmenü meist F12, F11, F8 oder Esc). Erster Start 1–2 min.

**Ein Image für mehrere PCs:** *Player koppeln* → *Für: PC* – wie beim Pi zeigt jeder PC einen Code.

**Unterschiede zum Pi:** Das System ist ein **Live-System** – immer schreibgeschützt, Stromausfälle schaden nicht. Es
gibt **keine Systemupdates**: neue Software (auch Sicherheitsupdates des Browsers) kommt mit einem neuen Image –
*Image erneut herunterladen*, Stick neu beschreiben. Die Player-Software selbst aktualisiert sich wie gewohnt vom Server.
Meist **kein HDMI-CEC** (TV ein/aus). Das Bild geht an jeden Anschluss (HDMI, DisplayPort, DVI, VGA), der Ton an den
HDMI-/DisplayPort-Ausgang mit Bildschirm.

**Aufbau:** Debian 13 (amd64) mit live-boot, gebaut von GitHub Actions zu jedem Release (`player/pc/bauen.sh`, SBOM
daneben). Eine Datei ist ISO und USB-Image zugleich: ISO9660 mit dem System und dem Platzhalter `signagecast.json`,
Partition 2 die EFI-Systempartition, Partition 3 eine kleine FAT-Partition `SCDATEN` für die Daten des Players. Kein
Desktop, kein SSH, keine Anmeldung an der Konsole.

## Browser-Gerät – nur ein Link (seit 0.36)

Für Geräte, die schon einen Browser haben – Smart-TV, Fire-TV-Stick, ein PC mit fertiger Kiosk-Live-CD (z. B. Porteus
Kiosk) oder einfach ein Browser im Vollbild. *Player hinzufügen* → Modell **Browser-Gerät** → *Link erstellen*. Die
Verwaltung zeigt einen geheimen Link `http://<Server>:8890/anzeige/<Schlüssel>`, der genau diesen Fernseher zeigt –
als Startseite eintragen.

- „Online“ heißt: Die Seite holt ihre Daten (alle 15 s). Nach 5 Minuten ohne kommt eine Benachrichtigung (wie beim Pi).
- Kein Image, kein Bildschirmfoto, kein Rückfall auf den Stream, keine Fernwartung.
- Der Link öffnet nur die Seite dieses Fernsehers, nie die Verwaltung. Wie ein Passwort behandeln; Port 8890 ist
  unverschlüsseltes HTTP – nur im eigenen Netz. *Neuen Link erzeugen* macht den alten sofort ungültig, *Entfernen* ebenso.

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
