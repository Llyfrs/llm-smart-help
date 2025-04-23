from typing import List, Optional

import psycopg2


class TermStorage:
    """
    TermStorage provides a simple key/value store for terms and their contexts using PostgreSQL.

    Each term is a unique key (TEXT PRIMARY KEY) associated with a context (TEXT).
    """

    def __init__(
        self,
        name: str,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        connection_string: str = None,
    ):
        if connection_string:
            self.connection = psycopg2.connect(connection_string)
        elif host and port and user and password and database:
            self.connection = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
            )
        else:
            raise ValueError(
                "Invalid arguments. Provide either connection_string or host, port, user, password, and database."
            )

        self.cursor = self.connection.cursor()
        self.table_name = name

        # Ensure table exists
        self._create_table()

    def _create_table(self) -> None:
        query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            term TEXT PRIMARY KEY,
            context TEXT,
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def save_term(self, term: str, context: str) -> None:
        """
        Insert or update a term and its context.
        :param term: The unique key identifying the term.
        :param context: The associated context text.
        """
        query = f"""
        INSERT INTO {self.table_name} (term, context)
        VALUES (%s, %s)
        ON CONFLICT (term) DO UPDATE
        SET context = EXCLUDED.context,
            updated_at = now();
        """
        self.cursor.execute(query, (term, context))
        self.connection.commit()

    def get_context(self, term: str) -> Optional[str]:
        """
        Retrieve the context for a given term.
        :param term: The term key.
        :return: The context string, or None if not found.
        """
        query = f"SELECT context FROM {self.table_name} WHERE term = %s;"
        self.cursor.execute(query, (term,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def list_terms(self) -> List[str]:
        """
        List all terms stored in the table.
        :return: List of term keys.
        """
        query = f"SELECT term FROM {self.table_name};"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def delete_term(self, term: str) -> bool:
        """
        Delete a term and its context.
        :param term: The term key to remove.
        :return: True if deletion succeeded.
        """
        query = f"DELETE FROM {self.table_name} WHERE term = %s;"
        self.cursor.execute(query, (term,))
        self.connection.commit()
        return True

    def clear_table(self) -> bool:
        """
        Remove all entries from the table.
        """
        query = f"TRUNCATE TABLE {self.table_name};"
        self.cursor.execute(query)
        self.connection.commit()
        return True
