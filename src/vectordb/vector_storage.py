import json
from typing import Literal

import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm

from src.vectordb.vector import Vector


class VectorStorage:
    """
    VectorStorage is a class that provides a simple interface to store and retrieve vectors from a PostgreSQL database.


    If the same table name is used it is persisted between different instances of the class. You need to set the same dimension every time, for the same table name.
    You can use :meth:`delete_table` to remove the table from the database, and thus resting it.
    """

    def __init__(
        self,
        name: str,
        dimension: int,
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
                host=host, port=port, user=user, password=password, database=database
            )
        else:
            raise ValueError(
                "Invalid arguments. Either connection_string or host, port, user, password, and database must be provided."
            )

        self.cursor = self.connection.cursor()
        self.table_name = name
        self.dimension = dimension

        self._create_table()

        actual_dimension = self._vector_size()
        if actual_dimension != self.dimension:
            raise ValueError(
                f"Dimension of the {self.table_name} table must be {actual_dimension} not {self.dimension} as specified the first time the table was created."
            )

    def _vector_size(self) -> int | None:
        query = f"""
                SELECT attname, atttypmod
                FROM pg_attribute
                WHERE attrelid = '{self.table_name}'::regclass
                AND attname = 'embedding';
                """

        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result:
            return result[1]
        return None

    def _create_table(self):
        query = f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                embedding vector({self.dimension}),
                file_name text,
                file_position integer,
                content text,
                metadata jsonb,
                updated_at timestamp with time zone DEFAULT now()
                );
                """

        self.cursor.execute(query)
        self.connection.commit()

    def _install_extension(self):
        query = "CREATE EXTENSION IF NOT EXISTS vector;"
        self.cursor.execute(query)
        self.connection.commit()

    def delete_table(self) -> bool:
        """
        Drop the table from the database. Removing all data.
        :return:
        """
        query = f"DROP TABLE IF EXISTS {self.table_name};"
        self.cursor.execute(query)
        self.connection.commit()
        return True

    def insert(
        self,
        vector: Vector
    ):
        """
        Insert a new vector into the database.
        :param file_name: The name of the file the vector belongs to.
        :param file_position: The position of the vector in the file. Up to the user how to use, I recommend using it for keeping of order.
        :param content: The text content of the vector.
        :param vector: The vector to be stored.
        :param metadata: Additional metadata to be stored.
        :return:
        """
        query = f"""
                INSERT INTO {self.table_name} (embedding, file_name, file_position, content, metadata)
                VALUES (%s, %s, %s, %s, %s);
                """

        self.cursor.execute(
            query, (vector, vector.file_name, vector.file_position, vector.content, json.dumps(vector.metadata))
        )
        self.connection.commit()

    def batch_insert(
            self,
            entries: list[Vector],
            batch_size: int = 1000,
            page_size: int = 500,
            verbose: bool = False
    ):
        """
        Efficient batch insert using psycopg2's execute_batch


        :param entries: List of Vector objects to insert. Note that ID and updated_at fields are ignored.
        :param batch_size: Number of records per batch (default 1000)
        :param page_size:  Number of records per page (executed on the database) (default 500)
        :param verbose: Whether to show progress bar (default False)
        """
        if not entries:
            return

        query = f"""
            INSERT INTO {self.table_name} 
            (embedding, file_name, file_position, content, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """

        # Prepare data tuples in correct order
        data = [
            (
                entry.vector,
                entry.file_name,
                entry.file_position,
                entry.content,
                json.dumps(entry.metadata)
            )
            for entry in entries
        ]

    # Use execute_batch with progress tracking
        with tqdm(total=len(data), desc="Inserting Batches", unit="batch", disable=not verbose) as pbar:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                execute_batch(self.cursor, query, batch, page_size=page_size)
                pbar.update(len(batch))
                self.connection.commit()

    def query(self, vector: list[float], n: int = 10, distance: Literal["l2", "inner_product", "cosine", "l1", "hamming", "jaccard"] = "cosine")  -> list[Vector]:

        dic = {
            "l2": "<->",
            "inner_product": "<#>",
            "cosine": "<=>",
            "l1": "<+>",
            "hamming": "<~>",
            "jaccard": "<%>"
        }

        symbol = dic[distance]

        query = f"""
                SELECT id, embedding, file_name, file_position, content, metadata, updated_at, embedding {symbol} %s::vector as distance
                FROM {self.table_name}
                ORDER BY distance
                LIMIT %s;
                """

        self.cursor.execute(query, (vector, n))
        results = self.cursor.fetchall()

        vectors = [
            self._parse(result)
            for result in results
        ]

        return vectors

    def get_file(self, file_name: str) -> list[Vector]:
        query = f"""
                SELECT *
                FROM {self.table_name}
                WHERE file_name = %s
                """

        self.cursor.execute(query, (file_name,))
        results = self.cursor.fetchall()

        vectors = [
            self._parse(result)
            for result in results
        ]

        return vectors


    @staticmethod
    def _parse(result) -> Vector:
        return Vector(
            id=result[0],
            vector=result[1],
            file_name=result[2],
            file_position=result[3],
            content=result[4],
            metadata=result[5],
            updated_at=result[6],
        )