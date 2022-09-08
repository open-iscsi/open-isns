AC_INIT(open-isns, [0.101])
AC_CONFIG_SRCDIR([isnsd.c])
AC_CONFIG_AUX_DIR([aclocal])

AC_CONFIG_HEADER(config.h)

AC_PROG_CC
AC_CANONICAL_HOST
AC_C_BIGENDIAN

AC_PROG_CPP
AC_PROG_INSTALL
AC_PROG_LN_S
AC_PROG_MAKE_SET
AC_PATH_PROG(SH, sh)

dnl C Compiler features
AC_C_INLINE
if test "$GCC" = "yes"; then
        CFLAGS="-Wall -Wextra $CFLAGS"
	CPPFLAGS="$CPPFLAGS -D_GNU_SOURCE"
fi

dnl Checks for header files.
AC_HEADER_STDC
AC_HEADER_SYS_WAIT
AC_CHECK_HEADERS([errno.h fcntl.h malloc.h stdlib.h string.h strings.h sys/time.h unistd.h locale.h getopt.h])

# Check if socket() is in libsocket
AC_CHECK_LIB(socket, socket, [LIBS="$LIBS -lsocket"])


AC_SUBST(GETOPTSRC)
AC_CHECK_FUNC(getopt_long, AC_DEFINE(HAVE_GETOPT_LONG, 1, [Define if you have the `getopt_long' function.]),
		[GETOPTSRC="$GETOPTSRC \$(top_srcdir)/compat/my_getopt.c"
		CPPFLAGS="-I\$(top_srcdir)/compat/ $CPPFLAGS"
		AC_DEFINE(HAVE_GETOPT_H, 1, [Define if you have the <getopt.h> header file.])])

WITH_SECURITY=maybe
AC_ARG_WITH(security,
	[  --with-security         Enable iSNS authentication - requires OpenSSL],
	[
		if test "x$withval" = "xno" -o "x$withval" = "xyes"; then
			WITH_SECURITY=$withval
		else
			WITH_SECURITY=yes
			CPPFLAGS="$CPPFLAGS -I${withval}"
			LDFLAGS="$LDFLAGS -L${withval}"
		fi
	]
)

if test "x$WITH_SECURITY" != "xno" ; then
	# Check for openssl support - very primitive, we just
	# check for the presence of crypto.h
	AC_CHECK_HEADERS([openssl/crypto.h],
		,
		[have_libcrypto=no])
	AC_CHECK_LIB(crypto, EVP_PKEY_new,
		[SECLIBS="-lcrypto"],
		[have_libcrypto=no])

	if test "x$have_libcrypto" != "xno" ; then
		AC_DEFINE(WITH_SECURITY, 1,
			[Define if you want to support iSNS authentication])
	else
		if test "x$WITH_SECURITY" = "xyes" ; then
			AC_MSG_ERROR([Security requested, but unable to find libcrypto])
		fi
	fi
fi
AC_SUBST(SECLIBS)

WITH_SLP=maybe
AC_ARG_WITH(slp,
	[  --with-slp              Enable SLP for server discovery - requires OpenSLP],
	[
		if test "x$withval" = "xno" -o "x$withval" = "xyes"; then
			WITH_SLP=$withval
		else
			WITH_SLP=yes
			CPPFLAGS="$CPPFLAGS -I${withval}"
			LDFLAGS="$LDFLAGS -L${withval}"
		fi
	]
)

if test "x$WITH_SLP" != "xno" ; then
	# Check for openslp support - very primitive
	AC_CHECK_HEADERS([slp.h],,
		[have_openslp=no])
	AC_CHECK_LIB(slp, SLPOpen,
		[SLPLIBS="-lslp"],
		[have_openslp=no])

	if test "x$have_openslp" != "xno" ; then
		AC_DEFINE(WITH_SLP, 1,
			[Define if you want to support SLP discovery])
	else
		if test "x$WITH_SLP" = "xyes" ; then
			AC_MSG_ERROR([SLP requested, but unable to find openslp])
		fi
	fi
fi
AC_SUBST(SLPLIBS)

RUNDIR=/var/run
AC_ARG_WITH(rundir,
	[  --with-rundir=/var/run  The runtime directory for PID files etc.],
	[
		if test "x$withval" = "xno" -o "x$withval" = "xyes"; then
			AC_MSG_ERROR([No rundir value specified.])
		else
			RUNDIR="${withval}"
		fi
	]
)

MEMDEBUG=
AC_ARG_ENABLE(memdebug,
	[  --enable-memdebug       Enable malloc debugging],
	[
		if test "x$enableval" = "xyes" ; then
			CPPFLAGS="$CPPFLAGS -DMEMDEBUG"
		fi
	]
)
AC_SUBST(OPTIMIZE)

ENABLE_SHARED=0
AC_ARG_ENABLE(shared,
	[  --enable-shared         Build shared library],
	[
		if test "x$enableval" = "xyes" ; then
			ENABLE_SHARED=1
		fi
	]
)
ENABLE_STATIC=1
AC_ARG_ENABLE(static,
	[  --disable-static        Build static library],
	[
		if test "x$enableval" = "xno" ; then
			ENABLE_STATIC=0
		fi
	]
)

if test "x$ENABLE_SHARED" = "x1" ; then
	# Taken and modified from libpng's configure.ac
	AC_MSG_CHECKING([if libraries can be versioned])
	GLD=`$CC -Wl,--help < /dev/null 2>/dev/null | grep version-script`
	if test "$GLD"; then
	HAVE_LD_VERSION_SCRIPT=1
	AC_MSG_RESULT(yes)
	else
	HAVE_LD_VERSION_SCRIPT=0
	AC_MSG_RESULT(no)
	AC_MSG_WARN(*** You have not enabled versioned symbols.)
	fi
	AC_SUBST(HAVE_LD_VERSION_SCRIPT)
fi

VERSION=AC_PACKAGE_VERSION
AC_SUBST(ENABLE_SHARED)
AC_SUBST(ENABLE_STATIC)
AC_SUBST(RUNDIR)
AC_SUBST(VERSION)

AC_OUTPUT(Makefile include/libisns/paths.h)

dnl Warn user that autoconf is deprecated here
AC_MSG_WARN([Autotool/configure/make are deprecated, and will be removed soon. Please using "meson" instead])
