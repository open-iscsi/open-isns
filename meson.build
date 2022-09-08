# meson build for open-isns

project('libisns', 'c',
  version: '0.102',
  meson_version: '>= 0.54.0',
  license: 'LGPL-2.1-or-later',
  default_options: [
    'c_std=gnu99',
    'warning_level=2',
    'buildtype=release',
    'libdir=/usr/lib64',
    'prefix=/usr']
  )

# we will need this below
cc = meson.get_compiler('c')

# get feature options
security_dep = dependency('libcrypto', required: get_option('security'))
slp_dep = cc.find_library('slp', required: get_option('slp'))

subdir('tests')
subdir('doc')
subdir('etc')
subdir('include/libisns')

lib_srcs = files([
  'server.c',
  'client.c',
  'objects.c',
  'callback.c',
  'timer.c',
  'vendor.c',
  'db.c',
  'db-file.c',
  'db-policy.c',
  'relation.c',
  'scope.c',
  'message.c',
  'security.c',
  'authblock.c',
  'policy.c',
  'pki.c',
  'register.c',
  'query.c',
  'getnext.c',
  'deregister.c',
  'esi.c',
  'scn.c',
  'dd.c',
  'entity.c',
  'portal-group.c',
  'storage-node.c',
  'domain.c',
  'simple.c',
  'tags.c',
  'attrs.c',
  'export.c',
  'socket.c',
  'slp.c',
  'error.c',
  'logging.c',
  'config.c',
  'parser.c',
  'buffer.c',
  'pidfile.c',
  'sysdep-unix.c',
  'util.c',
  'bitvector.c',
  'mdebug.c'])

incl_dirs = include_directories(['.', 'include'])

add_project_arguments(
  ['-D_GNU_SOURCE'],
  language: 'c')

#
# build our config.h file
#

conf = configuration_data()
conf.set('WITH_SECURITY', security_dep.found())
conf.set('WITH_SLP', slp_dep.found())
conf.set('HAVE_SLP_H', slp_dep.found())

config_h = configure_file(
  output: 'config.h',
  configuration: conf)

config_incdir = include_directories('.')

config_dep = declare_dependency(
  include_directories: config_incdir,
  sources: config_h)

#
# build our library -- we always build either the static or
# the shared library, or both
#

lib_deps = [config_dep, security_dep, slp_dep]

shared_link_args = []
if get_option('shared_version')
  shared_link_args = '-Wl,--version-script=@0@/libisns.vers'.format(meson.current_source_dir())
endif

libisns_lib = library('isns',
  lib_srcs,
  include_directories: incl_dirs,
  dependencies: lib_deps,
  link_args: shared_link_args,
  version: '0',
  install: true)

libisns_dep = declare_dependency(link_with: libisns_lib)

#
# build binaries
#

our_dependencies = [config_dep, security_dep, libisns_dep, slp_dep]

sbin_dir = get_option('sbindir')

executable('isnsd',
  sources: files('isnsd.c'),
  include_directories: incl_dirs,
  dependencies: our_dependencies,
  install: true,
  install_dir: sbin_dir)

executable('isnsdd',
  sources: files(['isnsdd.c', 'local.c']),
  include_directories: incl_dirs,
  dependencies: our_dependencies,
  install: true,
  install_dir: sbin_dir)

executable('isnsadm',
  sources: files('isnsadm.c'),
  include_directories: incl_dirs,
  dependencies: our_dependencies,
  install: true,
  install_dir: sbin_dir)

# a testing program (not installed, not currently used here)
e = executable('bitvector',
  sources: files('bitvector.c'),
  include_directories: incl_dirs,
  dependencies: our_dependencies,
  c_args: ['-DTEST'])
test('test bitvector', e)

# build our test files ??? (FIXME: not working)
pyunit_test_works = false
if pyunit_test_works
  test_progs = []
  foreach t: tests
    e = executable(t,
      sources: files('tests' / t + '.c'),
      include_directories: incl_dirs,
      dependencies: our_dependencies)
    test_progs += e
  endforeach
endif

#
# man pages
#
install_man([man8_pages, man5_pages])

#
# config files
#
install_data(config_files,
  install_dir: get_option('sysconfdir') / 'isns')

#
# systemd service files
#
install_data(files(['isnsd.service', 'isnsd.socket']),
  install_dir: get_option('systemddir') / 'system')

#
# our package file
#
pkg_mod = import('pkgconfig')
pkg_mod.generate(libraries: libisns_lib,
  version: '0',
  name: 'libisns',
  description: 'iSNS userspace library')

#
# public header files are installed from # include/libisns
#

#
# lastly, create our runtime directory (empty)
#
# NOTE: this can be replaced with install_emptydir() once
# the minimum requirement of Meson is bumped to >=0.60.0

install_subdir('isns',
  install_dir: '/var/lib',
  install_mode: 'r--------')
