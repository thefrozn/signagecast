# SignageCast – UI rules for the admin page

[Deutsch](UI-RULES.de.md) · [Glossary](GLOSSARY.md) · [Contributing](../CONTRIBUTING.md) · [← README](../README.md)

These rules apply to every new feature in the admin page (Cockpit page `cockpit/signagecast/`). Before you add
something, answer the decision tree in section 5 and state the answer in the pull request.

## 0. Where the rules come from

The rules are not invented here; they adopt proven patterns:

- **Shopify Polaris** – navigation is made of the things you manage (orders, products, customers), not of
  activities. So every feature sits where the thing it is about is.
- **Microsoft Azure portal** – every resource has the same frame: list, overview, topic tabs and activity log.
  If you can operate one thing, you can operate them all.
- **Home Assistant** – settings are a page of tiles, each with an icon, one sentence and a state. Even without
  technical knowledge you see at a glance what is set up and what is missing.
- **Apple Human Interface Guidelines** – depth comes step by step (progressive disclosure): the common things
  first, the rare ones on request. The interface stays calm without losing anything.

## 1. The menu is made of things (Shopify principle)

- Main menu items are plural nouns: things you create, look at and manage (e.g. channels, devices, layouts, media,
  data sources). Never activities, never technical terms.
- At most 7 main items, at most 2 levels.
- At the top: Overview (start page). At the bottom, separated: Settings.
- Actions such as announcement and emergency are fixed buttons in the header, not menu items.

## 2. Every thing has the same frame (Azure principle, lean)

- **List:** table with name, state in plain words, where it is used and last change. “+ New” at the top right,
  filter and search above the table.
- **Detail:** tabs in a fixed order:
  1. **Overview** – state, the most important values, quick actions
  2. **1 to 4 topic tabs**
  3. **History** – log of this thing, if there is one
- **Delete** is always at the bottom of the detail page, with a note where the thing is still used.
- **Child objects** (e.g. the topics of live videos) appear as a tab or list inside the parent, not in the main
  menu.

## 3. Settings like in Home Assistant

- Settings are a page of tiles. Each tile has an icon, a name, one sentence of description and a state
  (e.g. “connected”, “3 accounts”).
- Only what is set once, globally, belongs here: General, Home Assistant, Notifications, Accounts & access,
  AI assistants, Storage locations, Announcement panel and System (health, updates, backup, log).
- Accounts, passwords and access live in exactly one place: **Accounts & access**.

## 4. Calm through gradual depth (Apple principle)

- Every page shows the common things at the top. Rare ones go under a collapsible “Advanced”; technical fields
  (ID, header, ports) always go there.
- Creating something uses an assistant with few steps; advanced options come last.
- Help is an ⓘ with one sentence, no walls of text.

## 5. Decision tree for every new feature

Answer before building and state the answer in the pull request:

1. Do you create several of these and manage them? → **new thing.**
   Is it part of another thing? → **child object there.**
   Only if it stands on its own and is used often → **main menu.**
2. Is it a property or behaviour of an existing thing? → **section or tab on that thing’s detail page.**
3. Is it set once, globally? → **settings tile** (extend an existing tile before adding a new one).
4. Is it a one-off action? → **button on the thing or in the header**, never a menu item.
5. Is it about operation and maintenance? → **Settings › System.**

If none of these fits: do not bend the rules, ask the maintainer (issue or discussion).

## 6. Language

- One term per thing, the same everywhere. The [glossary](GLOSSARY.md) (German and English) is binding.
- State is always in plain words (“running”, “no connection for 10 min”), never only a colour or a code.
- Old addresses are redirected after every change (in `tv.js` the table `ALT`).

## 7. Documentation

- UI-RULES is part of the official documentation, linked from the README (section “Contributing”) and from
  [CONTRIBUTING.md](../CONTRIBUTING.md).
- [MANUAL.md](MANUAL.md) starts with the section “How the admin page is organised”, written for users without
  developer terms: things in the menu, settings as tiles, actions in the header, advanced options collapsed.
- The pull request template has the required field “Where does the feature go according to UI-RULES (section 5)?”.
- Every change to the menu updates UI-RULES, MANUAL and GLOSSARY in the same commit.

## 8. Agreed interpretation

Cases where the rules were not clear-cut, and how they are decided (since 0.65):

1. **7 main items** are counted without Overview and Settings; both stand apart at the start and the end.
2. **Accounts & access** holds everything used to log in *to SignageCast*: admin page, announcement panel, AI
   assistants, webhook. Credentials *for other services* (Home Assistant token, Telegram, e-mail, SMB/WebDAV, YouTube
   API, Tailscale/Headscale) stay with their connection; Accounts & access links to them.
3. **Live video automation** is global and therefore the “Live videos” tile; the collection links to it.
4. **Topics** are a child object of the collection (Live videos › Topics), only selected per channel.
5. **Clips** belong to Media (own, downloaded videos with a schedule).
6. **Remote sites** and **Live videos** are additional tiles because no existing tile fits.
7. The **layout designer** is a full-screen tool; it counts as a topic tab of the layout.
8. **History per thing** appears only where the log can assign an entry to that thing.
9. **“Video stream without viewers”** is about operation: Settings › System › Health.
10. A **detail panel on the right** (data sources, live videos) is allowed if it keeps the same order; full detail
    pages with tabs where several tabs are needed.
11. **Things with a picture** (layouts) keep tiles with a preview instead of a table; every tile shows the same as a
    table row (name, state, used by, last change), with search and “+ New” at the top right.
12. **Small things without a detail page:** single files (pictures, videos, PDFs) under Media › Files and single radio
    stations stay list entries with name, where they are used and delete with that note. Since 0.72 *Edit* unfolds a
    file's row (name, tags, validity, video window, add to gallery, delete) instead of opening a page.
13. **Media › Files** (since 0.72) is the media library: one table for all pictures, videos and PDFs; galleries and the
    video window use these files. A global option (*Convert videos*) lives under Settings › System › Health.
