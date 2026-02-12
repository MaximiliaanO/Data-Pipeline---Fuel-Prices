from scripts.db import DbHandler

class TestDbHandler:
    def test_transform_postcode(self):
        db = DbHandler()
        clean = db.transform_postcode(1, '1234&nbsp;AB')
        assert clean == '1234AB'
        clean_2 = db.transform_postcode(1, '1234&nbsp;AB&nbsp;')
        assert clean_2 == '1234AB'
        clean_3 = db.transform_postcode(1, '1234')
        assert clean_3 == '1234'