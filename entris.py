from dataclasses import dataclass


@dataclass
class SlotEntry:
    type: str
    perks: str


@dataclass
class PerkStyleEntry:
    id: int
    name: str
    icon: str
    sub_ids: list[int]

    stone: SlotEntry
    mixed: list[SlotEntry]
    stat: list[SlotEntry]


@dataclass
class ChampEntry:
    id: int
    name: str
    owned: bool
    level: int
    icon: str


@dataclass
class PerkEntry:
    name: str
    primary: int
    sub: int
    perks: list[int]
    id: int = None

    def __eq__(self, other):
        return self.primary == other.primary and self.sub == other.sub and self.perks == other.perks


@dataclass
class WebsocketResponse:
    event_type: str
    uri: str
    data: str
