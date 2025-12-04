from unittest.mock import patch, MagicMock
import main

@patch("main.scraper")
@patch("main.db")
def test_main(mock_db, mock_scraper):
    mock_scraper.download_html.return_value = MagicMock()
    mock_scraper.parse_html_stations.return_value = {"places": []}
    mock_scraper.retrieve_ids_and_links.return_value = {}
    mock_scraper.retrieve_individual_prices.return_value = []

    mock_db.create_connection.return_value = (MagicMock(), MagicMock())
    mock_db.latest_event_id.return_value = 1

    main.main()

    mock_scraper.download_html.assert_called_once()
    mock_db.create_connection.assert_called_once()