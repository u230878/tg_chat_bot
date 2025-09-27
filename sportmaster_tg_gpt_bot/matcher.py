from dataclasses import dataclass
from typing import List
import yaml
from pathlib import Path

@dataclass
class Intent:
    name: str
    keywords: List[str]
    reply: str

class IntentMatcher:
    def __init__(self, intents: List[Intent], fallback: str):
        self.intents = intents
        self.fallback = fallback

    @classmethod
    def from_yaml(cls, path: str) -> "IntentMatcher":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        intents = [Intent(**i) for i in data.get("intents", [])]
        fallback = data.get("fallback", "Запрос не распознан.")
        return cls(intents, fallback)

    def match(self, text: str) -> str:
        t = (text or "").lower()
        for intent in self.intents:
            for kw in intent.keywords:
                if kw in t:
                    return intent.reply
        return self.fallback