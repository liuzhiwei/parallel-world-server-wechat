from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Any, Dict, Tuple, Type, TypeVar
import json


# ----- Enums -----
class TurnAction(str, Enum):
    SPEAK_USER_DIGITAL_AVATAR = "SPEAK_USER_DIGITAL_AVATAR"
    SPEAK_TRAVEL_PARTNER = "SPEAK_TRAVEL_PARTNER"

class TopicAction(str, Enum):
    INIT_AND_GENERATE = "INIT_AND_GENERATE"
    CONTINUE_TOPIC = "CONTINUE_TOPIC"
    END_AND_GENERATE = "END_AND_GENERATE"


# ----- Helpers -----
T = TypeVar("T", bound=Enum)

def _enum_from_str(enum_cls: Type[T], value: str, field_name: str) -> T:
    try:
        return enum_cls(value)
    except Exception:
        allow = ", ".join(e.value for e in enum_cls)
        raise ValueError(f"Invalid value for {field_name}: {value!r}. Allowed: {allow}")

def _ensure_list_of_str(v: Any, field_name: str) -> List[str]:
    if v is None:
        return []
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise ValueError(f"{field_name} must be a list[str]")
    return v

def _len_cn(s: Optional[str]) -> int:
    return len(s or "")


# ----- Data classes -----
@dataclass(slots=True)
class NewTopic:
    title: str
    rationale: str
    confidence: float

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["NewTopic"]:
        if data is None:
            return None
        return cls(
            title=str(data.get("title", "")),
            rationale=str(data.get("rationale", "")),
            confidence=float(data.get("confidence", 0.0)),
        )


@dataclass(slots=True)
class TopicArgs:
    topic: Optional[str] = None
    new_topic: Optional[NewTopic] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TopicArgs":
        data = data or {}
        topic = data.get("topic", None)
        topic = None if topic in (None, "null") else str(topic)
        new_topic = NewTopic.from_dict(data.get("new_topic"))
        return cls(topic=topic, new_topic=new_topic)


@dataclass(slots=True)
class ThoughtResult:
    turn_action: TurnAction
    guidance_list: List[str] = field(default_factory=list)
    topic_action: TopicAction = TopicAction.CONTINUE_TOPIC
    topic_args: TopicArgs = field(default_factory=TopicArgs)
    confidence: float = 0.0
    rationale: Optional[str] = None

    # ---- Parse ----
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtResult":
        if not isinstance(data, dict):
            raise TypeError("ThoughtResult.from_dict expects a dict")

        turn_action = _enum_from_str(TurnAction, data.get("turn_action", ""), "turn_action")
        topic_action = _enum_from_str(TopicAction, data.get("topic_action", ""), "topic_action")
        guidance_list = _ensure_list_of_str(data.get("guidance_list"), "guidance_list")
        topic_args = TopicArgs.from_dict(data.get("topic_args"))
        confidence = float(data.get("confidence", 0.0))
        rationale = data.get("rationale", None)
        rationale = None if rationale is None else str(rationale)

        obj = cls(
            turn_action=turn_action,
            guidance_list=guidance_list,
            topic_action=topic_action,
            topic_args=topic_args,
            confidence=confidence,
            rationale=rationale,
        )
        return obj

    # ---- Non-throwing parse helper ----
    @classmethod
    def try_from_dict(cls, data: str) -> Tuple[Optional["ThoughtResult"], Optional[str]]:
        """
        从JSON字符串解析ThoughtResult对象
        
        Args:
            data: JSON字符串
            
        Returns:
            (ThoughtResult对象, 错误信息) 元组
        """
        try:
            # 解析JSON字符串
            dict_data = json.loads(data)
            
            obj = cls.from_dict(dict_data)
            err = obj.validate()
            if err:
                return None, f"validation failed: {err}"
            return obj, None
        except json.JSONDecodeError as e:
            return None, f"JSON parse failed: {e}"
        except Exception as e:
            return None, f"parse failed: {e}"

    # ---- Export ----
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["turn_action"] = self.turn_action.value
        d["topic_action"] = self.topic_action.value
        return d

    # ---- Business validation ----
    def validate(self) -> Optional[str]:

        # guidance_list 数量
        gl = self.turn_args.guidance_list
        if not (1 <= len(gl)):
            return f"guidance_list length must be 1..3, got {len(gl)}"

        # 每条建议, 例如：回复 1–25 字
        for i, g in enumerate(gl):
            L = _len_cn(g)
            if not (2 <= L):
                return f"guidance_list[{i}] length less 2, got {L}: {g!r}, not good guidance"

        # topic logic
        if self.topic_action == TopicAction.END_AND_GENERATE:
            if not self.topic_args or not self.topic_args.new_topic:
                return "END_AND_GENERATE requires topic_args.new_topic"
        if self.topic_action == TopicAction.CONTINUE_TOPIC:
            if not (self.topic_args and self.topic_args.topic):
                return "CONTINUE_TOPIC requires non-empty topic_args.topic"

        return None
