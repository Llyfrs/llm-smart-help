from typing import Optional, List, Tuple
import psycopg2


class RatingStorage:
    """
    QueryStorage provides a simple key/value store for queries, their answers, iteration count, cost, score, and timestamp using PostgreSQL.
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
            query TEXT PRIMARY KEY,
            answer TEXT,
            iteration INTEGER,
            cost FLOAT,
            score INTEGER CHECK (score IN (0, 1)),
            recorded_at TIMESTAMPTZ DEFAULT now()
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def save_query(self, query_text: str, answer: str, iteration: int, cost: float, score: int) -> None:
        """
        Insert or update a query record.
        :param query_text: The unique query string.
        :param answer: The answer text.
        :param iteration: Iteration number.
        :param cost: Associated cost.
        :param score: Score (0 or 1).
        """
        if score not in (0, 1):
            raise ValueError("Score must be either 0 or 1.")

        query = f"""
        INSERT INTO {self.table_name} (query, answer, iteration, cost, score, recorded_at)
        VALUES (%s, %s, %s, %s, %s, now())
        ON CONFLICT (query) DO UPDATE
        SET answer = EXCLUDED.answer,
            iteration = EXCLUDED.iteration,
            cost = EXCLUDED.cost,
            score = EXCLUDED.score,
            recorded_at = now();
        """
        self.cursor.execute(query, (query_text, answer, iteration, cost, score))
        self.connection.commit()

    def get_query(self, query_text: str) -> Optional[Tuple[str, int, float, int, str]]:
        """
        Retrieve data for a given query.
        :param query_text: The query string.
        :return: Tuple (answer, iteration, cost, score, recorded_at) or None if not found.
        """
        query = f"""
        SELECT answer, iteration, cost, score, recorded_at FROM {self.table_name}
        WHERE query = %s;
        """
        self.cursor.execute(query, (query_text,))
        result = self.cursor.fetchone()
        return result if result else None

    def list_queries(self) -> List[str]:
        """
        List all query strings stored in the table.
        :return: List of query strings.
        """
        query = f"SELECT query FROM {self.table_name};"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def delete_query(self, query_text: str) -> bool:
        """
        Delete a query record.
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
