import os
from db_storage.sqlite3_db_helper import SQLiteSession as SQLite3
from exceptions import DatabaseDoesNotExist
from config import DB_NAME, REVIEWERS_SHORTHAND


intial_table_queries = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER,
    ratee_id INTEGER,
    metric_id INTEGER NOT NULL,
    score REAL CHECK (score >= 1 AND score <= 10),
    FOREIGN KEY (metric_id) REFERENCES metrics(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (ratee_id) REFERENCES users(id),
    UNIQUE(user_id, ratee_id, metric_id)
);

CREATE TABLE IF NOT EXISTS user_auth (
    user_id INTEGER NOT NULL,
    browser_uuid CHAR(36) NOT NULL,
    PRIMARY KEY (user_id, browser_uuid),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, browser_uuid)
);
"""


def get_db_path(DB_NAME) -> str:
    db_store_file = os.path.join(os.path.dirname(__file__), DB_NAME)
    return db_store_file


DB_PATH = get_db_path(os.path.join("db_storage", DB_NAME))


def initialize_tables_for_db():
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.executescript(intial_table_queries)


def delete_all_db_data():
    tables = ['users', 'metrics', 'ratings', 'user_auth']
    with SQLite3(DB_PATH) as (_, cursor):
        for table in tables:
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name=?;
            """, (table,))
            if cursor.fetchone():
                cursor.execute(f"DELETE FROM {table};")

        cursor.executescript("""
            DELETE FROM sqlite_sequence;
        """)


def check_if_db_exists():
    if not os.path.exists(DB_PATH):
        raise DatabaseDoesNotExist(f"Database '{DB_NAME}' does not exist.")


def get_initialized_user_requests() -> dict[str, str]:
    query = """
        SELECT users.name, user_auth.browser_uuid
        FROM user_auth
        JOIN users ON user_auth.user_id = users.id;
    """
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}
    for name, browser_uuid in rows:
        if name not in result:
            result[name] = browser_uuid
    return result


def get_metric_id(metric_name) -> int:
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.execute("""
            SELECT id from metrics where name=?;
        """, metric_name)
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            raise Exception(f"Metric with name '{metric_name}' does not exist.")


def insert_all_data(user_data=(), metric_data=(), rating_data=(), auth_data=()) -> None:
    """
    Inserts data into users, metrics, ratings, and user_auth tables.

    Parameters:
        db_path (str): Path to the SQLite database.
        user_data (tuple): (username, name, description)
        metric_data (tuple): (name,)
        rating_data (tuple): (user_id, ratee_id, metric_id, score)
        auth_data (tuple): (user_id, browser_uuid)

    Example:
        insert_all_data(
            db_path="mydb.sqlite",
            user_data=("jdoe", "John Doe"),
            metric_data=("helpfulness", "Colleague is helpful to you and others"),
            rating_data=(1, 2, 1, 8.5),
            auth_data=(1, "550e8400-e29b-41d4-a716-446655440000")
        )
    """
    with SQLite3(DB_PATH) as (_, cursor):
        if user_data:
            for name, username in user_data:
                # Insert into users table
                cursor.execute("""
                    INSERT INTO users (
                        name, username
                    ) VALUES (?, ?);""", (name, username))

        if metric_data:
            for metric, desc in metric_data:
                # Insert into metrics table
                cursor.execute("""
                    INSERT INTO metrics (
                        name, description
                    ) VALUES (?, ?);""", (metric, desc))

        if rating_data:
            for user_id, ratee_id, metric_id, score in rating_data:
                # Insert into ratings
                cursor.execute("""
                    INSERT INTO ratings (
                        user_id, ratee_id, metric_id, score
                    ) VALUES (?, ?, ?, ?);""", (user_id, ratee_id, metric_id, score))

        if auth_data:
            # Insert into user_auth
            cursor.execute("""
                INSERT INTO user_auth (
                    user_id, browser_uuid
                ) VALUES (?, ?);""", auth_data)


def get_user_to_id_map() -> dict:
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.execute("""
            SELECT username, id from users;
        """)
        rows = cursor.fetchall()
        return dict(rows)


def get_metric_to_id_map() -> dict:
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.execute("""
            SELECT name, id from metrics;
        """)
        rows = cursor.fetchall()
        return dict(rows)


def get_reviewers_finalised_cols(reviewer_id):
    with SQLite3(DB_PATH) as (_, cursor):
        cursor.execute("""
            SELECT DISTINCT u.name
            FROM ratings r, users u
            ON r.ratee_id = u.id
            WHERE r.user_id=?;
        """, (reviewer_id,))
        rows = cursor.fetchall()
        return [REVIEWERS_SHORTHAND[it[0]] for it in rows]


# initialize_tables_for_db()

# insert_all_data(
#     user_data=("jdoe", "John Doe"),
#     metric_data=("helpfulness", "Colleague is helpful to you and others"),
#     rating_data=(1, 2, 1, 8.5),
#     auth_data=(1, "550e8400-e29b-41d4-a716-446655440000")
# )

# delete_all_db_data()

# print(get_reviewers_finalised_cols(1))
