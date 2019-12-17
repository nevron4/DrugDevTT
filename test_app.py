import unittest
import json
import app

BASE_URL = 'http://127.0.0.1:5000/contact'
BAD_ITEM_URL = '{}/test_username55'.format(BASE_URL)
GOOD_ITEM_URL = '{}/username1'.format(BASE_URL)


class TestFlaskApi(unittest.TestCase):

    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True
        setup_contact = {
          "addresses": ["first_name1@test.com", "last_name1@test.net"],
          "first_name": "first_name1",
          "last_name": "last_name1",
          "username": "username1"
        }
        self.app.post(BASE_URL,
                         data=json.dumps(setup_contact),
                         content_type='application/json')

    def test_add_contact(self):
        # missing value field = bad
        contact = {"username": "test_username1"}
        response = self.app.post(BASE_URL,
                                 data=json.dumps(contact),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 500)
        # addresses not valid email
        contact = {
          "addresses":  "test1test.com",
          "first_name": "test_first_name1",
          "last_name": "test_last_name1",
          "username": "test_username1"
        }
        response = self.app.post(BASE_URL,
                                 data=json.dumps(contact),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 404)
        # valid
        contact = {
          "addresses": ["test1@test.com", "test1@test.net"],
          "first_name": "test_first_name1",
          "last_name": "test_last_name1",
          "username": "test_username1"
        }
        response = self.app.post(BASE_URL,
                                 data=json.dumps(contact),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data())
        self.assertEqual(data['username'], 'test_username1')
        # cannot add contact with same username again
        contact = {
          "addresses": ["test2@test.com", "test2@test.net"],
          "first_name": "test_first_name2",
          "last_name": "test_last_name2",
          "username": "test_username1"
        }
        response = self.app.post(BASE_URL,
                                 data=json.dumps(contact),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 500)

    def test_list_user_emails(self):
        self.assertEqual(app.list_user_emails('username1'), ["first_name1@test.com", "last_name1@test.net"])

    def test_get_contacts(self):
        response = self.app.get(BASE_URL)
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        #self.assertEqual(len(data), 1)

    def test_get_contact(self):
        response = self.app.get(GOOD_ITEM_URL)
        data = json.loads(response.get_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['first_name'], 'first_name1')

    def test_update_contact(self):
        contact = {
            "addresses": ["first_name1@test.com", "last_name1@test.net"],
            "first_name": "first_name2",
            "last_name": "last_name2",
            "username": "username1"
        }
        response = self.app.put(GOOD_ITEM_URL,
                                data=json.dumps(contact),
                                content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data())
        self.assertEqual(data['first_name'], 'first_name2')

    def test_delete_contact(self):
        response = self.app.delete('http://127.0.0.1:5000/contact/test_username1')
        self.assertEqual(response.status_code, 200)
        response = self.app.delete(BAD_ITEM_URL)
        self.assertEqual(response.status_code, 404)


    def test_send_email(self):
        # missing value field = bad
        email = {"to_email": "first_name1@test.com"}
        response = self.app.post('http://127.0.0.1:5000/contact/test_username1/email',
                                 data=json.dumps(email),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 500)
        # addresses not valid email
        email = {
          "to_email":  "test1test.com",
          "subject": "Test subject",
          "text": "Test text",
        }
        response = self.app.post('http://127.0.0.1:5000/contact/test_username1/email',
                                 data=json.dumps(email),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 500)
        # valid
        email = {
            "to_email": "test1@test.com",
            "subject": "Test subject",
            "text": "Test text"
        }
        response = self.app.post('http://127.0.0.1:5000/contact/username1/email',
                                 data=json.dumps(email),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data())
        self.assertEqual(data['text'], 'Test text')


    def tearDown(self):
        # reset app.items to initial state
        response = self.app.delete(GOOD_ITEM_URL)


if __name__ == "__main__":
    unittest.main()