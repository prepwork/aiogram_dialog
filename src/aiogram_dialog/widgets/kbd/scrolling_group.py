from typing import Awaitable, Callable, Dict, List, Optional, Union

from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.api.protocols import DialogManager, DialogProtocol
from aiogram_dialog.widgets.common import ManagedWidget, WhenCondition
from aiogram_dialog.widgets.text import Text, Const, Format
from aiogram_dialog.widgets.widget_event import (
    ensure_event_processor,
    WidgetEventProcessor,
)

from .base import Keyboard
from .button import Button
from .group import Group

OnStateChanged = Callable[
    [ChatEvent, "ManagedScrollingGroupAdapter", DialogManager],
    Awaitable,
]


class PagerButton:
    def __init__(self, text: Text):
        self.text = text
        self.callback_data: str = None  # set by ScrollingGroup

    def _own_callback_data(self):
        return self.callback_data

    async def render_keyboard(
        self,
        data: Dict,
        manager: DialogManager,
    ) -> List[List[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text=await self.text.render_text(data, manager),
                    callback_data=self._own_callback_data(),
                ),
            ],
        ]


class PrevPage(PagerButton):
    def __init__(self, text: Text = Const("<")):
        super().__init__(text)


class NextPage(PagerButton):
    def __init__(self, text: Text = Const(">")):
        super().__init__(text)


class FirstPage(PagerButton):
    def __init__(self, text: Text = Format("{__value__}")):
        super().__init__(text)


class LastPage(PagerButton):
    def __init__(self, text: Text = Format("{__value__}")):
        super().__init__(text)


class CurrentPage(PagerButton):
    def __init__(self, text: Text = Format("{__value__}")):
        super().__init__(text)


class ScrollingGroup(Group):
    def __init__(
        self,
        *buttons: Keyboard,
        id: str,
        width: Optional[int] = None,
        height: int = 0,
        when: WhenCondition = None,
        on_page_changed: Union[
            OnStateChanged,
            WidgetEventProcessor,
            None,
        ] = None,
        hide_on_single_page: bool = False,
        pager_template: List[PagerButton] = (
            FirstPage(),
            PrevPage(),
            CurrentPage(),
            NextPage(),
            LastPage(),
        )
    ):
        super().__init__(*buttons, id=id, width=width, when=when)
        self.height = height
        self.on_page_changed = ensure_event_processor(on_page_changed)
        self.hide_on_single_page = hide_on_single_page
        self.pager_template = pager_template

    async def _render_keyboard(
        self,
        data: Dict,
        manager: DialogManager,
    ) -> List[List[InlineKeyboardButton]]:
        kbd = await super()._render_keyboard(data, manager)
        pages = len(kbd) // self.height + bool(len(kbd) % self.height)
        last_page = pages - 1
        if pages == 0 or (pages == 1 and self.hide_on_single_page):
            return kbd
        current_page = min(last_page, self.get_page(manager))
        next_page = min(last_page, current_page + 1)
        prev_page = max(0, current_page - 1)

        pager = [[]]
        b: Button

        for b in self.pager_template:
            if isinstance(b, PrevPage):
                b.callback_data = self._item_callback_data(prev_page)
                data["__value__"] = prev_page + 1
            if isinstance(b, NextPage):
                b.callback_data = self._item_callback_data(next_page)
                data["__value__"] = next_page + 1
            if isinstance(b, FirstPage):
                b.callback_data = self._item_callback_data("0")
                data["__value__"] = "1"
            elif isinstance(b, LastPage):
                b.callback_data = self._item_callback_data(last_page)
                data["__value__"] = last_page + 1
            elif isinstance(b, CurrentPage):
                b.callback_data = self._item_callback_data(current_page)
                data["__value__"] = current_page + 1

            raw_keyboard = await b.render_keyboard(data=data, manager=manager)
            pager[0].append(raw_keyboard[0][0])

        page_offset = current_page * self.height
        return kbd[page_offset : page_offset + self.height] + pager

    async def _process_item_callback(
        self,
        callback: CallbackQuery,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await self.set_page(callback, int(data), manager)
        return True

    def get_page(self, manager: DialogManager) -> int:
        return manager.current_context().widget_data.get(self.widget_id, 0)

    async def set_page(
        self,
        event: ChatEvent,
        page: int,
        manager: DialogManager,
    ) -> None:
        manager.current_context().widget_data[self.widget_id] = page
        await self.on_page_changed.process_event(
            event,
            self.managed(manager),
            manager,
        )

    def managed(self, manager: DialogManager):
        return ManagedScrollingGroupAdapter(self, manager)


class ManagedScrollingGroupAdapter(ManagedWidget[ScrollingGroup]):
    def get_page(self) -> int:
        return self.widget.get_page(self.manager)

    async def set_page(self, page: int) -> None:
        return await self.widget.set_page(
            self.manager.event,
            page,
            self.manager,
        )
