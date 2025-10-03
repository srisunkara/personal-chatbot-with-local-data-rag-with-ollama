from __future__ import annotations

from typing import List, Optional, Dict, Any

from config.pg_db_conn_manager import fetch_data, execute_query
from config.models import (
    ChatGroupDtl,
    ChatGroupDtlCreate,
    ChatGroupDtlUpdate,
    ChatHistory,
    ChatHistoryCreate,
    ChatHistoryUpdate,
)

SCHEMA = "personal_chat"


# -------------------- Chat Group DTL --------------------

def list_chat_groups(active_only: bool = False) -> List[ChatGroupDtl]:
    where_clause = "WHERE is_active = true" if active_only else ""
    rows = fetch_data(
        f"SELECT id, user_id, group_name, group_desc, is_active, created_ts FROM {SCHEMA}.chat_group_dtl {where_clause} ORDER BY id;"
    )
    return [ChatGroupDtl(**row) for row in rows]


def get_chat_group(group_id: int) -> Optional[ChatGroupDtl]:
    rows = fetch_data(
        f"SELECT id, user_id, group_name, group_desc, is_active, created_ts FROM {SCHEMA}.chat_group_dtl WHERE id = %s;",
        (group_id,),
    )
    if not rows:
        return None
    return ChatGroupDtl(**rows[0])


def create_chat_group(payload: ChatGroupDtlCreate) -> int:
    sql = (
        f"INSERT INTO {SCHEMA}.chat_group_dtl (id, user_id, group_name, group_desc, is_active) "
        f"VALUES (%s, %s, %s, %s, %s);"
    )
    return execute_query(
        sql,
        (
            payload.id,
            payload.user_id,
            payload.group_name,
            payload.group_desc,
            payload.is_active,
        ),
    )


essential_group_fields = {"user_id", "group_name", "group_desc", "is_active"}


def update_chat_group(group_id: int, payload: ChatGroupDtlUpdate) -> int:
    data: Dict[str, Any] = payload.model_dump(exclude_none=True)
    if not data:
        return 0
    # Only allow known fields
    data = {k: v for k, v in data.items() if k in essential_group_fields}
    if not data:
        return 0
    sets = ", ".join([f"{k} = %s" for k in data])
    params = list(data.values()) + [group_id]
    sql = f"UPDATE {SCHEMA}.chat_group_dtl SET {sets} WHERE id = %s;"
    return execute_query(sql, tuple(params))


def delete_chat_group(group_id: int) -> int:
    return execute_query(f"DELETE FROM {SCHEMA}.chat_group_dtl WHERE id = %s;", (group_id,))


# -------------------- Chat History --------------------

def list_chat_history(limit: int = 200) -> List[ChatHistory]:
    rows = fetch_data(
        f"SELECT id, user_id, user_inquiry, assistant_response, reference_id, chat_group_id, created_ts "
        f"FROM {SCHEMA}.chat_history ORDER BY created_ts DESC LIMIT %s;",
        (limit,),
    )
    return [ChatHistory(**row) for row in rows]


def get_chat_history(record_id: int) -> Optional[ChatHistory]:
    rows = fetch_data(
        f"SELECT id, user_id, user_inquiry, assistant_response, reference_id, chat_group_id, created_ts "
        f"FROM {SCHEMA}.chat_history WHERE id = %s;",
        (record_id,),
    )
    if not rows:
        return None
    return ChatHistory(**rows[0])


def create_chat_history(payload: ChatHistoryCreate) -> int:
    sql = (
        f"INSERT INTO {SCHEMA}.chat_history (id, user_id, user_inquiry, assistant_response, reference_id, chat_group_id) "
        f"VALUES (%s, %s, %s, %s, %s, %s);"
    )
    return execute_query(
        sql,
        (
            payload.id,
            payload.user_id,
            payload.user_inquiry,
            payload.assistant_response,
            payload.reference_id,
            payload.chat_group_id,
        ),
    )


essential_history_fields = {
    "user_id",
    "user_inquiry",
    "assistant_response",
    "reference_id",
    "chat_group_id",
}


def update_chat_history(record_id: int, payload: ChatHistoryUpdate) -> int:
    data: Dict[str, Any] = payload.model_dump(exclude_none=True)
    if not data:
        return 0
    data = {k: v for k, v in data.items() if k in essential_history_fields}
    if not data:
        return 0
    sets = ", ".join([f"{k} = %s" for k in data])
    params = list(data.values()) + [record_id]
    sql = f"UPDATE {SCHEMA}.chat_history SET {sets} WHERE id = %s;"
    return execute_query(sql, tuple(params))


def delete_chat_history(record_id: int) -> int:
    return execute_query(f"DELETE FROM {SCHEMA}.chat_history WHERE id = %s;", (record_id,))
