# Contributing to SignageCast

Thank you for helping. Questions and ideas are welcome in
[GitHub Discussions](https://github.com/thefrozn/signagecast/discussions), bugs in
[GitHub issues](https://github.com/thefrozn/signagecast/issues).

## Before you build

- **Three goals rank equally:** stable, secure and light (see [Principles](README.md#principles)). A change must not
  make one of them worse. Changes to the TV page or the render chain are measured before a release
  (CPU, memory, lost frames).
- **Admin page:** every new feature follows the [UI rules](docs/UI-RULES.md) ([Deutsch](docs/UI-RULES.de.md)).
  Answer the decision tree in section 5 and state the result in the pull request.
- **Words:** use the terms from the [glossary](docs/GLOSSARY.md), in German and English.
- **Secrets:** never commit passwords, tokens, API keys or private keys, not even in tests or examples.

## Pull requests

- Small and focused; one topic per pull request.
- Tests: `python3 -m unittest discover -s tests` must pass.
- User-visible changes go into `CHANGELOG.md` and the matching document under `docs/`.
- A change to the menu updates `docs/UI-RULES*.md`, `docs/MANUAL.md` and `docs/GLOSSARY.md` in the same commit.

---

## Deutsch (kurz)

Danke fürs Mitmachen. Fragen und Ideen gehören in die Discussions, Fehler in die Issues.

- Stabil, sicher und sparsam sind gleich wichtig; keine Änderung darf eines davon verschlechtern.
- Jede neue Funktion in der Verwaltung folgt der [UI-Regel](docs/UI-RULES.de.md). Den Entscheidungsbaum (Punkt 5)
  im Pull Request beantworten.
- Begriffe aus dem [Glossar](docs/GLOSSARY.md) verwenden.
- Keine Passwörter, Tokens, API-Keys oder privaten Schlüssel einchecken.
- Tests grün, CHANGELOG und Doku nachziehen. Menü-Änderungen ziehen UI-RULES, MANUAL und GLOSSARY im selben Commit
  mit.
