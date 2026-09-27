"""Memori multi-turn in-memory pengganti contextIdMap Langflow.

Frontend mengirim sessionId yang sama seperti dulu,
backend menyimpan riwayat chat per sesi di sini.
"""
from collections import defaultdict
from langchain_core.chat_history import InMemoryChatMessageHistory

_histories: dict[str, InMemoryChatMessageHistory] = defaultdict(
    InMemoryChatMessageHistory
)

MAX_TURNS = 10  # batasi biar prompt tidak kepanjangan


def get_history(session_id: str) -> InMemoryChatMessageHistory:
    return _histories[session_id or "default"]


def add_turn(session_id: str, user_text: str, ai_text: str) -> None:
    history = get_history(session_id)
    history.add_user_message(user_text)
    history.add_ai_message(ai_text)
    # Potong riwayat lama, simpan N turn terakhir saja
    msgs = history.messages
    if len(msgs) > MAX_TURNS * 2:
        history.clear()
        for m in msgs[-(MAX_TURNS * 2):]:
            history.add_message(m)


def history_text(session_id: str) -> str:
    history = get_history(session_id)
    lines: list[str] = []
    for m in history.messages[-(MAX_TURNS * 2):]:
        role = "User" if m.type == "human" else "AI"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


def clear_session(session_id: str) -> None:
    _histories.pop(session_id, None)
