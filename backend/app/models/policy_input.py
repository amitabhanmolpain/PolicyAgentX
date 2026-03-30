from typing import Optional

class PolicyInput:
    def __init__(
        self,
        text: str,
        region: Optional[str] = "India",
        source: Optional[str] = "user"
    ):
        self.text = text
        self.region = region
        self.source = source

    def to_dict(self):
        return {
            "text": self.text,
            "region": self.region,
            "source": self.source
        }