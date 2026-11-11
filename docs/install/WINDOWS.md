# SignageCast on a Windows PC

[← installation](../INSTALL.md) · [README](../../README.md) · *Deutsch weiter unten*

Two ways: **Docker Desktop** (recommended – one command) or **WSL** with Debian (more steps, Windows 11).

> **Experimental, not yet tested on real Windows hardware.** If something looks different on your PC, please tell us
> in an [issue](https://github.com/thefrozn/signagecast/issues).

## Before you start

- **Windows 10 22H2 or Windows 11**, 64-bit, on an **Intel or AMD** CPU – Windows on ARM does not work.
- **No graphics acceleration:** Windows does not pass Intel Quick Sync into Linux containers, so the CPU encodes
  H.264 in **Full HD** (about one CPU core per watching TV). For 4K use a Linux server or NAS with Intel graphics.
- **The PC has to run** while the TVs show something: switch off sleep mode (Settings → System → Power).
- About 1 GB RAM per TV and 10 GB disk space.

## Docker Desktop (recommended)

1. Install **Docker Desktop** (once): open PowerShell and run
   `winget install -e --id Docker.DockerDesktop` – or download it from docker.com. Sign out and in again, start
   Docker Desktop once and accept its terms. It uses WSL 2 by itself.
2. In **PowerShell** (no administrator needed):

   ```powershell
   irm https://raw.githubusercontent.com/thefrozn/signagecast/main/windows/schnellstart.ps1 | iex
   ```

   The script checks Docker Desktop, finds this PC's IP in your home network, creates `%USERPROFILE%\SignageCast`
   ([`compose.yaml`](../../windows/compose.yaml) + `.env`), pulls the image, starts the container and opens the admin.
   It prints the **initial password**, the admin address and the TV address.
3. If the **Windows firewall** asks: allow access on **private networks**.
4. Docker Desktop → **Settings → General → “Start Docker Desktop when you sign in”** – so SignageCast is back after a
   restart (the container itself restarts by itself).

- **Admin:** <http://localhost:19090> on the PC, `http://<PC-IP>:19090` in the home network. Change the initial
  password under **System → Access**.
- **TV:** `http://<PC-IP>:8888/tv` · **Raspberry Pi / PC players:** port 8890 is open, images from the admin work as usual.
- **Update:** run the same command again – settings and data stay in the Docker volume `signagecast`.
- **Other IP** (several network cards, VPN): `$env:SC_HOST_IP = "10.0.0.20"` before the command.
- Docker Desktop hides the address of the device asking (all requests seem to come from one address). Port 8890
  allows 20 requests per minute and address for webhook and panel login – with Docker Desktop that is shared by all
  devices. Players and logged-in panels are not affected.

## WSL with Debian (alternative)

For people who prefer Linux without Docker. Needs **Windows 11 22H2 or later** (mirrored networking, so TVs and Pis
reach SignageCast under the PC's IP). WSL is made for development – Windows may stop it when idle, step 5 keeps it running.

1. **PowerShell as administrator:** `wsl --install -d Debian` – restart if asked, then choose a Linux user name and password.
2. File `%USERPROFILE%\.wslconfig` (create it with Notepad):

   ```ini
   [wsl2]
   networkingMode=mirrored
   vmIdleTimeout=-1
   ```

3. **In Debian** (Start menu → Debian): switch on systemd and check the version – SignageCast needs Debian 13:

   ```bash
   printf '[boot]\nsystemd=true\n' | sudo tee /etc/wsl.conf
   cat /etc/debian_version      # 13.x – with 12.x first upgrade Debian (see debian.org “Upgrading to trixie”)
   ```

   Then in PowerShell: `wsl --shutdown` and open Debian again.
4. **Install SignageCast in Debian:**

   ```bash
   sudo apt-get update && sudo apt-get install -y curl
   curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sudo sh
   ```

   At the end it shows the address and a **random password** for the user `tvadmin` (shown only once).
5. **PowerShell as administrator** – let the home network in (only SignageCast's ports) and keep WSL running after sign-in:

   ```powershell
   New-NetFirewallHyperVRule -Name SignageCast -DisplayName SignageCast -Direction Inbound `
     -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 9090,8888,8890
   $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-WindowStyle Hidden -Command wsl.exe -d Debian --exec sleep infinity'
   Register-ScheduledTask -TaskName 'SignageCast WSL' -Action $a -Trigger (New-ScheduledTaskTrigger -AtLogOn) `
     -Settings (New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero))
   ```

- **Admin:** `https://<PC-IP>:9090` (Cockpit, user `tvadmin`) · **TV:** `http://<PC-IP>:8888/tv`
- **Update:** the same `install.sh` line again in Debian.
- The GUID is Microsoft's fixed ID for WSL in the Hyper-V firewall ([WSL networking](https://learn.microsoft.com/windows/wsl/networking)).

---

## Deutsch

Zwei Wege: **Docker Desktop** (empfohlen, ein Befehl) oder **WSL** mit Debian (mehr Schritte, Windows 11).

> **Experimentell, noch nicht auf echter Windows-Hardware getestet.** Sieht etwas anders aus, bitte ein
> [Issue](https://github.com/thefrozn/signagecast/issues) schreiben.

**Voraussetzungen:** Windows 10 22H2 oder 11, 64 Bit, Intel- oder AMD-Prozessor (kein Windows auf ARM). Ohne
Grafikbeschleunigung – Windows reicht Quick Sync nicht an Linux-Container durch, die CPU kodiert H.264 in **Full HD**
(etwa ein Kern je Fernseher, der gerade zuschaut). Der PC muss laufen, solange die Fernseher etwas zeigen
(Energiesparmodus aus). Etwa 1 GB RAM je Fernseher, 10 GB Platz.

### Docker Desktop (empfohlen)

1. **Docker Desktop** installieren (einmal): `winget install -e --id Docker.DockerDesktop` oder von docker.com, neu
   anmelden, Docker Desktop einmal starten und die Bedingungen bestätigen.
2. In **PowerShell** (ohne Administrator):

   ```powershell
   irm https://raw.githubusercontent.com/thefrozn/signagecast/main/windows/schnellstart.ps1 | iex
   ```

   Das Skript prüft Docker Desktop, ermittelt die IP des PCs im Heimnetz, legt `%USERPROFILE%\SignageCast` an, lädt
   das Image, startet den Container, öffnet die Verwaltung und zeigt **Startpasswort**, Verwaltungs- und Fernseher-Adresse.
3. Fragt die **Windows-Firewall**: Zugriff in **privaten Netzwerken** erlauben.
4. Docker Desktop → **Settings → General → „Start Docker Desktop when you sign in“** einschalten.

- **Verwaltung:** <http://localhost:19090> am PC, `http://<PC-IP>:19090` im Heimnetz; Startpasswort unter **System → Zugang** ändern.
- **Fernseher:** `http://<PC-IP>:8888/tv` · **Raspberry-Pi-/PC-Player:** Port 8890 ist offen.
- **Update:** denselben Befehl noch einmal – Einstellungen und Daten bleiben im Docker-Volume `signagecast`.
- **Andere IP** (mehrere Netzwerkkarten, VPN): vorher `$env:SC_HOST_IP = "10.0.0.20"` setzen.
- Docker Desktop verbirgt die Adresse des anfragenden Geräts (alle Anfragen kommen scheinbar von einer Adresse).
  Port 8890 erlaubt für Webhook und Pult-Anmeldung 20 Anfragen je Minute und Adresse – unter Docker Desktop teilen
  sich das alle Geräte. Player und angemeldete Pulte betrifft das nicht.

### WSL mit Debian (Alternative)

Ab **Windows 11 22H2** (Netzwerkmodus „mirrored“, damit Fernseher und Pis SignageCast unter der IP des PCs erreichen).
WSL ist für Entwicklung gedacht – Windows kann es im Leerlauf beenden, Schritt 5 hält es am Laufen.

1. **PowerShell als Administrator:** `wsl --install -d Debian`, bei Bedarf neu starten, Linux-Benutzer anlegen.
2. Datei `%USERPROFILE%\.wslconfig` (mit dem Editor anlegen) – Inhalt wie oben (`networkingMode=mirrored`, `vmIdleTimeout=-1`).
3. **In Debian:** systemd einschalten und Version prüfen (Debian 13 nötig) – Befehle wie oben, danach in PowerShell
   `wsl --shutdown` und Debian neu öffnen.
4. **SignageCast in Debian installieren:** `sudo apt-get install -y curl`, dann
   `curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sudo sh` – am Ende stehen
   Adresse und ein **zufälliges Passwort** für `tvadmin` (nur einmal sichtbar).
5. **PowerShell als Administrator:** Firewall-Regel nur für die Ports von SignageCast und Aufgabe, die WSL nach der
   Anmeldung am Laufen hält – Befehle wie oben.

- **Verwaltung:** `https://<PC-IP>:9090` (Cockpit, Benutzer `tvadmin`) · **Fernseher:** `http://<PC-IP>:8888/tv`
- **Update:** dieselbe `install.sh`-Zeile in Debian noch einmal.
