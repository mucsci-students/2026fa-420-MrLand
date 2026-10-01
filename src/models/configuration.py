from dataclasses import dataclass, field


@dataclass
class Configuration:
    courses: list = field(default_factory=list)
    faculty: list = field(default_factory=list)
    rooms: list = field(default_factory=list)
    labs: list = field(default_factory=list)
    time_blocks: list = field(default_factory=list)
    class_patterns: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    global_settings: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "courses": self.courses,
            "faculty": self.faculty,
            "rooms": self.rooms,
            "labs": self.labs,
            "time_blocks": self.time_blocks,
            "class_patterns": self.class_patterns,
            "conflicts": self.conflicts,
            "global_settings": self.global_settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Configuration":
        return cls(
            courses=data.get("courses", []),
            faculty=data.get("faculty", []),
            rooms=data.get("rooms", []),
            labs=data.get("labs", []),
            time_blocks=data.get("time_blocks", []),
            class_patterns=data.get("class_patterns", []),
            conflicts=data.get("conflicts", []),
            global_settings=data.get("global_settings", {}),
        )
