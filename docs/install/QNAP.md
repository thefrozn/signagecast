# SignageCast on a QNAP NAS (Container Station)

[← installation](../INSTALL.md) · [README](../../README.md) · *Deutsch weiter unten*

Installation by mouse in **Container Station** – no command line needed.

> **Not tested on real QNAP hardware yet.** The steps follow QNAP's documentation for Container Station 3. If something
> looks different on your NAS, please tell us in an [issue](https://github.com/thefrozn/signagecast/issues) – a short
> note “works on model X with QTS Y” helps too.

## Before you start

- **CPU:** the NAS needs an **Intel or AMD** processor (x86). ARM models (many TS-x33, TS-x28, TS-x32 …) do **not**
  work – the SignageCast image is built for x86 only. The model's data sheet tells you the CPU.
- **Graphics:** for smooth 4K a CPU with **Intel graphics** (Quick Sync, e.g. Celeron J4125, N5105, N100). Without it
  SignageCast runs a software fallback in Full HD, which needs about one CPU core per watching TV.
- **QTS 5.1 or later** (or QuTS hero) with **Container Station 3**.
- **Memory:** about 1 GB RAM per TV, 10 GB disk space.
- The NAS's **IP address** (Control Panel → Network & Virtual Switch, or Qfinder Pro), e.g. `192.168.1.20`.

## Step by step

1. **Install Container Station:** open the **App Center**, search for *Container Station* and click **Install**. When
   asked for a folder for containers, keep the suggestion.
2. **Open Container Station** and go to **Applications**.
3. Click **Create** (top right) → **Create Application**.
4. **Application name:** `signagecast`.
5. **YAML:** copy the following text into the field and change the two marked lines – `TZ` to your time zone and
   `SC_HOST_IP` to the IP address of the NAS:

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
         - signagecast:/data
       environment:
         TZ: Europe/Berlin            # ← your time zone
         SC_HOST_IP: "192.168.1.20"   # ← IP address of the NAS
   volumes:
     signagecast:
   ```

6. Click **Validate YAML** (optional, shows typing errors), then **Create**. Container Station downloads the image
   (about 1 GB, takes a few minutes) and starts it.
7. **Find the initial password:** go to **Containers**, click **signagecast** and open its **log**. Look for the line
   `SignageCast – Startpasswort der Verwaltung: …` – the text after the colon is the password.
8. **Open the admin** in your browser: `http://<NAS-IP>:19090` and log in with this password. Change it right away
   under **System → Access**. A short assistant asks for language, location and (optionally) Home Assistant.
9. **On the TV** open `http://<NAS-IP>:8888/tv` in the browser and set it as start page.

## Update

SignageCast does not update itself inside a container. To get a new version:

1. **Applications** → `signagecast` → **⋯ / Edit** → **Recreate** (QNAP's name for “start again with the newest image”),
   keep the YAML and confirm. If your version has no such button: **Containers** → `signagecast` → stop and remove it,
   then create the application again with the same YAML.
2. Settings, pictures and backups are in the volume `signagecast` and are kept. **Do not delete the volume.**

The admin shows a note when a new version is out (**System → Updates**).

## If something does not work

| Problem | Solution |
|---|---|
| “Create” fails with an error about `/dev/dri` | The NAS has no usable graphics: delete the two lines `devices:` and `- /dev/dri:/dev/dri` and create again (software fallback). |
| “port is already allocated” | Another app uses 8888 or 19090: change the **left** number, e.g. `"8899:8888"` – the TV address is then `http://<NAS-IP>:8899/tv`. |
| Image cannot be downloaded / “exec format error” | ARM NAS – not supported. |
| Clock shows the wrong time | Check `TZ` (list: “TZ identifier” in [this table](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)). |
| Picture stutters | Without Intel graphics the CPU encodes (Full HD) – the NAS may be too weak; check **System → Performance** and run fewer TVs at once. |
| Home Assistant guide shows a wrong IP | `SC_HOST_IP` must be the IP of the NAS. |

Webhook messages (optional) additionally need the line `- "8890:8890"` under `ports:`.

---

# Deutsch: SignageCast auf einem QNAP-NAS (Container Station)

Installation per Maus in der **Container Station** – ohne Kommandozeile.

> **Noch nicht auf echter QNAP-Hardware getestet.** Die Schritte folgen QNAPs Dokumentation zu Container Station 3.
> Sieht bei dir etwas anders aus, schreib es bitte in ein [Issue](https://github.com/thefrozn/signagecast/issues) – auch
> ein kurzes „läuft auf Modell X mit QTS Y“ hilft.

## Vorher prüfen

- **Prozessor:** Das NAS braucht einen **Intel- oder AMD**-Prozessor (x86). ARM-Modelle (viele TS-x33, TS-x28,
  TS-x32 …) gehen **nicht** – das SignageCast-Image gibt es nur für x86. Den Prozessor nennt das Datenblatt des Modells.
- **Grafik:** Für flüssiges 4K eine CPU mit **Intel-Grafik** (Quick Sync, z. B. Celeron J4125, N5105, N100). Ohne läuft
  ein Notbetrieb in Full HD per CPU – etwa ein Kern je Fernseher, der gerade zuschaut.
- **QTS 5.1 oder neuer** (oder QuTS hero) mit **Container Station 3**.
- **Speicher:** etwa 1 GB RAM je Fernseher, 10 GB Plattenplatz.
- Die **IP-Adresse** des NAS (Systemsteuerung → Netzwerk & virtueller Switch oder Qfinder Pro), z. B. `192.168.1.20`.

## Schritt für Schritt

1. **Container Station installieren:** **App Center** öffnen, *Container Station* suchen, **Installieren**. Fragt sie
   nach einem Ordner für Container, den Vorschlag lassen.
2. **Container Station öffnen** und zu **Anwendungen** (Applications) wechseln.
3. Oben rechts **Erstellen** → **Anwendung erstellen** (Create Application).
4. **Anwendungsname:** `signagecast`.
5. **YAML:** den Text oben aus Schritt 5 des englischen Teils in das Feld kopieren und die zwei markierten Zeilen
   ändern – `TZ` auf deine Zeitzone (`Europe/Berlin` passt für Deutschland), `SC_HOST_IP` auf die IP-Adresse des NAS.
   Hat das NAS keine Intel-Grafik, die zwei Zeilen `devices:` und `- /dev/dri:/dev/dri` löschen.
6. **YAML prüfen** (optional, zeigt Tippfehler), dann **Erstellen**. Die Container Station lädt das Image (etwa 1 GB,
   einige Minuten) und startet es.
7. **Startpasswort finden:** unter **Container** auf **signagecast** klicken und das **Protokoll** (Log) öffnen. Dort
   steht `SignageCast – Startpasswort der Verwaltung: …` – der Text nach dem Doppelpunkt ist das Passwort.
8. **Verwaltung öffnen:** im Browser `http://<NAS-IP>:19090`, mit diesem Passwort anmelden und es gleich unter
   **System → Zugang** ändern. Ein kurzer Assistent fragt nach Sprache, Ort und (optional) Home Assistant.
9. **Am Fernseher** im Browser `http://<NAS-IP>:8888/tv` öffnen und als Startseite festlegen.

## Update

Im Container aktualisiert sich SignageCast nicht selbst. Für eine neue Version:

1. **Anwendungen** → `signagecast` → **⋯ / Bearbeiten** → **Neu erstellen** (Recreate), YAML lassen und bestätigen.
   Gibt es den Knopf in deiner Version nicht: unter **Container** `signagecast` stoppen und entfernen, dann die
   Anwendung mit derselben YAML neu erstellen.
2. Einstellungen, Bilder und Sicherungen liegen im Volume `signagecast` und bleiben erhalten. **Das Volume nicht löschen.**

Die Verwaltung zeigt einen Hinweis, wenn es eine neue Version gibt (**System → Updates**).

## Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| „Erstellen“ scheitert mit Fehler zu `/dev/dri` | Keine nutzbare Grafik: die Zeilen `devices:` und `- /dev/dri:/dev/dri` löschen, neu erstellen (Notbetrieb). |
| „port is already allocated“ | Eine andere App nutzt 8888 oder 19090: die **linke** Zahl ändern, z. B. `"8899:8888"` – der Fernseher öffnet dann `http://<NAS-IP>:8899/tv`. |
| Image lädt nicht / „exec format error“ | ARM-NAS – wird nicht unterstützt. |
| Uhr geht falsch | `TZ` prüfen (für Deutschland `Europe/Berlin`). |
| Bild ruckelt | Ohne Intel-Grafik rechnet die CPU (Full HD) – das NAS ist evtl. zu schwach; **System → Leistungstest** prüfen, weniger Fernseher gleichzeitig. |
| Home-Assistant-Anleitung zeigt falsche IP | `SC_HOST_IP` muss die IP des NAS sein. |

Meldungen per Webhook (optional) brauchen zusätzlich die Zeile `- "8890:8890"` unter `ports:`.
