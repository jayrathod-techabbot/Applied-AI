import pytest
from unittest.mock import MagicMock
from recommender.retrieval.search import hybrid_search

@pytest.mark.asyncio
async def test_hybrid_search_importable():
    # Only verify that the function can be called (though it will fail without env vars)
    with pytest.raises(Exception):
        await hybrid_search("test query", [0.1]*1536)
