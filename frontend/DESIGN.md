# FirstReply design: "late night"

FirstReply uses the same type and dark style as Sahib's personal site (sahibs.dev), so his work looks
like one person made it. The chat looks like iMessage, because that's where this moment happens.
It's calmer than the site because the topic is a crisis: one accent color, no neon.

Tokens live in `src/index.css` (`:root` = light, `.dark` = dark) and `tailwind.config.js`.

## Type: Sahib's type system

| Role | Font | Used for |
|---|---|---|
| Display | **Syne** 700, big and tight | Hero headline, section titles, friend names, big numbers (trust score, what-if scores). Digits in "1 in 5" are set in Plex Sans, because Syne's "1" reads like a dotless "ı" |
| UI and body | **IBM Plex Sans** 400/500/600 | Everything else, including the feedback summary as large pull text |
| Data | **IBM Plex Mono** 400/500 | X-ray numbers, trust math, metric values, sources, small tracked meta labels ("01", "SIMULATED") |
| Chat | the phone's system font | Inside the Messages thread only, so it feels like a real phone |

All fonts are self-hosted with @fontsource (Latin subsets), so the strict CSP (`font-src 'self'`)
holds. Sentence case everywhere; no italic accent words, no gradient text. Mono meta labels are used
sparingly, never above every heading.

## Color: one accent, help red only for help

| Role | Dark (signature) | Light | Used for |
|---|---|---|---|
| Canvas | `#07070B` | `#F7F6FA` | Page background |
| Raised / card | `#101017` / `#14141C` | `#F0EFF5` / `#FFFFFF` | Bands, cards |
| Hairline | `#24242E` | `#E6E4EE` | Card borders, dividers |
| Text / muted | `#F6F4FA` / `#A39FB3` | `#0B0B12` / `#5E5A6E` | Text |
| Accent (one) | `#0A6EF0` fill, `#4DA3FF` text | `#0071EB` fill, `#0062CC` text | Primary pill buttons, links, focus, "Best", your bubbles, the trust gauge |
| Annotation | helped `#30D158`, hurt `#FF6961` | helped `#1B7532`, hurt `#D70015` | Trust changes, detected skills, "you lost them" |
| Help | `#D63A40` (white text) | `#C41230` | Only "I need help now", 988 and the crisis card |

The accent is the iMessage blue already in the chat. To use Sahib's `#FF4FD8` instead, change
`--brand` and `--brand-deep` only (and re-run `npm run test:a11y`). Every text pair passes WCAG AA.

No glass or backdrop blur, no glows or colored shadows, no grain, no gradients on text or buttons.
The only background moments are in the landing hero: the star field (dark) or dawn wash (light) and the breathing light behind the phone.

## Layout and components

- Max-width containers (72rem) with a strong left edge, generous whitespace, hairline section rules.
- Cards: 16px radius, 1px hairline, no shadow. Clickable cards lift 2px on hover with a slightly
  brighter border (`.card-lift`), like the project cards on sahibs.dev.
- Buttons are pills: a solid accent primary and an outline secondary, with a subtle press state.
- Landing: big Syne headline beside the live phone demo (a recorded real run); a full-bleed night
  band with a huge "1 in 5" and sourced sentences; three steps, each showing a real snippet of the
  app (bubbles, an X-ray row, "you said / what brought her back") instead of icons; the annotated
  real conversation; a calm safety card.
- Practice: story cards (solid-tone initial avatar, name in Syne, situation, plain chips); "Add your
  own friend" is the last card with a dashed hairline.
- Chat: the Messages thread is unchanged. The side panel has a trust gauge (accent arc, Syne
  number), the disclosure ladder and skill chips. X-ray is a solid dark panel with mono data.
- Feedback: summary as pull text, a numbered timeline, "This is where you lost them" (you said /
  what would have worked), the trust chart, then the full annotated conversation.
- What-if: branching futures; "Best" is a solid accent border plus the word "Best".

## Motion: calm, like a breath

Slow and eased (400 to 1200 ms, ease-out or ease-in-out), never springy. One meaningful moment
at a time. Everything plays once, and with reduced motion everything is static in its final state.

- **Opening (landing, about 2.5 s, never blocks reading):** a very sparse, slowly drifting star field
  on a canvas in dark mode (52 stars, 30 fps cap, paused when hidden or off-screen) or a soft dawn
  wash in light mode; a blue light behind the phone that *breathes* on a 5.5 s loop (max opacity
  0.35 dark / 0.18 light); the headline rises line by line (700 ms, 120 ms apart); the phone rises
  24 px and fades in; Maya's typing dots, then her first texts; the buttons fade in last.
- **Scroll moments (once, at ~30% in view):** the "1 in 5" band lights one of five figures in blue;
  each "how it works" snippet animates its own story (bubbles slide in, the X-ray trust bar fills and
  the number ticks to its real value, "you said" then "what brought her back"); annotated rows fade
  in with an 8 px rise.
- **Everywhere:** card hover lift (2 px, brighter hairline, 200 ms) and a 0.98 press on pills.
- **Never:** flashing, parallax on text, scroll-jacking, sound. Help UI ("I need help now", 988,
  the crisis card) never animates. Ambient motion exists only in the landing hero.

## Copy

- Buttons name the outcome: "Pick a friend to text", "Text Maya", "Try a different reply".
- No marketing adjectives, no em dashes. Facts carry their source (CDC YRBS 2023, 20.4%, "in the past
  year"; Fox et al., 2021). Numbers on the landing come from a recorded real run.
- Safety wording follows `docs/SAFE_MESSAGING.md` exactly.

## Self-check before shipping a screen

Grep the source for violet/indigo hexes, `backdrop-blur`, `blur-`, `shadow-glow`, `Fraunces`,
gradient text, sparkles and em dashes in `src/i18n/*.json`; run `npm run test:a11y` in both themes.
