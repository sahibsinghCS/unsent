---
title: FirstReply
emoji: 💬
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Practice the text that could help a struggling friend
---

# FirstReply

Practice texting a friend who is struggling, then get feedback on what helped.

- A deterministic engine decides what the practice friend may reveal and when; OpenAI only writes
  the friend's wording, and a verifier plus the Guardian safety model check every reply.
- Our own trained models score the helper's messages and explain the turning point.
- Need help right now? In the US, call or text **988** (Suicide & Crisis Lifeline). The app's
  "Help now" button lists lines for other countries. In immediate danger, call 911.

This Space runs the Docker image from the project repository (Congressional App Challenge 2026,
IL-11). Conversations live only in server memory and are deleted after an hour of inactivity.
