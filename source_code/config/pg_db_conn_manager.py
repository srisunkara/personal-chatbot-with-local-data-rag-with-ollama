import os
from contextlib import contextmanager
from typing import List, Dict, Any, Union

import psycopg2

# ❗ IMPORTANT: Replace these with your actual database credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'llm_playground')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASS', 'Sunny@CA')
DB_PORT = os.getenv('DB_PORT', '5432')


@contextmanager
def get_db_connection():
    """
    Provides a database connection within a context manager.
    The connection is automatically closed upon exiting the 'with' block.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        yield conn
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            conn.close()


def dict_fetch_all(cursor) -> List[Dict[str, Any]]:
    """Returns all rows from a cursor as a list of dictionaries."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_data(query: str, params: tuple = None, as_dicts: bool = True) -> Union[List[Dict[str, Any]], List[List[Any]]]:
    """
    Fetches data from the database.

    Args:
        query: The SQL query string.
        params: Optional parameters for the query.
        as_dicts: If True, returns a list of dictionaries. If False,
                  returns a list of lists. Defaults to True.

    Returns:
        A list of dictionaries or a list of lists.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if as_dicts:
                    return dict_fetch_all(cur)
                else:
                    # Fetch and return the raw data (list of tuples), then convert to list of lists
                    return [list(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


def execute_query(query: str, params: tuple = None) -> int:
    """
    Executes a DML query (INSERT, UPDATE, DELETE) and commits the transaction.
    Returns the number of rows affected.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                return cur.rowcount
    except Exception as e:
        print(f"Error executing query: {e}")
        return 0


# Example Usage
if __name__ == "__main__":
    # Example 1: Fetching data as a list of dictionaries (default behavior)
    print("Fetching users as dictionaries:")
    # In the query, use a single placeholder, and the wildcard is part of the param
    users_dict = fetch_data("SELECT * FROM personal_chat.chat_history;", as_dicts=False)
    print(users_dict)

    print("-" * 50)
