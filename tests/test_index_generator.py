import pytest
from application.listener import app, get_iopn_records, NamesError, listen
from unittest import mock
import os
import json
from tests.fake_kombu import FakeConnection, FakeExchange, FakeConsumer, FakeQueue, FakeFailingConnection


class FakeResponse(object):
    def __init__(self, content=None, status_code=200):
        super(FakeResponse, self).__init__()
        self.data = content
        self.status_code = status_code


directory = os.path.dirname(__file__)
single_PI_proprietor = json.loads(open(os.path.join(directory, 'data/single_PI_proprietor.json'), 'r').read())


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def mock_kombu(function):
        @mock.patch('kombu.Connection', return_value=FakeConnection())
        @mock.patch('kombu.common.maybe_declare')
        @mock.patch('kombu.Exchange', return_value=FakeExchange())
        @mock.patch('kombu.Consumer', return_value=FakeConsumer())
        def wrapped(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
            return function(self, mock_consumer, mock_exchange, mock_declare, mock_connection)
        return wrapped

    @mock_kombu
    def test_health_check(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=201))
    def test_simple_proprietor_conversion(self, mock_post, mock_consumer, mock_exchange, mock_declare, mock_connection):
        output = get_iopn_records(single_PI_proprietor)
        assert len(output) == 1
        assert output[0]['title_number'] == 'LK31302'
        assert output[0]['registered_proprietor'] == 'Murl Lenora Ullrich'
        assert output[0]['office'] == 'Peytonland Office'
        assert output[0]['sub_register'] == 'Proprietorship'
        assert output[0]['name_type'] == 'Standard'

    @mock_kombu
    @mock.patch('requests.post', return_value=FakeResponse(status_code=500))
    def test_simple_proprietor_conversion_insert_failed(self, mock_post, mock_consumer, mock_exchange, mock_declare, mock_connection):
        with pytest.raises(NamesError) as excinfo:
            get_iopn_records(single_PI_proprietor)
        print(excinfo.value.value)
        assert excinfo.value.value == "Search API non-201 response: 500"

    @mock_kombu
    def test_exception_handled(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        queue = FakeQueue()
        listen(FakeFailingConnection(), queue, False)
        assert queue.data['exception_class'] == "NamesError"
