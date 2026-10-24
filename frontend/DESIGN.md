# FirstReply design: "it looks like your phone"

The moment this app is about happens on a phone, late at night, in a text thread. So the design
language is the product's own material, the text conversation. FirstReply should feel like a real
messaging app plus a teacher's honest notes, not a startup landing page.

Every page is built from this file. Tokens live in `src/index.css` (`:root` = light, `.dark` = dark)
and `tailwind.config.js`.

## Color: four roles, no others

| Role | Light | Dark | Used for |
|---|---|---|---|
| System neutrals | `#FFFFFF` cells, `#F2F2F7` page, `#E5E5EA` fills, text `#000`, secondary `#636368`, hairline `#C6C6C8` | `#000` page, `#1C1C1E` cells, `#2C2C2E` fills, text `#FFF`, secondary `#A0A0A7`, hairline `#38383A` | Everything by default |
| Action (one) | `#0071EB` fill, `#0062CC` text | `#0A6EF0` fill, `#4DA3FF` text | Primary buttons, links, focus ring, sent bubbles, the current level |
| Annotation | helped `#1B7532`, hurt `#D70015` | helped `#30D158`, hurt `#FF6961` | Green/red underlines, trust changes, detected skills |
| Help | `#C41230` | `#FF6961` (dark text) | Only "I need help now", 988 and the crisis card |

The iOS blues and green are nudged just enough to pass WCAG AA with real text (exact `#007AFF` with
white text is 4.0:1, `#248A3D` on white is 4.4:1). No violet, ember, cream paper, grain, gradients,
glows or colored shadows anywhere.

## Type

- The device's own UI font for everything (`-apple-system, "SF Pro Text", "Segoe UI", Roboto,
  system-ui`). No web fonts: nothing to download, and it's the vernacular of a messaging app.
- Hierarchy from size and weight only: bold, large, tight headlines like iOS large titles.
- Sentence case everywhere. No eyebrow labels, no uppercase tracking, no italics for emphasis, no
  gradient text.
- Monospace only for real numbers inside X-ray (a debug view).

## Layout and components

- Inset grouped sections like a settings list: 10–12 px radius, hairline borders and separators,
  no shadows, no glass.
- Landing: a plain headline beside the real conversation and one primary button. "How it works" is
  an annotated conversation (real bubbles, each with a note on what the app did), not feature cards.
  Facts are sentences with their source, not stat banners.
- Practice: a contact list (avatar, name, one-line preview, chevron).
- Chat: a Messages-style thread (bubbles with tails, receipts, header with the avatar centered).
- X-ray: a plain dark gray inset (`#1C1C1E`) with system text and hairlines.
- Feedback: your transcript first, annotated inline; one simple trust line chart; plain summary.
- What-if: a thread splitting into alternative replies; the best one is marked with the word "Best".
- Icons: thin line icons, used sparingly, never inside a colored rounded square. No sparkles.

## Motion

Only motion that carries meaning: typing dots, a bubble sliding in, the trust number changing.
No section fade-ups or staggers. Reduced motion is always respected.

## Copy

- Headlines say something only this app could say.
- Buttons name the outcome: "Pick a friend to text", "Text Maya", "See your feedback", "Try a
  different reply". No "Get started", no arrows in labels.
- No marketing adjectives, no "not just X, it's Y", no em dashes.
- Facts carry their source: "1 in 5 US high schoolers seriously considered suicide in the past
  year (CDC Youth Risk Behavior Survey, 2023, 20.4%)" and "When teens tell someone about suicidal
  thoughts, it's most often a friend (Fox et al., 2021)".
- Safety wording follows `docs/SAFE_MESSAGING.md` exactly.

## Self-check before shipping a screen

Ask: "Would I make this exact choice for any other app?" If yes, change it. Then grep the source for
violet/indigo hexes, `gradient`, `backdrop-blur`, `Fraunces`, `uppercase tracking`, `→`, sparkles,
and em dashes in `src/i18n/*.json`.
