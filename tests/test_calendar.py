from datetime import datetime
from types import SimpleNamespace

from composio.exceptions import ComposioMultipleConnectedAccountsError

from squad.calendar import CalendarLinker, composio_user_id
from tests.fakes import TZ

START = datetime(2026, 10, 26, 0, 0, tzinfo=TZ)
END = datetime(2026, 11, 2, 0, 0, tzinfo=TZ)


class StubAccounts:
    def __init__(self, items=(), link_error=None):
        self.items = list(items)
        self.link_error = link_error
        self.link_calls = []
        self.list_calls = []
        self.deleted = []

    def link(self, user_id, auth_config_id, *, callback_url=None):
        self.link_calls.append((user_id, auth_config_id, callback_url))
        if self.link_error:
            raise self.link_error
        return SimpleNamespace(redirect_url="https://connect.composio.dev/link/abc")

    def list(self, **kwargs):
        self.list_calls.append(kwargs)
        return SimpleNamespace(items=self.items)

    def delete(self, nanoid):
        self.deleted.append(nanoid)


class StubTools:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, slug, arguments, **kwargs):
        self.calls.append((slug, arguments, kwargs))
        if self.error:
            raise self.error
        return self.result


def make_linker(accounts=None, tools=None):
    composio = SimpleNamespace(
        connected_accounts=accounts or StubAccounts([SimpleNamespace(id="ca_1")]),
        tools=tools or StubTools(),
    )
    return CalendarLinker(composio, "ac_test", "https://squad.example/linked"), composio


def ok_result():
    return {
        "successful": True,
        "error": None,
        "data": {
            "calendars": {
                "primary": {
                    "busy": [
                        {
                            "start": "2026-10-28T18:00:00-07:00",
                            "end": "2026-10-28T19:30:00-07:00",
                        }
                    ]
                },
                "other@example.com": {
                    "busy": [
                        {"start": "2026-10-30T10:00:00Z", "end": "2026-10-30T11:00:00Z"}
                    ]
                },
            }
        },
    }


def test_composio_user_id():
    assert composio_user_id("42") == "discord:42"


def test_connect_url_returns_redirect():
    linker, composio = make_linker()
    assert linker.connect_url("42") == "https://connect.composio.dev/link/abc"
    assert composio.connected_accounts.link_calls == [
        ("discord:42", "ac_test", "https://squad.example/linked")
    ]


def test_already_connected_returns_none():
    accounts = StubAccounts(link_error=ComposioMultipleConnectedAccountsError("dup"))
    linker, _ = make_linker(accounts=accounts)
    assert linker.connect_url("42") is None


def test_is_connected_and_disconnect():
    accounts = StubAccounts([SimpleNamespace(id="ca_1"), SimpleNamespace(id="ca_2")])
    linker, _ = make_linker(accounts=accounts)
    assert linker.is_connected("42") is True
    assert accounts.list_calls[0] == {
        "user_ids": ["discord:42"],
        "toolkit_slugs": ["googlecalendar"],
        "statuses": ["ACTIVE"],
    }
    linker.disconnect("42")
    assert accounts.deleted == ["ca_1", "ca_2"]
    assert not make_linker(accounts=StubAccounts([]))[0].is_connected("42")


def test_busy_blocks_parses_nested_calendars():
    linker, _ = make_linker(tools=StubTools(result=ok_result()))
    blocks = linker.busy_blocks("42", START, END, TZ)
    assert [(b.start.isoformat(), b.end.isoformat()) for b in blocks] == [
        ("2026-10-28T18:00:00-07:00", "2026-10-28T19:30:00-07:00"),
        ("2026-10-30T10:00:00+00:00", "2026-10-30T11:00:00+00:00"),
    ]


def test_busy_blocks_none_on_failure():
    failed = {"successful": False, "error": "boom", "data": {}}
    assert (
        make_linker(tools=StubTools(result=failed))[0].busy_blocks("42", START, END, TZ)
        is None
    )
    raising = StubTools(error=RuntimeError("network"))
    assert make_linker(tools=raising)[0].busy_blocks("42", START, END, TZ) is None
    not_linked = make_linker(accounts=StubAccounts([]), tools=StubTools(ok_result()))
    assert not_linked[0].busy_blocks("42", START, END, TZ) is None


def test_execute_arguments_exact():
    tools = StubTools(result=ok_result())
    linker, _ = make_linker(tools=tools)
    linker.busy_blocks("42", START, END, TZ)
    [(slug, arguments, kwargs)] = tools.calls
    assert slug == "GOOGLECALENDAR_FIND_FREE_SLOTS"
    assert arguments == {
        "items": ["primary"],
        "time_min": START.isoformat(),
        "time_max": END.isoformat(),
        "timezone": "America/Phoenix",
    }
    assert kwargs == {"user_id": "discord:42", "dangerously_skip_version_check": True}
