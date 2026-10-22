"""List the OpenAI chat models your key can use (needs OPENAI_API_KEY). Run: make models"""

from __future__ import annotations

import os

from openai import OpenAI

if __name__ == "__main__":
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    names = sorted(m.id for m in client.models.list())
    for name in names:
        if name.startswith(("gpt", "o")):
            print(name)
