from typing import Union, Callable, Dict

from aiogram_dialog.manager.manager import DialogManager

Predicate = Callable[[Dict, "Whenable", DialogManager], bool]
WhenCondition = Union[str, Predicate, None]


def new_when_field(fieldname: str) -> Predicate:
    def when_field(data: Dict, widget: "Whenable", manager: DialogManager) -> bool:
        return bool(data.get(fieldname))

    return when_field


def true(*_args, **_kwargs):
    return True


def false(*_args, **_kwargs):
    return False


def ensure_condition(when: WhenCondition, default: Predicate) -> Predicate:
    if when is None:
        return default
    elif isinstance(when, str):
        return new_when_field(when)
    else:
        return when


class Whenable:

    def __init__(self, when: WhenCondition = None, when_not: WhenCondition = None):
        self.condition = ensure_condition(when, true)
        self.not_condition = ensure_condition(when_not, false)

    def is_(self, data, manager):
        return self.condition(data, self, manager) and not self.not_condition(data, self, manager)
