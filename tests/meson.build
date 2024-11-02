# meson build control file for open-isns tests

tests = ['pauw1', 'pauw2', 'pauw3', 'pauw4']

test_prog = find_program('test-isns.py')
test('unittest the daemon', test_prog, args: ['-f', '-D', '../tests'], timeout: 120)
