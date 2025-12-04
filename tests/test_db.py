from scripts.db import latest_event_id

def test_latest_event_id_none(mock_cursor):
    mock_cursor.fetchone.return_value = [None]
    assert latest_event_id(mock_cursor) == 1

def test_latest_event_id_increment(mock_cursor):
    mock_cursor.fetchone.return_value = [10]
    assert latest_event_id(mock_cursor) == 11

from scripts.db import update_fact_data

def test_update_fact_data(mock_connection, mock_cursor):
    """Test that executes and commits update_fact_data SQL."""
    
    pricelist = [(1, 123, "2024-01-01", "diesel", 1.50)]

    update_fact_data(mock_connection, mock_cursor, pricelist)

    mock_cursor.execute.assert_called()
    mock_connection.commit.assert_called()