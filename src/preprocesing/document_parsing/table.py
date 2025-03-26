from dataclasses import dataclass
from typing import List


@dataclass
class Table:
    caption: str
    headers: List[str]
    rows: List[List[str]]

    def __str__(self) -> str:
        """
        Returns markdown representation of the table
        :return:
        """

        table = f"{self.caption}:\n\n"
        table += "|" + "|".join(self.headers) + "|\n"
        table += "|" + "|".join(["---" for _ in self.headers]) + "|\n"

        for row in self.rows:
            table += "|" + "|".join(row) + "| \n"

        return table
