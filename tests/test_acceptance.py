import sys
import os
import mock

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import fake_filesystem_unittest

from os.path import expanduser
from mock import MagicMock
from tests.helper import saml_assertion, read_config_file, Struct
from aws_role_credentials import cli
from StringIO import StringIO

def load_tests(loader, tests, ignore):
    return fake_filesystem_unittest.load_doctests(loader, tests, ignore, example)

class TestAcceptance(fake_filesystem_unittest.TestCase):
    AWS_HOME = expanduser('~/.aws')
    TEST_FILE=expanduser('~/.aws/credentials')

    def setUp(self):
        self.patcher = mock.patch('aws_role_credentials.cli.configurelogging')
        self.patcher.start()

        self.setUpPyfakefs()
        if not os.path.exists(self.AWS_HOME):
            os.makedirs(self.AWS_HOME)

    def tearDown(self):
        self.patcher.stop()
        pass

    @mock.patch('aws_role_credentials.actions.boto.sts')
    def test_credentials_are_generated_from_saml(self, mock_sts):
        mock_conn = MagicMock()
        mock_conn.assume_role_with_saml.return_value = Struct({'credentials':
                                                               Struct({'access_key': 'SAML_ACCESS_KEY',
                                                                       'secret_key': 'SAML_SECRET_KEY',
                                                                       'session_token': 'SAML_TOKEN'})})
        mock_sts.connect_to_region.return_value = mock_conn

        sys.stdin = StringIO(saml_assertion(['arn:aws:iam::1111:role/DevRole,arn:aws:iam::1111:saml-provider/IDP']))
        cli.main(['test.py', 'saml',
                  '--profile', 'test-profile',
                  '--region', 'un-south-1'])

        self.assertEqual(read_config_file(self.TEST_FILE),
                         ['[test-profile]',
                          'output = json',
                          'region = un-south-1',
                          'aws_access_key_id = SAML_ACCESS_KEY',
                          'aws_secret_access_key = SAML_SECRET_KEY',
                          'aws_session_token = SAML_TOKEN',
                          ''])

    @mock.patch('aws_role_credentials.actions.boto.sts')
    def test_credentials_are_generated_from_user(self, mock_sts):
        mock_conn = MagicMock()
        mock_conn.assume_role.return_value = Struct({'credentials':
                                                     Struct({'access_key': 'SAML_ACCESS_KEY',
                                                             'secret_key': 'SAML_SECRET_KEY',
                                                             'session_token': 'SAML_TOKEN'})})
        mock_sts.connect_to_region.return_value = mock_conn

        arn = 'arn:role/developer'
        session_name = 'dev-session'

        cli.main(['test.py', 'user', arn, session_name,
                  '--profile', 'test-profile',
                  '--region', 'un-south-1'])

        self.assertEqual(read_config_file(self.TEST_FILE),
                         ['[test-profile]',
                          'output = json',
                          'region = un-south-1',
                          'aws_access_key_id = SAML_ACCESS_KEY',
                          'aws_secret_access_key = SAML_SECRET_KEY',
                          'aws_session_token = SAML_TOKEN',
                          ''])

    @mock.patch('aws_role_credentials.actions.Popen')
    @mock.patch('aws_role_credentials.actions.boto.sts')
    def test_credentials_exec_command(self, mock_sts, mock_popen):
        mock_conn = MagicMock()
        mock_conn.assume_role.return_value = Struct({'credentials':
                                                     Struct({'access_key': 'SAML_ACCESS_KEY',
                                                             'secret_key': 'SAML_SECRET_KEY',
                                                             'session_token': 'SAML_TOKEN'})})

        cli.main(['test.py', 'user', 'arn:role/developer',
                  'dev-session',
                  '--exec', 'echo hello'])

        args, kwargs = mock_popen.call_args

        self.assertTrue(['echo', 'hello'] in args)
