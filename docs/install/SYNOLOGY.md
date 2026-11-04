# SignageCast on a Synology NAS (Container Manager)

[← installation](../INSTALL.md) · [README](../../README.md) · *Deutsch weiter unten*

Installation by mouse in **Container Manager** – no command line needed.

> **Not tested on real Synology hardware yet.** The steps follow Container Manager on DSM 7.2. If something looks
> different on your NAS, please tell us in an [issue](https://github.com/thefrozn/signagecast/issues) – a short note
> “works on model X with DSM Y” helps too.

## Before you start

- **CPU:** the NAS needs an **Intel or AMD** processor (x86) – in practice the **“+” models** (e.g. DS224+, DS423+,
  DS720+, DS920+, DS923+). ARM models (most “j” and many value models) do **not** work – the SignageCast image is built
  for x86 only. Synology's model list (“Which CPU does my NAS have?”) tells you the CPU.
- **Graphics:** for smooth 4K a CPU with **Intel graphics** – e.g. the Celeron J4125 in DS224+, DS423+, DS720+, DS920+.
  The AMD Ryzen models (e.g. DS923+, DS1522+) have **no** graphics unit: SignageCast then runs a software fallback in
  Full HD, which needs about one CPU core per watching TV.
- **DSM 7.2 or later** with **Container Manager** (older DSM: the “Docker” package – the steps are similar).
- **Memory:** about 1 GB RAM per TV, 10 GB disk space.
- The NAS's **IP address** (Control Panel → Network → Network Interface), e.g. `192.168.1.20`.

## Step by step

1. **Install Container Manager:** open the **Package Center**, search for *Container Manager* and click **Install**.
   It creates the shared folder `docker`.
2. **Create a folder for SignageCast:** in **File Station** open the shared folder `docker` and create the folder
   `signagecast` in it.
3. **Open Container Manager** and go to **Project** → **Create**.
4. **Project name:** `signagecast`. **Path:** choose the folder `docker/signagecast` from step 2.
   **Source:** **Create docker-compose.yml**.
5. Copy the following text into the field and change the two marked lines – `TZ` to your time zone and `SC_HOST_IP`
   to the IP address of the NAS:

   ```yaml
   services:
     signagecast:
       image: ghcr.io/thefrozn/signagecast:latest
       container_name: signagecast
       restart: unless-stopped
       devices:
         - /dev/dri:/dev/dri          # Intel graphics – delete these two lines if the NAS has none
       ports:
         - "8888:8888"                # stream for the TVs
         - "19090:19090"              # admin
       volumes:
         - ./data:/data               # settings and data in docker/signagecast/data
       environment:
         TZ: Europe/Berlin            # ← your time zone
         SC_HOST_IP: "192.168.1.20"   # ← IP address of the NAS
   ```

6. Click **Next**. If a page for **Web Station / web portal** appears, leave it switched off and click **Next** again.
   Then **Done**. Container Manager downloads the image (about 1 GB, takes a few minutes) and starts it.
7. **Find the initial password:** go to **Container**, click **signagecast** → **Details** → **Log**. Look for the line starting with
   `SignageCast – Startpasswort der Verwaltung / initial admin password:` – the word after the colon is the password.
8. **Open the admin** in your browser: `http://<NAS-IP>:19090` and log in with this password. Change it right away
   under **System → Access**. A short assistant asks for language, location and (optionally) Home Assistant.
9. **On the TV** open `http://<NAS-IP>:8888/tv` in the browser and set it as start page.

**Firewall:** if the DSM firewall is on (Control Panel → Security → Firewall), allow the ports **8888** and **19090**
for your home network.

## Update

SignageCast does not update itself inside a container. To get a new version:

1. **Project** → `signagecast` → **Action** → **Stop**.
2. **Image** → `ghcr.io/thefrozn/signagecast` – if it shows **Update available**, click it. Otherwise: **Project** →
   `signagecast` → **Action** → **Build** (downloads the newest image and starts again).
3. Settings, pictures and backups are in the folder `docker/signagecast/data` and are kept. **Do not delete it.**

The admin shows a note when a new version is out (**System → Updates**). Tip: Hyper Backup of the folder
`docker/signagecast` also saves SignageCast; additionally the admin can make its own backups (**System → Backup**).

## If something does not work

| Problem | Solution |
|---|---|
| Build fails with an error about `/dev/dri` | The NAS has no usable graphics: delete the two lines `devices:` and `- /dev/dri:/dev/dri` and build again (software fallback). |
| “port is already allocated” | Another app uses 8888 or 19090: change the **left** number, e.g. `"8899:8888"` – the TV address is then `http://<NAS-IP>:8899/tv`. |
| Image cannot be downloaded / “exec format error” | ARM NAS – not supported. |
| Admin or TV page cannot be reached | DSM firewall: allow 8888 and 19090 (see above). |
| Clock shows the wrong time | Check `TZ` (list: “TZ identifier” in [this table](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)). |
| Picture stutters | Without Intel graphics the CPU encodes (Full HD) – the NAS may be too weak; check **System → Performance** and run fewer TVs at once. |
| Home Assistant guide shows a wrong IP | `SC_HOST_IP` must be the IP of the NAS. |

Webhook messages (optional) additionally need the line `- "8890:8890"` under `ports:`.

---

# Deutsch: SignageCast auf einem Synology-NAS (Container Manager)

Installation per Maus im **Container Manager** – ohne Kommandozeile.

> **Noch nicht auf echter Synology-Hardware getestet.** Die Schritte folgen dem Container Manager unter DSM 7.2. Sieht
> bei dir etwas anders aus, schreib es bitte in ein [Issue](https://github.com/thefrozn/signagecast/issues) – auch ein
> kurzes „läuft auf Modell X mit DSM Y“ hilft.

## Vorher prüfen

- **Prozessor:** Das NAS braucht einen **Intel- oder AMD**-Prozessor (x86) – praktisch die **„+“-Modelle** (z. B.
  DS224+, DS423+, DS720+, DS920+, DS923+). ARM-Modelle (die meisten „j“- und viele Einsteiger-Modelle) gehen **nicht** –
  das SignageCast-Image gibt es nur für x86. Welchen Prozessor dein NAS hat, steht in Synologys Modell-Liste.
- **Grafik:** Für flüssiges 4K eine CPU mit **Intel-Grafik** – z. B. der Celeron J4125 in DS224+, DS423+, DS720+,
  DS920+. Die AMD-Ryzen-Modelle (z. B. DS923+, DS1522+) haben **keine** Grafikeinheit: Dann läuft ein Notbetrieb in
  Full HD per CPU – etwa ein Kern je Fernseher, der gerade zuschaut.
- **DSM 7.2 oder neuer** mit **Container Manager** (älteres DSM: Paket „Docker“ – die Schritte sind ähnlich).
- **Speicher:** etwa 1 GB RAM je Fernseher, 10 GB Plattenplatz.
- Die **IP-Adresse** des NAS (Systemsteuerung → Netzwerk → Netzwerkschnittstelle), z. B. `192.168.1.20`.

## Schritt für Schritt

1. **Container Manager installieren:** **Paket-Zentrum** öffnen, *Container Manager* suchen, **Installieren**. Dabei
   entsteht der freigegebene Ordner `docker`.
2. **Ordner anlegen:** in der **File Station** den Ordner `docker` öffnen und darin den Ordner `signagecast` anlegen.
3. **Container Manager öffnen** → **Projekt** → **Erstellen**.
4. **Projektname:** `signagecast`. **Pfad:** den Ordner `docker/signagecast` aus Schritt 2 wählen.
   **Quelle:** **docker-compose.yml erstellen**.
5. Den Text aus Schritt 5 des englischen Teils oben in das Feld kopieren und die zwei markierten Zeilen ändern –
   `TZ` auf deine Zeitzone (`Europe/Berlin` passt für Deutschland), `SC_HOST_IP` auf die IP-Adresse des NAS. Hat das
   NAS keine Intel-Grafik, die zwei Zeilen `devices:` und `- /dev/dri:/dev/dri` löschen.
6. **Weiter**. Erscheint eine Seite zu **Web Station / Webportal**, ausgeschaltet lassen und wieder **Weiter**, dann
   **Fertig**. Der Container Manager lädt das Image (etwa 1 GB, einige Minuten) und startet es.
7. **Startpasswort finden:** unter **Container** auf **signagecast** klicken → **Details** → **Protokoll**. Dort steht eine
   Zeile `SignageCast – Startpasswort der Verwaltung / initial admin password: …` – das Wort nach dem Doppelpunkt ist das Passwort.
8. **Verwaltung öffnen:** im Browser `http://<NAS-IP>:19090`, mit diesem Passwort anmelden und es gleich unter
   **System → Zugang** ändern. Ein kurzer Assistent fragt nach Sprache, Ort und (optional) Home Assistant.
9. **Am Fernseher** im Browser `http://<NAS-IP>:8888/tv` öffnen und als Startseite festlegen.

**Firewall:** Ist die DSM-Firewall an (Systemsteuerung → Sicherheit → Firewall), die Ports **8888** und **19090** für
das Heimnetz freigeben.

## Update

Im Container aktualisiert sich SignageCast nicht selbst. Für eine neue Version:

1. **Projekt** → `signagecast` → **Aktion** → **Stoppen**.
2. **Image** → `ghcr.io/thefrozn/signagecast` – steht dort **Update verfügbar**, darauf klicken. Sonst: **Projekt** →
   `signagecast` → **Aktion** → **Erstellen** (Build; lädt das neueste Image und startet neu).
3. Einstellungen, Bilder und Sicherungen liegen im Ordner `docker/signagecast/data` und bleiben erhalten. **Nicht löschen.**

Die Verwaltung zeigt einen Hinweis, wenn es eine neue Version gibt (**System → Updates**). Tipp: Hyper Backup des
Ordners `docker/signagecast` sichert SignageCast mit; zusätzlich macht die Verwaltung eigene Sicherungen
(**System → Sicherung**).

## Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| Erstellen scheitert mit Fehler zu `/dev/dri` | Keine nutzbare Grafik: die Zeilen `devices:` und `- /dev/dri:/dev/dri` löschen, neu erstellen (Notbetrieb). |
| „port is already allocated“ | Eine andere App nutzt 8888 oder 19090: die **linke** Zahl ändern, z. B. `"8899:8888"` – der Fernseher öffnet dann `http://<NAS-IP>:8899/tv`. |
| Image lädt nicht / „exec format error“ | ARM-NAS – wird nicht unterstützt. |
| Verwaltung oder TV-Seite nicht erreichbar | DSM-Firewall: 8888 und 19090 freigeben (siehe oben). |
| Uhr geht falsch | `TZ` prüfen (für Deutschland `Europe/Berlin`). |
| Bild ruckelt | Ohne Intel-Grafik rechnet die CPU (Full HD) – das NAS ist evtl. zu schwach; **System → Leistungstest** prüfen, weniger Fernseher gleichzeitig. |
| Home-Assistant-Anleitung zeigt falsche IP | `SC_HOST_IP` muss die IP des NAS sein. |

Meldungen per Webhook (optional) brauchen zusätzlich die Zeile `- "8890:8890"` unter `ports:`.
