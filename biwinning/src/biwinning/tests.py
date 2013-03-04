import unittest
from peewee import Model
from biwinning.models import UtilsMixIn, Club

class TestUtilsMixIn(unittest.TestCase):

    def setUp(self):
        self.model = type('TestModel', (UtilsMixIn, Model, object), {'name': 'bob'})

    def test_matches_dict(self):
        instance = self.model()
        self.assertTrue(instance.matches_dict({'name': 'bob'}), 'Dict should be equal to values.')
        self.assertFalse(instance.matches_dict({'name': 'alice'}), 'Dict should not be equal to values.')

    def test_values_from_dict(self):
        instance = self.model()
        self.assertNotEqual(instance.name, 'alice', 'Name should be bob')
        instance.values_from_dict({'name': 'alice'})
        self.assertEqual(instance.name, 'alice', 'Name should be alice')


class TestClubModel(unittest.TestCase):
    def test_create_club(self):
        club = Club(name='The club', strava_id='1')
