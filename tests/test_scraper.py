from scripts.scraper import Scraper
from tests.samplehtml import sample

class TestScraper:
    def test_parse_base_with_real_html(self):
        scraper = Scraper()
        scraper.base_page = sample
        scraper.parse_base()

        assert scraper.stations is not None
        assert 'places' in scraper.stations
        assert type(scraper.stations) == dict

    def test_get_links(self):
        scraper = Scraper()
        scraper.stations = {"places" : [{'id': 1, 'guid': 'https://someurl.com'}, {'id':2, 'guid':'https://someurl.com'}]}
        scraper.get_links()
        assert type(scraper.stations) == dict
        assert type(scraper.links) == dict
        assert scraper.links == {1: 'https://someurl.com', 2: 'https://someurl.com'}
        
    def test_generate_coroutines(self):
        scraper = Scraper()
        scraper.links = {1: 'https://someurl.com', 2: 'https://someurl.com'}
        scraper.generate_coroutines()
        assert type(scraper.coroutines) == list
        assert len(scraper.coroutines) == 2
    
    def test_parse_prices(self):
        scraper = Scraper()
        scraper.cororesponses = [{1: '<html><div class="price">€ 1.50</div><div class="price">€ 2.50</div></html>'}, {2 :'<html><div class="price">€ 1.50</div><div class="price">€ 2.50</div></html>'}]
        scraper.event_id = 0
        scraper.parse_prices()
        assert type(scraper.pricelist) == list
        assert len(scraper.pricelist) == 4