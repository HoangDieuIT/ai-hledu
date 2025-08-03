from collections.abc import Iterable
from typing import Optional
from itertools import zip_longest, chain
from fastapi import Header


class I18N:
    """
    Class for localizing messages.
    """
    class Lang:
        def __init__(self, lang: str) -> None:
            self.tags = [v.lower() for v in lang.split('-')]

        def __eq__(self, other: "I18N.Lang") -> bool:
            return all(t1 == t2 for t1, t2 in zip_longest(self.tags, other.tags))

        def __lt__(self, other: "I18N.Lang") -> bool:
            return len(self.tags) > len(other.tags) and all(t1 == t2 for t1, t2 in zip(self.tags, other.tags))

        def __le__(self, other: "I18N.Lang") -> bool:
            return self == other or self < other

        def __gt__(self, other: "I18N.Lang") -> bool:
            return not self <= other

        def __ge__(self, other: "I18N.Lang") -> bool:
            return not self < other

        @property
        def value(self) -> str:
            return '-'.join(self.tags)

    def __init__(self, accept_language: list[str] | None) -> None:
        """
        Initializes with a list of languages to be localized.

        Args:
            accept_language: List of languages. *Accept-Language* format of HTTP header.
        """
        self.accept_languages = self._parse(accept_language or [])

    def _parse(self, queries: list[str]) -> list[tuple['I18N.Lang', float]]:
        def parse_lang(lang: str) -> tuple[I18N.Lang, float]:
            lang = lang.strip()
            if ';' in lang:
                lang, q = lang.split(';')
                q = float(q.split('=')[1])
                return I18N.Lang(lang), 0.0
            else:
                q = 1.0
            return I18N.Lang(lang), q

        def parse(al: str) -> Iterable[tuple[I18N.Lang, float]]:
            for l in al.split(','):
                lang, q = parse_lang(l)
                if lang:
                    yield lang, q

        unordered = chain.from_iterable(parse(al) for al in queries)

        return sorted(unordered, key=lambda x: x[1], reverse=True)

    def lookup(self, availables: list[str]) -> Optional['I18N.Lang']:
        """
        Gets the most appropriate language from the language candidates.

        Args:
            availables: Priority-ordered list of languages.
        Returns:
            The most appropriate language.
        """
        available_langs = [I18N.Lang(l) for l in availables]

        for lang, _ in self.accept_languages:
            match = min(filter(lambda l: l >= lang, available_langs), default=None)
            if match:
                return match

        return None


def i18n(accept_language: list[str] | None = Header(default=None, include_in_schema=False)) -> I18N:
    """
    Function to receive I18N as a FastAPI Dependency.
    """
    return I18N(accept_language)
