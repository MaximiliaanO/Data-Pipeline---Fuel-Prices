from unittest.mock import patch, MagicMock
from scripts.scraper import download_html

@patch("scripts.scraper.requests.get")
def test_download_html_success(mock_get):
    """Test dat download_html een response object teruggeeft wanneer de request slaagt."""
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = download_html()

    assert result == mock_response
    mock_get.assert_called_once()

from scripts.scraper import parse_html_stations

def test_parse_html_stations_extracts_json():
    """Test dat parse_html_stations correct JSON uit een script tag haalt."""

    class FakeResponse:
        text = """
        <script>
        var placesInitialData = {"places":[{"id":10,"guid":"abc"}]};
        </script>
        """

    result = parse_html_stations(FakeResponse())

    assert "places" in result
    assert result["places"][0]["id"] == 10

from scripts.scraper import retrieve_ids_and_links

def test_retrieve_ids_and_links():
    """Test dat ID en link goed worden omgezet naar dictionary."""
    
    test_json = {
        "places": [
            {"id": 1, "guid": "link1"},
            {"id": 2, "guid": "link2"}
        ]
    }

    result = retrieve_ids_and_links(test_json)

    assert result == {1: "link1", 2: "link2"}

from unittest.mock import patch, MagicMock
from scripts.scraper import retrieve_individual_prices

@patch("scripts.scraper.download_html")
@patch("scripts.scraper.bs4.BeautifulSoup")
@patch("scripts.scraper.time.sleep", return_value=None)
def test_retrieve_individual_prices(mock_sleep, mock_soup, mock_download):
    """Test dat prijzen correct worden verzameld."""

    mock_html = MagicMock()
    mock_download.return_value = mock_html

    mock_elem1 = MagicMock()
    mock_elem1.getText.return_value = "€1.233"

    mock_elem2 = MagicMock()
    mock_elem2.getText.return_value = "€1.455"

    mock_soup.return_value.select.return_value = [mock_elem1, mock_elem2]

    links = {123: "fakeurl"}
    event_id = 1

    result = retrieve_individual_prices(links, event_id)

    assert len(result) == 2
    assert result[0][3] == "benzine"
    assert result[1][3] == "diesel"

