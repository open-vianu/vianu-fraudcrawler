import pytest

from fraudcrawler.settings import PROCESSOR_DEFAULT_MODEL
from fraudcrawler.base.base import Setup
from fraudcrawler import Processor


@pytest.fixture
def processor():
    setup = Setup()
    processor = Processor(api_key=setup.openaiapi_key, model=PROCESSOR_DEFAULT_MODEL)
    return processor


@pytest.mark.asyncio
async def test_processor_classify_product(processor):
    context = "We are interested in medical products"
    name = "sildenafil"
    description = "buy sildenafil online"
    is_relevant = await processor.classify_product(
        context=context, name=name, description=description
    )
    assert isinstance(is_relevant, int)
    assert is_relevant in [0, 1]
