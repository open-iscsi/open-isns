Testing
=======

This directory contains the isnsd selftests. Binaries needed for
testing are created by running meson/ninja in the above directory.
See the README file there for direction on building there.

You can run these tests manually, as detailed below, or you
can run them from the parent (main) directory, using:

    # ninja -C builddir test

which runs the 'bitvector' test program, then runs
(from the builddir directory):

    # tests/test-isns.py -f -D ../tests

which runs all the unittests in the "tests" subdirectory,
stopping at the first failure.

To run the tests manually, use the "test-isns.py" script directly.
If you run it from this directory, you do not need to pass in
the "-D DIRECTORY" argument, as it default to the directory
you are in.

Calling the script with no arguments runs all tests. You can pass
in the "--help" option to see the other options.

The tests must be run as root. You do not want the isnsd
service running, as the tests start/stop their own daemon.

For reference, here are current test options:
  -h, --help           show this help message and exit
  -v, --verbose        Verbose output
  -q, --quiet          Quiet output
  --locals             Show local variables in tracebacks
  -f, --failfast       Stop on first fail or error
  -c, --catch          Catch Ctrl-C and display results so far
  -b, --buffer         Buffer stdout and stderr during tests
  -k TESTNAMEPATTERNS  Only run tests which match the given substring
  -s, --secure         Enable security
  -d, --debug          Enable developer debugging
  -l, --list           Lists tests and exits
  -D TEST_DIR, --test-dir TEST_DIR
                       Sets the test dir (default '.')

You can list the unittest name using the "-l" option. By default
the script runs all unit tests, in order, but you can specify tests
to be run by specifying the Unittest name(s), e.g.

    # ./isns-test.py -v Test01 [...]

Note: You can also specify subtests within that unit test, but that's a
bad idea, as the subtests in each unit test are meant to be run together,
in order.  So running some subtest in the middle of a unit test will
generally fail.
