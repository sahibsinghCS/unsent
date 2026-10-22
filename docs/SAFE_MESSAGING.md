# Safe-messaging checklist (non-negotiable)

FirstReply is about suicide. Every piece of content (scenarios, friend lines, exemplars, UI text, the video) must follow public safe-messaging guidance, such as that from the American Foundation for Suicide Prevention (AFSP) and reportingonsuicide.org. Agents and humans check content against this list before committing it.

## Never
- [ ] Describe, name, hint at or ask about **methods, means, locations or plans**, even vaguely ("pills", "the bridge", "how", "when").
- [ ] Present suicide as a solution, as inevitable, or as a way to solve problems or get revenge.
- [ ] Include graphic or detailed descriptions of self-harm or injury.
- [ ] Have the friend encourage, dare or romanticize self-harm.
- [ ] Have the friend claim to be a real person in crisis outside the practice frame.
- [ ] Use AI to generate crisis advice for a real situation. "Real mode" is fixed, reviewed text only.
- [ ] Shame anyone for struggling or for not knowing what to say.

## Always
- [ ] Use warning signs at the level of feelings and behaviour (hopelessness, feeling like a burden, withdrawing, giving things away), never at the level of method.
- [ ] Show hope and help-seeking as possible and normal: level 4 is always reachable.
- [ ] Keep resources visible: 988 (US), "tell a trusted adult," 911 for immediate danger.
- [ ] Give a content warning before each practice scenario, and an "I need help now" button on every screen.
- [ ] Check in with the user after each session ("How are you feeling after that?").
- [ ] Keep the friend's language realistic but not graphic: "thoughts of not wanting to be alive," "thoughts of suicide."
- [ ] Mark AI-written content `review_status: "draft"` until a human has read it.

## Automated checks
- `tests/unit/test_contracts.py` scans scenarios for a list of method words.
- The ENGINE lane's bank validator runs the Guardian's `check_friend` on **every** friend line.
- The RED-TEAM lane (Wave B) tries to make the friend say unsafe things, and every failure becomes a permanent test.
