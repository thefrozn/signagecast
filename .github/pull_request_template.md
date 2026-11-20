## What and why / Was und warum

<!-- One or two sentences. / Ein bis zwei Sätze. -->

## Where does the feature go according to UI-RULES (section 5)? / Wo liegt die Funktion laut UI-RULES (Punkt 5)? (required / Pflicht)

<!--
Answer the decision tree in docs/UI-RULES.md, e.g.
"2 – property of a channel → tab ‘Display & schedule’ on the channel detail page".
If no answer fits, say so – do not bend the rules.
Write "no admin change" if the admin page is not touched.
-->

## Checklist / Prüfliste

- [ ] Tests pass (`python3 -m unittest discover -s tests`)
- [ ] Terms from `docs/GLOSSARY.md`, German and English
- [ ] Menu changed? Then UI-RULES, MANUAL and GLOSSARY updated in the same commit, old addresses redirected (`ALT`)
- [ ] No secrets (passwords, tokens, keys)
- [ ] TV page or render chain changed? Then CPU/RAM/lost frames measured
