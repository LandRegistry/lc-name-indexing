from application.listener import app, get_iopn_records
from unittest import mock
import os
import json
from tests.fake_kombu import FakeConnection, FakeExchange, FakeConsumer


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

    # @mock.patch('kombu.Connection', return_value=FakeConnection())
    # @mock.patch('kombu.common.maybe_declare')
    # @mock.patch('kombu.Exchange', return_value=FakeExchange())
    # @mock.patch('kombu.Consumer', return_value=FakeConsumer())
    @mock_kombu
    def test_health_check(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock_kombu
    def test_simple_proprietor_conversion(self, mock_consumer, mock_exchange, mock_declare, mock_connection):
        output = get_iopn_records(single_PI_proprietor)
        assert len(output) == 1
        assert output[0]['title_number'] == 'LK31302'
        assert output[0]['registered_proprietor'] == 'Murl Lenora Ullrich'
        assert output[0]['office'] == 'Peytonland Office'
        assert output[0]['sub_register'] == 'Proprietorship'
        assert output[0]['name_type'] == 'Standard'

