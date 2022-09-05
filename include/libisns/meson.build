# meson build control file for open-isns public include files

inc_conf = configuration_data()
inc_conf.set('RUNDIR', get_option('rundir'))
inc_conf.set('VERSION', meson.project_version())

static_hdr_files = files([
  'attrs.h',
  'buffer.h',
  'isns.h',
  'isns-proto.h',
  'message.h',
  'source.h',
  'types.h',
  'util.h'])

template_hdr_name = 'paths.h'
template_hdr_file = files('paths.h.in')

configure_file(
  input: template_hdr_file,
  output: template_hdr_name,
  configuration: inc_conf,
  install: true,
  install_dir: get_option('includedir') / 'libisns')

install_headers(static_hdr_files, subdir: 'libisns')
