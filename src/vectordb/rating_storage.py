from typing import Optional, List, Tuple
import psycopg2


class RatingStorage:
    """
    RatingStorage provides a simple key/value store for queries, their answers,
    iteration count, cost, score, and timestamp using PostgreSQL.
    Allows multiple entries with the same query string.
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
            id SERIAL PRIMARY KEY,
            query TEXT,
            answer TEXT,
            iteration INTEGER,
            cost FLOAT,
            score INTEGER CHECK (score IN (0, 1)),
            recorded_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_query ON {self.table_name} (query);
        """
        self.cursor.execute(query)
        self.connection.commit()

    def save_query(self, query_text: str, answer: str, iteration: int, cost: float, score: int) -> None:
        """
        Insert a new query record.
        :param query_text: The query string.
        :param answer: The answer text.
        :param iteration: Iteration number.
        :param cost: Associated cost.
        :param score: Score (0 or 1).
        """
        if score not in (0, 1):
            raise ValueError("Score must be either 0 or 1.")

        query = f"""
        INSERT INTO {self.table_name} (query, answer, iteration, cost, score, recorded_at)
        VALUES (%s, %s, %s, %s, %s, now());
        """
        self.cursor.execute(query, (query_text, answer, iteration, cost, score))
        self.connection.commit()

    def get_query(self, query_text: str) -> Optional[Tuple[str, int, float, int, str]]:
        """
        Retrieve the most recent entry for a given query.
        :param query_text: The query string.
        :return: Tuple (answer, iteration, cost, score, recorded_at) or None if not found.
        """
        query = f"""
        SELECT answer, iteration, cost, score, recorded_at FROM {self.table_name}
        WHERE query = %s
        ORDER BY recorded_at DESC
        LIMIT 1;
        """
        self.cursor.execute(query, (query_text,))
        result = self.cursor.fetchone()
        return result if result else None

    def list_queries(self) -> List[str]:
        """
        List all distinct query strings stored in the table.
        :return: List of query strings.
        """
        query = f"SELECT DISTINCT query FROM {self.table_name};"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def delete_query(self, query_text: str) -> bool:
        """
        Delete all records matching a query string.
        :param query_text: The query string to remove.
        :return: True if deletion succeeded.
        """
        query = f"DELETE FROM {self.table_name} WHERE query = %s;"
        self.cursor.execute(query, (query_text,))
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
