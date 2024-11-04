#!/usr/bin/env python3
"""
Unit tests for open-isns, using the unittest built-in package

********
WARNING:
	 Do NOT rename and of the 'stage names' (the first argument to isns_stage())
	withing a TestCase.

	Since the 'data/*' file names are based on the stage name, so changing
        one means you have to rename the data file(s) to match.
********

TODO:
    - Add option to 'populate' the 'data/*' directory tree, instead of failing
      each time a data file is not present, as well as creating the data file,
      which seems like a questionable side-effect methodology. This way, the only
      way to populate would be to pass this option. But it would not override
      existing data files (??).
    - Change the tests so that they verify the output directly from each step,
      rather than compare the output to previous runs, which is inherently buggy,
      since we may have saved bad data as a reference. So this method only
      really catches new bugs. (Enhancement)
    - Don't start the tests if an isnsd server is already running. Perhaps we
      should care about what port it is one? But if a daemon is left running by
      a previous failed test, new tests just mysteriously fail.
    - Add option to set the "__isns_bin_dir" in harness.py
    - Add a check in each subtest to ensure the previous subtest was run, so
      that trying to run just one random subtest will fail, even though allowed
      by unittest.
    - Get security working
"""

import sys
import unittest
import harness

class Test01(unittest.TestCase):
    """
    Simple test case: ensure a single client can talk to a server,
    including registering, querying, and deregistering, with and
    without security.
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll the test client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enrolling client')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register an iniator with default port
        """
        harness.isns_stage('registration', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_query_object_eid(self):
        """
        Run a simple query
        """
        harness.isns_stage('query', 'Querying eid')
        (res, msg) = harness.isns_query_objects(self.client_config, ['eid'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test99_deregister_client(self):
        """
        Deregister client
        """
        harness.isns_stage('deregister', 'Deregister client')
        (res, msg) = harness.isns_deregister_client(self.client_config)
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test02(unittest.TestCase):
    """
    A little more complicated est case: ensure a two clients can
    talk to a server, including registering, queiying, and deregistering,
    with and without security.
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client1_config = harness.create_client(cls.server_config, '127.1.0.1')
        cls.client2_config = harness.create_client(cls.server_config, '127.1.0.2')
        harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_clients(self):
        """
        Enroll the test client
        """
        if self.security:
            harness.isns_stage('enroll1', 'Enroll client 1')
            self.assertEqual(harness.isns_enroll_client(self.client1_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.isns_stage('enroll2', 'Enroll client 2')
            self.assertEqual(harness.isns_enroll_client(self.client2_config,
                                                        ['node-type=target']), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_portals(self):
        """
        Register iniator and target portals
        """
        harness.isns_stage('registration1', 'Register client1: initiator portals')
        (res, msg) = harness.isns_register_client(self.client1_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.isns_stage('registration2', 'Register client2: target portals')
        (res, msg) = harness.isns_register_client(self.client2_config,
                                                  ['target', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_query_object_eids_before(self):
        """
        Run a simple query on each client -- clients will not see each other (yet)
        """
        harness.isns_stage('query1-1', 'Querying client1 eid')
        (res, msg) = harness.isns_query_objects(self.client1_config, ['eid'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client1_config)
        self.assertTrue(res, msg)
        harness.isns_stage('query1-2', 'Querying client2 eid')
        (res, msg) = harness.isns_query_objects(self.client2_config, ['eid'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client2_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test04_register_discovery_domain(self):
        """
        Register a discovery domain (DD) that links the two clients
        """
        harness.isns_stage('dd-registration1', 'Add Discovery Domain')
        (res, msg) = harness.isns_register_domain(self.client1_config,
                                                  ['member-name=isns.client1',
                                                   'member-name=isns.client2'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test05_query_object_eids_after(self):
        """
        Run a simple query on each client -- clients should be able to see each
        other now
        """
        harness.isns_stage('query2-1', 'Querying client1 eid')
        (res, msg) = harness.isns_query_objects(self.client1_config, ['eid'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client1_config)
        self.assertTrue(res, msg)
        harness.isns_stage('query2-2', 'Querying client2 eid')
        (res, msg) = harness.isns_query_objects(self.client2_config, ['eid'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client2_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test06_query_object_node_type(self):
        """
        Have the first initiator query for the target
        """
        harness.isns_stage('query3', 'Querying client1 iscsi-node-type')
        (res, msg) = harness.isns_query_objects(self.client1_config, ['iscsi-node-type'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client1_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test07_add_discovery_domain_member(self):
        """
        Have the first initiator query for the target
        """
        harness.isns_stage('dd-registration2', 'Add Discovery Domain Member')
        (res, msg) = harness.isns_register_domain(self.client1_config,
                                                  ['dd-id=1',
                                                   'member-name=isns.client2',
                                                   'member-name=iqn.com.foobar:disk1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test08_query_discovery_domain_membersip(self):
        """
        Get a list of the Discovery Domains (DDs) we are a member of
        """
        harness.isns_stage('query4', 'Querying client1 dd-id')
        (res, msg) = harness.isns_query_objects(self.client1_config, ['dd-id'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_query_response(self.client1_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test09_remove_discovery_domain_entries(self):
        """
        Remove some entries from the DD (and add one)
        """
        harness.isns_stage('deregister1', 'Deregister Client by member-iscs-index')
        (res, msg) = harness.isns_deregister_domain(self.client1_config,
                                                    ['1', 'member-iscsi-idx=10'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)

        harness.isns_stage('deregister2', 'Deregister Client by member-name')
        (res, msg) = harness.isns_deregister_domain(self.client1_config,
                                                    ['1',
                                                     'member-name=iqn.com.foobar:disk1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)

        harness.isns_stage('dd-registration3', 'Add Discovery Domain Member Again')
        (res, msg) = harness.isns_register_domain(self.client1_config,
                                                  ['member-name=isns.client2'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)

        harness.isns_stage('deregister3', 'Deregister Domaon')
        (res, msg) = harness.isns_deregister_domain(self.client1_config, ['1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)

        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test03(unittest.TestCase):
    """
    Validate registration and deregistration
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll our client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enroll our cilent')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register our client
        """
        harness.isns_stage('registration', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_deregister_client_portal(self):
        """
        Unregistering the portal should leave the iscsi node and
        portal group active, and move the portal to state limbo.
        """
        harness.isns_stage('deregister1', 'Deregister Client by portal')
        (res, msg) = harness.isns_deregister_client(self.client_config,
                                                    ['portal=127.0.0.1:860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test04_deregister_client_name(self):
        """
        As the iscsi node goes away, so should the whole entity
        """
        harness.isns_stage('deregister2', 'Deregister Client by member-iscs-index')
        (res, msg) = harness.isns_deregister_client(self.client_config,
                                                    ['iscsi-name=isns.client1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test04(unittest.TestCase):
    """
    Verify database remains intact across server reboots
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll our client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enroll our cilent')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register our client
        """
        harness.isns_stage('registration', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_restart_server_verify_ok(self):
        """
        Restart the server and ensure the DB is still good
        """
        harness.isns_stage('restart', 'Restart the server and ensure DB ok')
        new_pid = harness.isns_restart_server(self.server_config, self.server_pid)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        self.assertNotEqual(self.server_pid, new_pid,
                            'New PID same as old? (%d)' % new_pid)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test05(unittest.TestCase):
    """
    Test that an entity's registration expires as configured
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll our client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enroll our cilent')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register our client
        """
        harness.isns_stage('registration', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_verify_regitration_expires(self):
        """
        Ensure the registration expires as the 20 second registration period
        """
        harness.isns_stage('expired', 'Waiting for registration period to expire (25s)')
        harness.isns_idle(25)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test06(unittest.TestCase):
    """
    Validate DevAttrReg replace mode
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll our client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enroll our cilent')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register our client
        """
        harness.isns_stage('registration1', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator', 'portal'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_get_client_eid(self):
        """
        Get our eid (entity id)
        """
        harness.isns_stage('query', 'Get our Entity ID (eid)')
        (res, eid) = harness.isns_query_eid(self.client_config)
        self.assertTrue(res, 'unable to get eid for client (%d)' % res)
        self.__class__.eid = eid
        harness.vprint('*** SUCCESS ***')

    def test04_replace_initiator_portal(self):
        """
        Replace the portal with different values
        """
        harness.isns_stage('registration2-1', 'Replace initiator portal')

        # set portal to 192.168.1.1, then override with 192.168.1.2
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['--replace',
                                                   'entity=%s' % self.__class__.eid,
                                                   'initiator',
                                                   'portal=192.168.1.1:860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        harness.isns_stage('registration2-2', 'Replace initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['--replace',
                                                   'entity=%s' % self.__class__.eid,
                                                   'initiator',
                                                   'portal=192.168.1.2:860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test05_register_discovery_domain(self):
        """
        Register our DD
        """
        harness.isns_stage('dd-registration1', 'Add Discovery Domain')
        (res, msg) = harness.isns_register_domain(self.client_config,
                                                  ['member-name=isns.client1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test06_replace_initiator_portal_with_dd(self):
        """
        Replace the portal again. Now the object index of the initiator
        should not change, since it is a domain member now
        """
        harness.isns_stage('registration3', 'Replace initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['--replace',
                                                   'entity=%s' % self.__class__.eid,
                                                   'initiator',
                                                   'portal=192.168.1.1:860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test07_make_portal_dd_member(self):
        """
        Make the portal a domain member too. Now even the portal index should stay
        the same. Note that we do not replace whole entity now, but just the portal
        """
        harness.isns_stage('dd-registration2', 'Register port in Discovery Domain')
        (res, msg) = harness.isns_register_domain(self.client_config,
                                                  ['dd-id=1',
                                                   'member-addr=192.168.1.1',
                                                   'member-port=860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.isns_stage('registration4', 'Replace whole entity')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['--replace',
                                                   '--key', 'portal=192.168.1.1:860',
                                                   'portal=192.168.1.2:860'])
        self.assertTrue(res, msg)
        harness.isns_stage('registration5', 'Replace whole entity again')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['--replace',
                                                   '--key', 'portal=192.168.1.2:860',
                                                   'portal=192.168.1.1:860'])
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test08_deregister_and_reregister(self):
        """
        Deregister the whole client, and re-register. Portal and Client
        index should remain the same
        """
        harness.isns_stage('deregister', 'Deregister our client')
        (res, msg) = harness.isns_deregister_client(self.client_config,
                                                    ['eid=%s' % self.__class__.eid])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.isns_stage('registration6', 'Re-Register the client')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator',
                                                   'portal=192.168.1.1:860'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test07(unittest.TestCase):
    """
    Validate that the server discards portals that do not
    respond to ESI messages
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_enroll_client(self):
        """
        Enroll our client
        """
        if self.security:
            harness.isns_stage('enroll', 'Enroll our cilent')
            self.assertEqual(harness.isns_enroll_client(self.client_config), 0)
            (res, msg) = harness.verify_db(self.server_config)
            self.assertTrue(res, msg)
            harness.vprint('*** SUCCESS ***')
        else:
            harness.vprint('*** Skipped (no security) ***')

    def test02_register_client_initiator_portal(self):
        """
        Register a simple initiator with one portal, then wait for ESI to expire
        """
        harness.isns_stage('registration1', 'Register client initiator portal')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator',
                                                   'portal,esi-port=65535,esi-interval=5'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.isns_stage('expired1', 'Wait for ESI to expire (15s)')
        harness.isns_idle(15)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_register_client_two_portals(self):
        """
        Register a simple initiator with two portals, one with ESI and one without.
        When the ESI-monitored portal expires, this should still take down
        the whole network entity.
        """
        harness.isns_stage('registration2', 'Register client with two portals')
        (res, msg) = harness.isns_register_client(self.client_config,
                                                  ['initiator',
                                                   'portal,esi-port=65535,esi-interval=5',
                                                   'portal=127.0.0.1:1'])
        harness.isns_stage('expired2', 'Wait for ESI to expire again (15s)')
        harness.isns_idle(15)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test08(unittest.TestCase):
    """
    Validate using an external program

    Test case captured from a Wasabi Storage Builder registering itself

    For now, no security
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__, security=False)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_run_external_program_pauw1(self):
        """
        Run the first external program
        """
        harness.isns_stage('pauw1', 'Run external program pauw1')
        (res, msg) = harness.isns_external_test(self.client_config, ['pauw1'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test09(unittest.TestCase):
    """
    Validate using an external program

    Test case captured from an iscsi-target registering itself

    For now, no security
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__, security=False)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_run_external_program_pauw2(self):
        """
        Run the second external program
        """
        harness.isns_stage('pauw2', 'Run external program pauw2')
        (res, msg) = harness.isns_external_test(self.client_config, ['pauw2'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test10(unittest.TestCase):
    """
    Validate using an external program

    Test a problem reported by Albert, where re-registration shortly before
    ESI expiry fails to resurrect the registration properly

    Takes a while (20 seconds?)

    For now, no security
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__, security=False)
        cls.server_config = harness.create_server({'ESIMinInterval':'10s'})
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_run_external_program_pauw3(self):
        """
        Run the third external program
        """
        harness.isns_stage('pauw3-1', 'Run external program pauw3 (slow)')
        (res, msg) = harness.isns_external_test(self.client_config,
                                                ['pauw3', '16'])
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test02_wait_for_esi_to_expire(self):
        """
        Wait for ESI to come around
        """
        harness.isns_stage('expired1', 'Wait for ESI to expire (5s)')
        harness.isns_idle(5)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test03_run_external_program_pauw3_again(self):
        """
        Run the third external program
        """
        harness.isns_stage('pauw3-2', 'Run external program pauw3 (slow)')
        (res, msg) = harness.isns_external_test(self.client_config,
                                                ['pauw3', '-n', '16'])
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    def test04_wait_for_esi_to_expire_again(self):
        """
        Wait for ESI to come around
        """
        harness.isns_stage('expired2', 'Wait for ESI to expire (5s)')
        harness.isns_idle(5)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()


class Test11(unittest.TestCase):
    """
    Validate using an external program

    Test MS initiator registraion. The oddity about this is that the PG object
    preceeds the initiator object in the message.

    For now, no security
    """

    @classmethod
    def setUpClass(cls):
        harness.vprint('*** Starting %s' % cls.__name__)
        cls.security = harness.set_up_test(cls.__name__, security=False)
        cls.server_config = harness.create_server()
        cls.client_config = harness.create_client(cls.server_config)
        cls.server_pid = harness.isns_start_server(cls.server_config)

    def setUp(self):
        if harness.Global.debug or harness.Global.verbosity > 1:
            # this makes debug printing a little more clean
            print('', file=sys.stderr)

    def test01_run_external_program_pauw4(self):
        """
        Run the second external program
        """
        harness.isns_stage('pauw2', 'Run external program pauw4')
        (res, msg) = harness.isns_external_test(self.client_config, ['pauw4'])
        self.assertTrue(res, msg)
        (res, msg) = harness.verify_db(self.server_config)
        self.assertTrue(res, msg)
        harness.vprint('*** SUCCESS ***')

    @classmethod
    def tearDownClass(cls):
        harness.isns_finish()

# get a list of testcase classes, for listing
class_names_list=[]
for n in dir():
    if n.startswith("Test"):
        class_names_list.append(n)

def print_test_list_and_exit(verbosity):
    """
    print list of all tests

    always print the test cases, and print more if verbosity set

    verbosity       action
       0 (-1)       print list of test cases
       1 (default)  add in test case descriptions
       2 (-v)       add in Subtests and descriptions of them
    """
    global class_names_list

    for c in class_names_list:
        cls = getattr(sys.modules[__name__], c)
        print("*** Test Case: %s" % cls.__name__, end='')
        if verbosity > 0:
            print(cls.__doc__)
            if verbosity > 1:
                for m in dir(cls):
                    if m.startswith("test"):
                        method_doc = getattr(cls, m).__doc__
                        print("\t* Test Method: %s: %s" % (m, method_doc.strip()))
                print()
        else:
            print()
    sys.exit(0)

class MyTestProgram(unittest.TestProgram):
    """
    Augment TestProgram by adding a new method, which prints test case info
    """
    def list_tests(self):
        print_test_list_and_exit(harness.Global.verbosity)

if __name__ == '__main__':
    # do our own hackery first, to get access to verbosity, security, etc,
    # as well as add our own command-line options
    harness.setup_testProgram_overrides()
    # this next step parses args, gathers the tests, runs the tests, and displays
    # the results
    MyTestProgram()
