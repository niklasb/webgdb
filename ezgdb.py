from __future__ import print_function
import re
import tempfile
import traceback

import util

REGISTERS = {
    8 : ['al', 'ah', 'bl', 'bh', 'cl', 'ch', 'dl', 'dh'],
    16: ['ax', 'bx', 'cx', 'dx'],
    32: ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp', 'eip'],
    64: ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp', 'rip',
         'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15']
}

class EzGdb(object):
    def __init__(self, gdb):
        self.gdb = gdb

    def execute(self, cmd):
        with tempfile.NamedTemporaryFile() as f:
            self.gdb.execute('set logging off') # prevent nested call
            self.gdb.execute('set height 0') # disable paging
            self.gdb.execute('set logging file {}'.format(f.name))
            self.gdb.execute('set logging overwrite on')
            self.gdb.execute('set logging redirect on')
            self.gdb.execute('set logging on')
            try:
                self.gdb.execute(cmd)
                self.gdb.flush()
                return f.read()
            finally:
                self.gdb.execute('set logging off')

    @util.memoize
    def get_arch(self):
        out = self.execute('maintenance info sections ?')
        m = re.search(r'file type ([^\.]+)', out)
        assert m
        arch = m.group(1)
        return arch, 64 if '64' in arch else 32

    def get_bits(self):
        return self.get_arch()[1]

    def get_stack_reg(self):
        return REGISTERS[self.get_bits()][7]

    def get_ip_reg(self):
        return REGISTERS[self.get_bits()][8]

    def get_breakpoints(self):
        out = self.execute('info breakpoints')
        result = []
        for line in out.splitlines():
            if re.match(r'^(\d+).*', line):
                addr = line.split()[4]
                if addr.startswith('0x'):
                    result.append(int(addr, 16))
        return result

    def get_registers(self):
        regs = {}
        for line in self.execute('info registers').splitlines():
            parts = line.split()
            regs[parts[0]] = int(parts[1], 16)
        return regs

    def get_ip(self):
        return self.get_registers()[self.get_ip_reg()]

    def disassemble(self, addr, n):
        self.gdb.execute('set disassembly-flavor intel')
        asm = self.execute('x/{}i {}'.format(n, addr))
        lines = asm.splitlines()
        func = None
        if lines[0][-1] == ':':
            func = lines[0].split()[-1][:-1]
            lines = lines[1:]
        ins = []
        lines = iter(lines)
        for line in lines:
            parts = line.split()
            if parts[0] == '=>':
                parts = parts[1:]

            label = None
            addr = int(parts[0].rstrip(':'), 16)

            if parts[1].startswith('<'):
                label = parts[1][1:-2]
                if label[0] == '+':
                    label = func + label
                parts = parts[2:]

            # join with succeeding line if wrapped
            if not parts:
                parts += next(lines).split()
            mnemonic = parts[0]
            op_str = ' '.join(parts[1:])
            ins.append({
                'address': addr,
                'label': label,
                'mnemonic': mnemonic,
                'op_str': op_str,
            })
        return ins
