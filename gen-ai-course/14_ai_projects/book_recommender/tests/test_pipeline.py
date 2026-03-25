import pytest
from recommender.recommendation.pipeline import recommend

@pytest.mark.asyncio
async def test_pipeline_importable():
    # Only verify that it is callable and structured correctly
    assert callable(recommend)
