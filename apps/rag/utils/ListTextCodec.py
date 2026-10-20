"""ListTextCodec - the DB keeps `keyword` / `question` as one TEXT column,
while the API / JSON uses lists.  One item per line keeps it lossless
(questions can contain commas)."""


class ListTextCodec:
    SEPARATOR = "\n"

    @classmethod
    def join(cls, items):
        return cls.SEPARATOR.join(i.strip() for i in (items or []) if i and i.strip())

    @classmethod
    def split(cls, text):
        return [line.strip() for line in (text or "").split(cls.SEPARATOR) if line.strip()]
