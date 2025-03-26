import pytest

from fraudcrawler.base.settings import PROCESSOR_MODEL
from fraudcrawler.base.base import Setup
from fraudcrawler import Processor

@pytest.fixture
def processor():
    setup = Setup()
    processor = Processor(api_key=setup.openaiapi_key, model=PROCESSOR_MODEL)
    return processor

def test_processor_keep_product(processor):
    product = {
        "url": "http://example.ch",
        "product": {
            "name": "sildenafil",
            "description": "buy sildenafil online",
            "metadata": {
                "probability": 0.5
            }
        }
    }
    assert processor.keep_product(product=product, country_code='ch', threshold=0.1) is True
    assert processor.keep_product(product=product, country_code='com', threshold=0.1) is False
    assert processor.keep_product(product=product, country_code='ch', threshold=0.6) is False

@pytest.mark.asyncio
async def test_processor_classify_product(processor):
    product = {
        "url": "http://example.ch",
        "product": {
            "name": "sildenafil",
            "description": "buy sildenafil online",
            "metadata": {
                "probability": 0.5
            }
        }
    }
    context = "We are interested in medical products"
    product = await processor.classify_product(product=product, context=context)
    assert 'is_relevant' in product
    assert isinstance(product['is_relevant'], int)
    assert product['is_relevant'] in [0, 1]
    