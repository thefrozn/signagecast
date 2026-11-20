# SignageCast – UI-Regel für die Verwaltung

[English](UI-RULES.md) · [Glossar](GLOSSARY.md) · [Mitmachen](../CONTRIBUTING.md) · [← README](../README.de.md)

Diese Regel gilt für jede neue Funktion in der Verwaltung (Cockpit-Seite `cockpit/signagecast/`). Wer etwas hinzufügt,
beantwortet vorher den Entscheidungsbaum in Punkt 5 und nennt die Antwort im Pull Request.

## 0. Vorbilder

Die Regel ist nicht neu erfunden, sie übernimmt bewährte Muster:

- **Shopify Polaris** – die Navigation besteht aus Dingen, die man verwaltet (Bestellungen, Produkte, Kunden), nicht
  aus Tätigkeiten. Dadurch findet man jede Funktion dort, wo das Ding steht, um das es geht.
- **Microsoft Azure Portal** – jede Ressource hat dasselbe Gerüst aus Liste, Übersicht, fachlichen Reitern und
  Protokoll. Wer ein Ding bedienen kann, kann deshalb alle bedienen.
- **Home Assistant** – die Einstellungen sind eine Kachelseite mit Symbol, einem Satz und Status. Auch ohne
  Fachwissen sieht man so auf einen Blick, was eingerichtet ist und was fehlt.
- **Apple Human Interface Guidelines** – die Tiefe kommt schrittweise (progressive disclosure): Zuerst steht das
  Häufige da, Seltenes erst auf Wunsch. Die Oberfläche bleibt dadurch ruhig, ohne dass etwas fehlt.

## 1. Das Menü besteht aus Dingen (Shopify-Prinzip)

- Hauptmenüpunkte sind Hauptwörter im Plural: Dinge, die man anlegt, ansieht und verwaltet (z. B. Kanäle, Geräte,
  Layouts, Medien, Datenquellen). Nie Tätigkeiten, nie Technikbegriffe.
- Höchstens 7 Hauptpunkte, höchstens 2 Ebenen.
- Oben steht die Übersicht (Startseite), unten getrennt die Einstellungen.
- Aktionen wie Durchsage und Notfall sind feste Schaltflächen in der Kopfzeile, keine Menüpunkte.

## 2. Jedes Ding hat dasselbe Gerüst (Azure-Prinzip, schlank)

- **Liste:** Tabelle mit Name, Status in Klartext, Verwendung und letzter Änderung. „+ Neu“ steht oben rechts,
  Filter und Suche über der Tabelle.
- **Detail:** Reiter in fester Reihenfolge:
  1. **Übersicht** – Status, wichtigste Werte, Schnellaktionen
  2. **1 bis 4 fachliche Reiter**
  3. **Verlauf** – Protokoll dieses Dings, falls vorhanden
- **Löschen** steht immer unten in der Detailseite, mit dem Hinweis, wo das Ding noch verwendet wird.
- **Unterobjekte** (z. B. Themen eines Live-Videos) erscheinen als Reiter oder Liste im Elternobjekt, nicht im
  Hauptmenü.

## 3. Einstellungen wie in Home Assistant

- Die Einstellungen sind eine Kachelseite. Jede Kachel hat ein Symbol, einen Namen, einen Satz Beschreibung und einen
  Status (z. B. „verbunden“, „3 Konten“).
- Hierher gehört nur, was einmal global eingestellt wird: Allgemein, Home Assistant, Benachrichtigungen,
  Konten & Zugang, KI-Assistenten, Speicherorte, Durchsage-Pult und System (Zustand, Updates, Sicherung, Protokoll).
- Konten, Passwörter und Zugänge liegen an genau einer Stelle: **Konten & Zugang**.

## 4. Ruhe durch schrittweise Tiefe (Apple-Prinzip)

- Jede Seite zeigt oben das Häufige. Seltenes liegt unter einem einklappbaren „Erweitert“. Technische Felder
  (Kennung, Header, Ports) stehen immer dort.
- Zum Anlegen gibt es Assistenten mit wenigen Schritten, Erweitertes kommt zum Schluss.
- Hilfe gibt es als ⓘ mit einem Satz, keine Textwände.

## 5. Entscheidungsbaum für jede neue Funktion

Vor dem Bauen beantworten und im Pull Request nennen:

1. Legt man davon mehrere an und verwaltet sie? → **neues Ding.**
   Ist es Teil eines anderen Dings? → **Unterobjekt dort.**
   Nur wenn es eigenständig ist und häufig genutzt wird → **Hauptmenü.**
2. Ist es eine Eigenschaft oder ein Verhalten eines vorhandenen Dings? → **Abschnitt oder Reiter auf dessen
   Detailseite.**
3. Wird es einmal global eingestellt? → **Einstellungs-Kachel** (eine vorhandene erweitern, bevor eine neue entsteht).
4. Ist es eine einmalige Handlung? → **Schaltfläche am Ding oder in der Kopfzeile**, nie ein Menüpunkt.
5. Betrifft es Betrieb und Wartung? → **Einstellungen › System.**

Passt nichts davon: die Regel nicht biegen, sondern den Maintainer fragen (Issue oder Discussion).

## 6. Sprache

- Ein Begriff pro Sache, überall gleich. Maßgeblich ist das [Glossar](GLOSSARY.md) (Deutsch und Englisch).
- Status steht immer in Klartext („läuft“, „keine Verbindung seit 10 min“), nie nur als Farbe oder Code.
- Alte Adressen werden bei jeder Umstellung weitergeleitet (in `tv.js` die Tabelle `ALT`).

## 7. Doku

- UI-RULES ist Teil der offiziellen Doku und wird aus dem README (Abschnitt „Mitmachen“) und aus
  [CONTRIBUTING.md](../CONTRIBUTING.md) verlinkt.
- [MANUAL.md](MANUAL.md) erklärt vorne im Abschnitt „So ist die Verwaltung aufgebaut“ für Nutzer, ohne
  Entwicklerbegriffe: Dinge im Menü, Einstellungen als Kacheln, Aktionen in der Kopfzeile, Erweitert eingeklappt.
- Die Pull-Request-Vorlage hat das Pflichtfeld „Wo liegt die Funktion laut UI-RULES (Punkt 5)?“.
- Bei jeder Änderung am Menü werden UI-RULES, MANUAL und GLOSSARY im selben Commit nachgezogen.

## 8. Festgelegte Auslegung

Fälle, in denen die Regel nicht eindeutig war, und wie sie entschieden sind (seit 0.65):

1. **7 Hauptpunkte** zählen ohne Übersicht und Einstellungen; beide stehen getrennt am Anfang bzw. Ende.
2. **Konten & Zugang** enthält alles, womit man sich *bei SignageCast* anmeldet: Verwaltung, Durchsage-Pult,
   KI-Assistenten, Webhook. Zugangsdaten *zu fremden Diensten* (Home-Assistant-Token, Telegram, E-Mail, SMB/WebDAV,
   YouTube-API, Tailscale/Headscale) bleiben bei ihrer Verbindung; Konten & Zugang verlinkt sie.
3. **Automatik der Live-Videos** ist global und deshalb die Kachel „Live-Videos“; die Sammlung verlinkt sie.
4. **Themen** sind ein Unterobjekt der Sammlung (Live-Videos › Themen), je Kanal nur ausgewählt.
5. **Einspieler** gehören zu den Medien (eigene, geladene Videos mit Zeitplan).
6. **Fernstandorte** und **Live-Videos** sind zusätzliche Kacheln, weil keine vorhandene passt.
7. Der **Layout-Designer** ist ein Vollbild-Werkzeug; er gilt als fachlicher Reiter des Layouts.
8. **Verlauf je Ding** erscheint nur, wo das Protokoll den Eintrag einem Ding zuordnen kann.
9. **„Videostream ohne Zuschauer“** gehört zum Betrieb: Einstellungen › System › Zustand.
10. Ein **Detailfeld rechts** (Datenquellen, Live-Videos) ist erlaubt, wenn es dieselbe Reihenfolge hat; volle
    Detailseiten mit Reitern dort, wo mehrere Reiter nötig sind.
11. **Dinge mit Bild** (Layouts) behalten Kacheln mit Vorschau statt einer Tabelle; jede Kachel zeigt dieselben Angaben
    wie eine Tabellenzeile (Name, Status, Verwendung, letzte Änderung), darüber Suche und „+ Neu“ oben rechts.
12. **Kleine Dinge ohne eigene Detailseite:** einzelne Bilder und Videos unter Medien sowie einzelne Radiosender bleiben
    Listeneinträge mit Name, Verwendung und Löschen samt Hinweis, wo sie verwendet werden.
