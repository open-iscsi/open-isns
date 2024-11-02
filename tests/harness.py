"""
harness stuff (support)
"""

import os
import shutil
import sys
import unittest
import re
import time

#
# globals
#
class Global:
    # tmp directories where the tests will be run
    _isns_test_base_path = '/tmp/isns-test'
    _isns_test_path = '/tmp/isns-test/test'
    # various attributes
    _isns_test_dump = None
    _isns_test_data = None
    _isns_seq = 0
    _isns_servers = []
    _isns_server_config_data = {}
    _isns_stage_name = None
    _isns_stage_names = []

    _isns_ignore_tags = ['0004', '0603v']

    # where the tests are relative to where we start them from
    # default to "current directory"
    test_dir = '.'
    # for locating binaries under test_dir (FIXME: should be a command-line option?)
    isns_bin_dir = '../builddir'

    verbosity = 1
    security = False
    debug = False

def dprint(*args):
    """
    Print a debug message if in debug mode
    """
    if Global.debug:
        print('DEBUG: ', file=sys.stderr, end='')
        for arg in args:
            print(arg, file=sys.stderr, end='')
        print('', file=sys.stderr)

def vprint(*args):
    """
    Print a verbose message
    """
    if Global.verbosity > 0 and args:
        for arg in args:
            print(arg, end='')
        print('')

def get_bindir():
    """
    return the directory where binaries live
    """
    return '%s/%s' % (Global.test_dir, Global.isns_bin_dir)

def isns_stage(name, msg):
    """
    gaurd against duplicate stage names, since data files are named, based on them
    """
    if name in Global._isns_stage_names:
        print('internal error: duplicate stage name: %s\n' % name, file=sys.stderr)
        sys.exit(1)
    Global._isns_stage_name = name
    Global._isns_stage_names.append(name)
    vprint('*** Stage %s: %s ***' % (name, msg))

def set_up_test(test_name, security=None):
    Global._isns_test_path = '%s/%s' % (Global._isns_test_base_path, test_name)
    Global._isns_test_dump = '%s/dump' % Global._isns_test_path
    Global._isns_test_data = '%s/data/%s' % (Global.test_dir, test_name)

    if Global._isns_test_path.startswith('/tmp/'):
        if os.path.isdir(Global._isns_test_path):
            shutil.rmtree(Global._isns_test_path)

    if not os.path.isdir(Global._isns_test_path):
        os.makedirs(Global._isns_test_path, 0o755)
    if not os.path.isdir(Global._isns_test_dump):
        os.mkdir(Global._isns_test_dump, 0o755)

    if security is not None:
        dprint("Setting security=", security)
        Global.security = security

    # start clean
    Global._isns_seq = 0
    Global._isns_stage_name = None
    Global._isns_stage_names = []

    return Global.security

def run_cmd(cmd, output_save_file=None):
    """
    run specified command, waiting for and returning result
    """
    if Global.verbosity > 1:
        cmd_str = ' '.join(cmd)
        if output_save_file:
            cmd_str += ' >& %s' % output_save_file
        vprint(cmd_str)
    pid = os.fork()
    if pid < 0:
        print("Error: cannot fork!", flie=sys.stderr)
        sys.exit(1)
    if pid == 0:
        # the child
        if output_save_file:
            stdout_fileno = sys.stdout.fileno()
            stderr_fileno = sys.stderr.fileno()
            new_stdout = os.open(output_save_file, os.O_WRONLY|os.O_CREAT|os.O_TRUNC,
                                 mode=0o664)
            os.dup2(new_stdout, stdout_fileno)
            os.dup2(new_stdout, stderr_fileno)
        os.execvp(cmd[0], cmd)
        # not reached

    # the parent
    wpid, wstat = os.waitpid(pid, 0)
    if wstat != 0:
        dprint("exit status: (%d) %d" % (wstat, os.WEXITSTATUS(wstat)))
    return os.WEXITSTATUS(wstat)

def new_initArgParsers(self):
    """
    Add  some options to the normal unittest main options
    """
    global old_initArgParsers

    old_initArgParsers(self)
    self._main_parser.add_argument('-s', '--secure', dest='security',
            action='store_true',
            help='Enable security')
    self._main_parser.add_argument('-d', '--debug', dest='debug',
            action='store_true',
            help='Enable developer debugging')
    self._main_parser.add_argument('-l', '--list', dest='list',
            action='store_true',
            help='List tests and exit')
    self._main_parser.add_argument('-D', '--test-dir', dest='test_dir',
            default='.',
            help='Sets the test dir (default ".")')

def new_parseArgs(self, argv):
    """
    Gather globals from unittest main for local consumption
    """
    global old_parseArgs

    old_parseArgs(self, argv)
    Global.verbosity = self.verbosity
    Global.security = self.security
    Global.debug = self.debug
    Global.test_dir = self.test_dir
    dprint("found: debug=%s, verbosity=%d, security=%s, list=%s, test_dir='%s'" % \
           (Global.debug, Global.verbosity,
            Global.security, self.list, self.test_dir))
    if self.list:
        self.list_tests()

def setup_testProgram_overrides():
    """
    Add in special handling for a couple of the methods in TestProgram (main)
    so that we can add parameters and detect some globals we care about
    """
    global old_parseArgs, old_initArgParsers

    old_initArgParsers = unittest.TestProgram._initArgParsers
    unittest.TestProgram._initArgParsers = new_initArgParsers
    old_parseArgs = unittest.TestProgram.parseArgs
    unittest.TestProgram.parseArgs = new_parseArgs

def create_key(keyfile):
    """
    create a key file for security, if enabled
    """
    if Global.security:
        vprint('*** Creating key at %s' % keyfile)
        res = run_cmd(['./genkey', '-fsk', keyfile, '2048'], '%s.log' % keyfile)
        if res != 0:
            print('internal error: cannot general key (%d)' % res)
            sys.exit(1)
    return keyfile

class isns_config(object):
    name = ''
    def __init__(self, path):
        self.path = path
        self.dict = dict()

def build_config(from_config, to_config, local_config):
    """
    build a config file from the from_config, using local_config,
    and creating to_config
    """
    from_config_path = '%s/%s' % (Global.test_dir, from_config)
    vprint('*** Building %s -> %s' % (from_config_path, to_config))
    pat = re.compile(r'(\S+)(\s*=\s*)(\S+)')
    skip_pat = re.compile(r'@[A-Z_]*@')
    result = isns_config(to_config)
    with open(from_config_path, 'r') as from_fd:
        with open(to_config, 'a') as to_fd:
            for line in from_fd:
                res = pat.match(line.rstrip())
                if not res:
                    continue
                key_val = res.group(1)
                middle = res.group(2)
                val = res.group(3)
                if key_val in local_config:
                    val = local_config[key_val]
                    line = '%s%s%s\n' % (key_val, middle, val)
                elif skip_pat.search(line):
                    #dprint("Skipping unconfigured line!")
                    continue
                result.dict[key_val] = val
                to_fd.write(line)
    return result
        
def create_server(overrides=None):
    """
    Create a server configration instance
    """
    dprint("create_server: PWD=%s" % os.getcwd())
    handle = 'server%d' % Global._isns_seq
    Global._isns_seq += 1
    my_dir = '%s/%s' % (Global._isns_test_path, handle)
    if not os.path.isdir(my_dir):
        os.mkdir(my_dir, 0o755)
    if not os.path.isdir(Global._isns_test_dump):
        dprint("making dir %s for the server ???" % Global._isns_test_dump)
        os.mkdir(Global._isns_test_dump, 0o755)

    server_addr = '127.0.0.1:7770'

    server_config = '%s/config' % my_dir

    local_config = dict()
    local_config['SourceName'] = 'isns.%s' % handle
    local_config['Database'] = '%s/database' % my_dir
    local_config['BindAddress'] = server_addr
    local_config['PIDFile'] = '%s/pid' % my_dir
    local_config['ControlSocket'] = '%s/control' % my_dir
    local_config['Security'] = 1 if Global.security else 0
    local_config['AuthKeyFile'] = create_key('%s/auth_key' % my_dir)

    if overrides:
        dprint("overrides:", overrides)
        for key in overrides:
            value = overrides[key]
            dprint("overriding config[%s] with %s" % \
                   (key, value))
            local_config[key] = value

    return build_config('server.conf', server_config, local_config)

def create_client(server_config, client_address=None):
    """
    create a client, given a server config file
    """
    handle = 'client%d' % Global._isns_seq
    Global._isns_seq += 1
    my_dir = '%s/%s' % (Global._isns_test_path, handle)
    if not os.path.isdir(my_dir):
        os.mkdir(my_dir, 0o755)

    control_socket = server_config.dict['ControlSocket']

    if 'BindAddress' in server_config.dict:
        server_addr = server_config.dict['BindAddress']
    else:
        server_addr = '127.0.0.1:7770'

    client_config_path = '%s/config' % my_dir

    local_config = dict()
    local_config['SourceName'] = 'isns.%s' % handle
    local_config['AuthName'] = '%s.isns-test.eu' % handle
    local_config['ServerAddress'] = server_addr
    local_config['ControlSocket'] = control_socket
    if client_address:
        local_config['BindAddress'] = client_address
    local_config['server_config'] = server_config.path
    local_config['Security'] = 1 if Global.security else 0
    local_config['AuthKeyFile'] = create_key('%s/auth_key' % my_dir)
    local_config['ServerKeyFile'] = \
                   '%s.pub' % server_config.dict['AuthKeyFile']

    client_config = build_config('client.conf', client_config_path, local_config)

    Global._isns_server_config_data[client_config_path] = server_config.path

    return client_config

def get_logfile_from_config(config):
    return '%s/logfile' % os.path.dirname(config)

def isns_start_server(server_config):
    """
    start the isnsd server
    """
    if not os.path.isfile(server_config.path):
        print("internal error: no config file: %s" % server_config.path,
              file=sys.stderr)
        sys.exit(1)

    logfile = get_logfile_from_config(server_config.path)
    pidfile = server_config.dict['PIDFile']

    vprint('*** Starting server (logging to %s)' % logfile)

    cmd = ['%s/isnsd' % get_bindir(),
           '-c', server_config.path,
           '-f',
           '-d', 'all' ]
    if Global.verbosity > 0:
        cmd_str = '%s >& %s' % (' '.join(cmd), logfile)
        vprint(cmd_str)

    pid = os.fork()
    if pid < 0:
        print("internal error: cannot fork!", file=sys.stderr)
        sys.exit(1)

    if pid == 0:
        # the child -- run 'cmd 2>&1'
        stdout_fileno = sys.stdout.fileno()
        stderr_fileno = sys.stderr.fileno()
        new_stdout = os.open(logfile, os.O_WRONLY|os.O_CREAT|os.O_TRUNC,
                             mode=0o664)
        os.dup2(new_stdout, stdout_fileno)
        os.dup2(new_stdout, stderr_fileno)
        os.execvp(cmd[0], cmd)
        # not reached

    # the parent -- get child PID from file to be sure its ready
    dprint("parent: waiting for child PIDFile=%s (pid=%d)" % \
           (pidfile, pid))

    # wait for the PID file to appear for a bit, then get PID from it
    for retry in range(15):
        if os.path.isfile(pidfile):
            break
        time.sleep(1)
    if not os.path.isfile(pidfile):
        print("internal error: no pid file: %s" % pidfile, file=sys.stderr)
        sys.exit(1)
    with open(pidfile, 'r') as pid_fd:
        pid_from_file = int(pid_fd.readline().strip())
    vprint('*** Started server (pid=%d) ***' % pid_from_file)
    if pid_from_file in Global._isns_servers:
        print('internal error: duplicate server PID?', file=sys.stderr)
        sys.exit(1)
    Global._isns_servers.append(pid_from_file)
    return pid_from_file

def isns_stop_server(server_pid):
    """
    stop a single server with supplied PID, and remove said PID from server list
    """
    dprint('Killing isnsd server pid=%d' % server_pid)
    try:
        os.kill(server_pid, 15)
    except ProcessLookupError:
        print('warning: cannot send signal to server pid=%d: no such process' % \
              server_pid)
    if server_pid in Global._isns_servers:
        Global._isns_servers.remove(server_pid)

def isns_idle(sleep_amt):
    if Global.verbosity > 1:
        print('Snooze', end='')
        sys.stdout.flush()
    for secs in range(sleep_amt):
        if Global.verbosity > 1:
            print('.', end='')
            sys.stdout.flush()
        time.sleep(1)
    if Global.verbosity > 1:
        print('')
        
def isns_restart_server(server_config, server_pid):
    isns_stop_server(server_pid)
    vprint('*** Waiting for server to finish (5s)')
    isns_idle(5)
    return isns_start_server(server_config)

def isns_enroll_client(client_config, extra_args=None):
    """
    enroll client -- called for security mode
    """
    server = Global._isns_server_config_data[client_config.path]

    source_name = client_config.dict['SourceName']
    auth_name = client_config.dict.get('AuthName')
    auth_key = client_config.dict.get('AuthKeyFile')

    args = ['--local',
            '--enroll', auth_name,
            'node-name=%s' % source_name]
    if auth_key:
        args.append('key=%s.pub' % auth_key)
    if extra_args:
        args += extra_args

    (log_file, client_exit_value) = run_client(client_config, args)

    return client_exit_value

def run_client(client_config, args):
    """
    run a client instance -- arguments required
    """
    logfile = get_logfile_from_config(client_config.path)

    cmd = ['%s/isnsadm' % get_bindir(),
           '-c', client_config.path] + args
    exit_val = run_cmd(cmd, logfile)
    return (logfile, exit_val)

def isns_external_test(client_config, args):
    """
    Run an external test program
    """
    logfile = get_logfile_from_config(client_config.path)

    cmd = ['%s/%s' % (get_bindir(), args[0]),
           '-c', client_config.path] + args[1:]
    exit_val = run_cmd(cmd, logfile)
    return (logfile, exit_val)

def copy_file(from_file, to_file):
    dprint("Copying '%s' => '%s'" % (from_file, to_file))
    with open(from_file, 'r') as from_fd:
        with open(to_file, 'w') as to_fd:
            for line in from_fd:
                to_fd.write(line)

def skip_header(lines):
    #dprint("skip_header: first line: /%s/" % lines[0].rstrip())
    while lines:
        line = lines.pop(0)
        if line.startswith('-'):
            break
    #dprint("skip_header: now first line: /%s/" % lines[0].rstrip())

def get_next_db_object(lines):
    """
    From the input array of lines, return the glob of lines that make
    the next 'object'
    """
    tag_pat = re.compile('\s+([0-9a-fv]+)\s+')
    tags = []
    result = []
    while True:
        if not lines:
            break
        line = lines.pop(0)
        if line.startswith('-'):
            continue
        #dprint("looking at line: /%s/" % line)
        res = tag_pat.match(line)
        if res:
            if res.group(1) in Global._isns_ignore_tags:
                dprint("get_next_db_object: ignoring tag %s" % res.group(1))
                continue
            tags.append(line)
        else:
            if result:
                # we already have a result -- put this one back
                lines.insert(0, line)
                #dprint("break-ing -- we went to far!")
                break
            result.append(line)

    if tags:
        result += tags

    return result

def compare_db_objects(obj1, obj2):
    dprint("compare_db_objects")
    if obj1.size() != obj2.size():
        return False
    for i in range(obj1.size()):
        if obj1[i] != obj2[i]:
            return False
    return True

def load_dump(fname):
    lines = []
    dprint("load_dump(%s): entering" % fname)
    with open(fname) as fd:
        for line in fd:
            lines.append(line.rstrip())
    return lines

def verify_db_dump_file(data_file, dump_file):
    """
    Verify that the data (source) file and the
    dump (for comparison) files have the same 'objects'
    """
    dprint("verify_db_dump_file(%s, %s): entering" % (data_file, dump_file))

    data_lines = load_dump(data_file)
    dump_lines = load_dump(dump_file)

    skip_header(data_lines)
    skip_header(dump_lines)

    # I think this "line number" stuff is bogus, as it doesn't reflect any
    # actual line numbers
    line_no = 0

    while True:
            line_no += 1

            dump_obj = get_next_db_object(dump_lines)
            data_obj = get_next_db_object(data_lines)

            if not dump_obj and not data_obj:
                # both lists are empty -- done
                break

            if not dump_obj or not data_obj:
                vprint('*** %s: Excess data at end of dump or data' % \
                       Global._isns_stage_name)
                return (False, 'excess data in dump')

            #if not compare_db_objects(dump_obj, data_obj)

            if dump_obj != data_obj:
                vprint('*** Object mismatch (object %d)' % line_no)
                vprint('Expected:')
                vprint('%s' % '\n'.join(data_obj))
                vprint('Got:')
                vprint('%s' % '\n'.join(dump_obj))
                return (False, "Compare DB objects failed: Object at line %d" % line_no)

    if dump_lines:
        return (False, 'unexpected end of dump at line %d' % lin_no)

    return (True, '')

def verify_db(server_config):
    """
    Set pu to verify a database dump, then do the comparison
    """
    if not Global._isns_test_data:
        print("internal error: Test Case forgot to call set_up_test",
              file=sys.stderr)
        sys.exit(1)
    stage = Global._isns_stage_name
    dump_file = '%s/%s' % (Global._isns_test_dump, stage)

    dprint("planning to dump DB to %s" % dump_file)
    cmd = ['%s/isnsd' % get_bindir(),
           '-c', server_config.path,
           '--dump-db']
    cmd_result = run_cmd(cmd, dump_file)
    if cmd_result != 0:
        return (False, 'Could not dump DB (%d)' % cmd_result)

    data_dir = Global._isns_test_data
    data_file = '%s/%s' % (data_dir, stage)
    if not Global.security:
        data_file += '-no-security'

    # see if the reference data file exists. If it doesn't, this means
    # we are priming the test case, i.e. generating the data for the
    # first time, for future use, so just copy the file
    if not os.path.isfile(data_file):
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, 0o777)
        dprint("First Time: copying %s to %s" % (dump_file, data_file))
        copy_file(dump_file, data_file)
        return (False, 'Created initial data file: %s. Run again.' % data_file)

    # finally! verify the data matches
    vprint('*** Verifying database dump for stage % s' % stage)
    return verify_db_dump_file(data_file, dump_file)

def _isns_register_client(client_config, reg_params):
    args = ['--register']
    if reg_params:
        args += reg_params
    return run_client(client_config, args)

def isns_register_client(client_config, reg_params):
    """
    register a client
    """
    (logfile, exit_val) = _isns_register_client(client_config, reg_params)
    if exit_val == 0:
        return (True, '')
    return (False, 'failed to register client, logfile=%s' % logfile)


def _isns_query_objects(client_config, query_list):
    args = ['--query']
    if query_list:
        args += query_list
    return run_client(client_config, args)

def verify_query_response_file(data_file, dump_file):
    """
    verify that the query response files are the same
    """
    dprint("verify_query_response(%s, %s): entering" % (data_file, dump_file))

    data_lines = load_dump(data_file)
    dump_lines = load_dump(dump_file)

    stage = Global._isns_stage_name
    if len(dump_lines) > len(data_lines):
        vprint('*** %s: Excess data in dump at line %d' % (stage, len(data_lines) + 1))
        return (False, 'Excess data in dump at line: %d' % (len(data_lines) + 1))
    if len(dump_lines) < len(data_lines):
        vprint('*** %s: Unexpected end of dump at line %d' % (stage, len(dump_lines) + 1))
        return (False, 'Unexpected end of dump at line %d' % (len(dump_lines) + 1))

    start_pat = re.compile('\S')
    for line_no in range(len(dump_lines)):
        a = dump_lines[line_no]
        b = data_lines[line_no]
        if start_pat.match(a):
            if a == b:
                continue
            vprint('*** %s: Mismatch at line %d' % (stage, line_no))
            vprint('*** Found:    %s' % a)
            vprint('*** Expected: %s' % b)
            return (False, 'Mismatch at line %d' % line_no)

        (a_tag, a_value) = a.split()[1:3]
        (b_tag, b_value) = b.split()[1:3]

        if a_tag != b_tag:
            vprint('*** %s: Tag mismatch at line %d' % (stage, line_no))
            vprint('*** Found:    %s' % a_tag)
            vprint('*** Expected: %s' % b_tag)
            return (False, 'Tag mismatch at line %d' % line_no)

        if a_tag in Global._isns_ignore_tags:
            dprint("verify_query_response_file: ignoring tag %s" % res.group(1))
            continue

        if a_value != b_value:
            vprint('*** %s: Value mismatch at line %d' % (stage, line_no))
            vprint('*** Found:    %s' % a)
            vprint('*** Expected: %s' % b)
            return (False, 'Value mismatch at line %d' % line_no)

    return (True, '')

def verify_query_response(client_config):
    """
    Set up to verify a query response, then do the comparison
    """
    if not Global._isns_test_data:
        print("internal error: Test Case forgot to call set_up_test",
              file=sys.stderr)
        sys.exit(1)
    stage = Global._isns_stage_name

    dump_file = get_logfile_from_config(client_config.path)
    data_dir = Global._isns_test_data
    data_file = '%s/%s' % (data_dir, stage)
    if not Global.security:
        data_file += '-no-security'

    # see if the reference data file exists. If it doesn't, this means
    # we are priming the test case, i.e. generating the data for the
    # first time, for future use, so just copy the file
    if not os.path.isfile(data_file):
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir, 0o777)
        dprint("First time: copying %s to %s" % (dump_file, data_file))
        copy_file(dump_file, data_file)
        return (False, 'Created initial data file: %s. Run again.' % data_file)

    # finally! verify data matches
    vprint('*** Verifying data for stage: %s ***' % stage)
    return verify_query_response_file(data_file, dump_file)

def isns_query_objects(client_config, query_list):
    """
    query object(s)
    """
    (logfile, exit_val) = _isns_query_objects(client_config, query_list)
    if exit_val != 0:
        return (False, 'query objects failed; logfile=%s' % logfile)
    return (True, '')

def isns_query_eid(client_config, extra_args=None):
    """
    Get the eid
    """
    args = ['--query-eid']
    if extra_args:
        args += extra_args

    vprint('*** Querying for EID ***')
    (logfile, exit_val) = run_client(client_config, args)
    if exit_val != 0:
        return (False, 0)

    # get the EID from the log file
    with open(logfile, 'r') as l_fd:
        eid_from_file = l_fd.readline().strip()
    dprint("Found EID=%s from %s!!!" % (eid_from_file, logfile))
    return (True, eid_from_file)

def isns_deregister_client(client_config, extra_args=None):
    """
    Deregister a client -- if no args are passed in then query and use the
    entity id (eid)
    """
    dprint('Deregister client, config=%s' % client_config.path)

    if not extra_args:
        (res, eid) = isns_query_eid(client_config)
        if not res:
            return (False, 'Cannot get our own EID!')
        extra_args = ['eid=%s' % eid]

    args = ['--deregister'] + extra_args

    (logfile, exit_val) = run_client(client_config, args)
    if exit_val != 0:
        return (False, 'deregister failed, exit val=%d' % exit_val)

    return (True, '')

def isns_register_domain(client_config, extra_args=None):
    """
    Register a discovery domain (DD)
    """
    args = ['--local', '--dd-register']
    if extra_args:
        args += extra_args

    (logfile, exit_val) = run_client(client_config, args)
    if exit_val != 0:
        return (False, 'dd-register failed, exit val=%d' % exit_val)

    return (True, '')

def isns_deregister_domain(client_config, extra_args):
    """
    Deregister a discovery domain (DD) -- extra_args are required, since we will
    always need a domain ID (the first argument)
    """
    args = ['--local', '--dd-deregister'] + extra_args
    (logfile, exit_val) = run_client(client_config, args)
    if exit_val != 0:
        return (False, 'dd-dregister (id=%s) failed, exit val=%d' % \
                (extra_args[0], exit_val))

    return (True, '')

def isns_finish():
    """
    all done!
    """
    dprint('isns_finish!')
    for pid in Global._isns_servers:
        dprint('Killing isnsd server pid=%d' % pid)
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            print('warning: cannot send signal to server pid=%d: no such process' % pid,
                  file=sys.stderr)
    Global._isns_servers = []
