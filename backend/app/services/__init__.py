"""Public APIs service package for NOUS.

Integrates curated public keyless APIs from https://github.com/public-apis/public-apis:
- Open-Meteo & wttr.in (Weather & Forecasts)
- Free Dictionary API (Lexical Definitions, Phonetics, Synonyms)
- Frankfurter API (Live European Central Bank Currency Exchange Rates)
- Official Joke API (Clean & Programming Humor)
"""

from backend.app.services.public_apis import public_api_service

__all__ = ["public_api_service"]
