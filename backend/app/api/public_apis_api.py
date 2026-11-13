"""Public APIs HTTP Endpoints for NOUS.

Exposes endpoints consuming curated open public APIs from https://github.com/public-apis/public-apis:
- Open-Meteo & wttr.in (Weather Forecast)
- Free Dictionary API (Lexicon Lookup)
- Frankfurter API (Currency Exchange)
- Official Joke API (Humor)
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.services.public_apis import public_api_service

router = APIRouter(prefix="/api/public", tags=["Public APIs"])


@router.get("/weather")
async def get_weather(location: str = Query("London", description="Target city or location")):
    """Get live or verified weather forecast for any location worldwide."""
    return await public_api_service.get_weather(location=location)


@router.get("/dictionary")
async def lookup_dictionary(word: str = Query("algorithm", description="English word to define")):
    """Get word definition, phonetics, parts of speech, and synonyms."""
    return await public_api_service.lookup_definition(word=word)


@router.get("/currency")
async def convert_currency(
    amount: float = Query(100.0, description="Monetary amount to convert"),
    from_currency: str = Query("USD", description="Source 3-letter currency code"),
    to_currency: str = Query("EUR", description="Target 3-letter currency code"),
):
    """Convert currencies using European Central Bank reference exchange rates."""
    return await public_api_service.convert_currency(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
    )


@router.get("/joke")
async def get_random_joke(category: Optional[str] = Query("general", description="Category: 'general' or 'programming'")):
    """Fetch a clean joke or developer joke."""
    return await public_api_service.get_random_joke(category=category)
