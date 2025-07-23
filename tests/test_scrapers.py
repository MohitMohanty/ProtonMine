import pytest
from scrapers.google_scraper import GoogleScraper
from scrapers.general_scraper import GeneralWebScraper
from database.json_db import JSONDatabase

class TestScrapers:
    def test_google_scraper_init(self):
        scraper = GoogleScraper()
        assert scraper is not None
    
    def test_trusted_domain_check(self):
        scraper = GoogleScraper()
        assert scraper.is_trusted_domain("https://reuters.com/article") == True
        assert scraper.is_trusted_domain("https://spam-site.com") == False
    
    def test_database_connection(self):
        db = JSONDatabase(use_mongodb=False)
        assert db is not None

def run_tests():
    pytest.main(['-v', 'tests/'])

if __name__ == "__main__":
    run_tests()
