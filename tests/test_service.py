import unittest
import json
import logging
from flask_api import status    # HTTP Status Codes

from models import Recommendation
import service

######################################################################
#  T E S T   C A S E S
######################################################################

# Product_id
PS4 = 1
CONTROLLER = 2

class TestRecommendationservice(unittest.TestCase):
    """ Recommendation Service Tests """

    @classmethod
    def setUpClass(cls):
        """ Run once before all tests """
        service.app.debug = False
        service.initialize_logging(logging.INFO)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        """ Runs before each test """
        service.Recommendation.remove_all()
        self.app = service.app.test_client()

    def tearDown(self):
        service.Recommendation.remove_all()

    def test_get_recommendation(self):
        ps4 = Recommendation(id=0, product_id=PS4, recommended_product_id=CONTROLLER, recommendation_type="accessory")
        ps4.save()

        """ Read a single Recommendation """
        resp = self.app.get('/recommendations/1')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['product_id'], PS4)
        self.assertEqual(data['recommended_product_id'], CONTROLLER)
        self.assertEqual(data['recommendation_type'], "accessory")
        self.assertEqual(data['likes'], 0)

    def test_get_recommendation_not_found(self):
        """ Read a Recommendation thats not found """
        resp = self.app.get('/recommendations/11')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_recommendation(self):
        """Create a recommendation"""
        # save the current number of recommendations for later comparison
        recommendation_count = self.get_recommendation_count()
        # add a new recommendation
        new_recommendation = {'id': 0, 'product_id': 6, 'recommended_product_id': 7, 'recommendation_type': "up-sell", 'likes': 10}
        data = json.dumps(new_recommendation)
        resp = self.app.post('/recommendations', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get('Location', None)
        self.assertTrue(location != None)
        # Check the data is correct
        new_json = json.loads(resp.data)
        self.assertEqual(new_json['product_id'], 6)
        # check that count has gone up and includes 4
        resp = self.app.get('/recommendations')
        # print 'rest_data(2): ' + resp.rest_data
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), recommendation_count + 1)
        self.assertIn(new_json, data)

    def test_delete_recommendation(self):
        """Deletes a recommendation"""
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        service.Recommendation(0, 2, 3, "accessory", 2).save()

        # save the current number of recommendation for later comparison
        recommendation_count = self.get_recommendation_count()
        self.assertEqual(recommendation_count, 2)

        # delete a recommendation
        resp = self.app.delete('/recommendations/1', content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        new_count = self.get_recommendation_count()
        self.assertEqual(new_count, recommendation_count - 1)

    def test_update_recommendation(self):
        """ Update a Recommendation """
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        new_recommendation = {'id': 0,'product_id': 2, 'recommended_product_id': 8, 'recommendation_type': "up-sell", 'likes': 1}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        resp = self.app.get('/recommendations')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_json = json.loads(resp.data)
        self.assertEqual(new_json[0]['recommended_product_id'], 8)

    def test_update_recommendation_with_no_product_id(self):
        """ Update a Recommendation with no product_id"""
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        new_recommendation = {'id': 0, 'recommended_product_id': 8, 'recommendation_type': "up-sell", 'likes': 1}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recommendation_with_no_recommended_product_id(self):
        """ Update a Recommendation with no recommended_product_id"""
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        new_recommendation = {'id': 0, 'product_id': 2, 'recommendation_type': "up-sell", 'likes': 1}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recommendation_with_no_recommendedation_type(self):
        """ Update a Recommendation with no recommendation_type"""
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        new_recommendation = {'id': 0, 'product_id': 2, 'recommended_product_id': 8,'likes': 1}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recommendation_with_no_likes_field(self):
        """ Update a Recommendation with no likes field added"""
        service.Recommendation(0, 2, 4, "up-sell", 1).save()
        new_recommendation = {'id': 0, 'product_id': 2, 'recommended_product_id': 8, 'recommended_type': "up-sell"}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/1', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_recommendation_not_found(self):
        """ Update a recommendation that can't be found """
        new_recommendation = {'id': 0, 'product_id': 2, 'recommended_product_id': 8, 'recommendation_type': "up-sell", 'likes': 1}
        data = json.dumps(new_recommendation)
        resp = self.app.put('/recommendations/0', data=data, content_type='application/json')
        self.assertEquals(resp.status_code, status.HTTP_404_NOT_FOUND)

######################################################################
# Utility functions
######################################################################

    def get_recommendation_count(self):
        """ save the current number of recommendations """
        resp = self.app.get('/recommendations')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = json.loads(resp.data)
        return len(data)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()