
Welcome to Open-iSNS
====================
This is a partial implementation of iSNS, according to RFC4171.
The implementation is still somewhat incomplete, but I'm releasing
it for your reading pleasure.

The distribution comprises:

* isnsd
        This is the iSNS server, supporting persistent storage
        of registrations in a file based database.

* isnsadm
        A command line utility for querying the iSNS database,
        and for registering/deregistering nodes and portals

* isnsdd
        An iSNS Discovery Daemon, which is still very much work
        in progress. The daemon is supposed to handle all the
        bit banging and server communications required to register
        a node, its portals, and to maintain the registration.
        It is also supposed to use the iSNS State Change Notification
        framework to learn of new targets or initiators coming online,
        and inform local services (such as the iSCSI initiator daemon)
        about these changes.

Thanks!
-------
Many thanks to Albert Pauw for his fearless testing of snapshots,
and his copious feedback!


What works, after a fashion:
----------------------------
 -      For now, I've been focusing on getting the iSCSI part to
        work. There is some very basic support for FC objects, but
        this will be hardly useful yet.

 -      Registration, deregistration, query, getnext
        You can use isnsadm to register iSCSI nodes, and portals.
        isnsadm also illustrates how this is supposed to be used from
        the client perspective.

 -      Discovery domains are supported mostly. The administrator
        can create discovery domains using isnsadm, and place storage
        nodes in domains. Queries by clients are scoped by their
        discovery domains membership, so that they will be unable to
        see nodes not part of a shared DD.

        Open-iSNS currently does not allow clients to place themselves
        in a DD.

        Optionally, storage nodes that are not in any discovery domain
        will be placed in a "default DD" (see the DefaultDiscoveryDomain
        in isnsd.conf).

 -      ESI, supported both by the server and the discovery daemon

 -      SCN, supported by the server and the discovery daemon

What is still missing
---------------------
 -      Better documentation (esp. a HOWTO on getting started with iSNS)
 -      DD Sets
 -      Various bits and pieces of the protocol
 -      FC support

Building Open-iSNS
------------------
Meson is now the only build system, as the old
autoconf files have been removed.

Using meson to Build open-isns
------------------------------
For Open-iSNS, the system is built using meson and ninja
(see https://github.com/mesonbuild/meson). If these packages aren't
available to you on your Linux distribution, you can download
the latest release from: https://github.com/mesonbuild/meson/releases.
The README.md file there describes in detail how to build it yourself,
including how to get ninja.

To build the open-isns, first run meson to configure the build,
from the top-level open-iscsi directory, e.g.:

    rm -rf builddir
    mkdir builddir
    meson [<OPTIONS>] setup builddir

Meson has many options, some built in, and some specifically for
this project. To see the built-in options, run:

    meson setup --help

One option of note is "--default-library={shared,static,both}". The
meson default is "shared".

The project-specific options are set using -D<OPTION>=VALUE. OPTIONS
are from. You can use 'meson configure' to see these project options:

   security        feature [check]           use libcrypt for security
   slp             feature [check]           use Service Location Protocol
   shared_version  boolean [true]            use library versioning, if
                                             building a shared library
   systemddir      string [/usr/lib/systemd] location of systemd files
   rundir          string [/var/run]         where socket and pidfile go
   enable-mdebug   boolean [false]           Enable memory debugging

Thus, one might run:

    meson setup --default-library=both -Dsecurity=disabled -Drundir=/some/dir

Once meson has created and set up your "builddir" directory, you can
actually build the code using ninja:

    ninja -C builddir [--verbose]

Note: for testing purposes, you need to use "builddir", and not some other
directory name, since the python tests, in the "tests" subdirectory, expect
the binaries to be there.

Dependencies:
-------------
 -      If you want to build Open-iSNS with support for authentication,
        you need the OpenSSL libraries and header files installed.

 -      If you want to build Open-iSNS with SLP support, you need the
        OpenSLP library and header file installed.



Testing
-------
See the README in the tests subdirectory for information on running
the isnsd selftests. You can run them from the main directory, if
you wish, as root, using:

    # ninja -C builddir test

Getting started
---------------
On the iSNS server, you need to generate a server key and install it. The
simplest way is probably to use the isnssetup script included in the
source package.

For each client you wish to use, you should then register that key using
the example setup script, or steps similar to those in the script.

iSNS Security
-------------
This implementation of iSNS supports authentication, as described in RFC
4171. In order to use it, you have to create DSA keys for the server and
all clients.

iSNS uses conceptually the same security mechanism as SLP, and identifies
principals by a "Security Parameter Index", which is essentially a string
identifying a key.

Open-iSNS fully supports DSA based security, and offers a flexible
policy mechanism that ties an SPI to a network entity and the storage
node names it is allowed to use. For an introduction to the security
model used by Open-iSNS, refer to the isns_config(5) manual page. An
overview on setting up the iSNS server for authentication is given in
the EXAMPLES section of the isnsadm(8) manual page.

Downloading Open-iSNS
---------------------
Open-iSNS is available for download from:

        https://github.com/open-iscsi/open-isns/archive/$(VERSION).tar.gz

or, in source form, from:

        https://github.com/open-iscsi/open-isns

You have to grab the latest tarball and compile it; fancy things such
as RPMs are not available yet.

------------------------------------------------------------------


                        COPYRIGHT NOTICE

        Copyright (C) 2007 Olaf Kirch.

        This library is free software; you can redistribute it and/or
        modify it under the terms of the GNU Lesser General Public
        License as published by the Free Software Foundation; either
        version 2.1 of the License, or (at your option) any later version.

        This library is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
        Lesser General Public License for more details.

        You should have received a copy of the GNU Lesser General Public
        License along with this library; if not, write to the Free Software
        Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
        02110-1301 USA.

------------------------------------------------------------------

Author:
        Olaf Kirch <okir@suse.com>

Current maintainer:
        Lee Duncan <lduncan@suse.com>           (since 2015)

------------------------------------------------------------------

Things to do:
-------------
* fully implement/require device discovery sets
* implement ability to pass in flags to systemd service file for isnsd
* ensure all tests pass with security
