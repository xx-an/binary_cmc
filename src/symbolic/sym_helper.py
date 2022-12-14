# Concolic model checker
# Copyright (C) <2021> <Xiaoxin An> <Virginia Tech>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import itertools
from z3 import *
from ..common import lib
from ..common import utils
from ..common import global_var

cnt = 0
mem_cnt = 0
stdout_mem_cnt = 0

STDOUT_ADDR = BitVec('stdout', utils.MEM_ADDR_SIZE)

def cnt_init():
    global cnt
    global mem_cnt
    cnt = 0
    mem_cnt = 0

def gen_sym(length=utils.MEM_ADDR_SIZE):
    global cnt
    if cnt == 23: cnt += 1
    expr = utils.generate_sym_expr(cnt)
    res = BitVec(expr, length)
    cnt += 1
    return res

def gen_mem_sym(length=utils.MEM_ADDR_SIZE):
    global mem_cnt
    expr = utils.generate_sym_expr(mem_cnt)
    res = BitVec('m#' + expr, length)
    mem_cnt += 1
    return res
    
def gen_stdout_mem_sym(length=utils.MEM_ADDR_SIZE):
    global stdout_mem_cnt
    # expr = utils.generate_sym_expr(stdout_mem_cnt)
    res = BitVec('stdout', length) + BitVecVal(stdout_mem_cnt, length)
    stdout_mem_cnt += 1
    return res

def gen_seg_reg_sym(name, length=utils.MEM_ADDR_SIZE):
    res = BitVec('_' + name, length)
    return res

def substitute_sym_val(arg, prev_val, new_val):
    res = substitute(arg, (prev_val, new_val))
    return simplify(res)


def models(formula, max=10):
    solver = Solver()
    solver.add(formula)
    count = 0
    while count < max or max == 0:
        count += 1
        if solver.check() == sat:
            model = solver.model()
            yield model 
            block = []
            for z3_decl in model:
                arg_domains = []
                for i in range(z3_decl.arity()):
                    domain, arg_domain = z3_decl.domain(i), []
                    for j in range(domain.num_constructors()):
                        arg_domain.append( domain.constructor(j) () )
                    arg_domains.append(arg_domain)
                for args in itertools.product(*arg_domains):
                    block.append(z3_decl(*args) != model.eval(z3_decl(*args)))
            solver.add(Or(block))

def gen_sym_x(length=utils.MEM_ADDR_SIZE):
    res = BitVec('x', length)
    return res
    
def bottom(length):
    return BitVec('Bottom', length)

def gen_spec_sym(name, length=utils.MEM_ADDR_SIZE):
    return BitVec(name, length)

def is_bit_vec_num(sym):
    return isinstance(sym, BitVecNumRef)

def is_equal(x, y):
    return simplify(x == y)


def sym_op(op, x, y):
    res = None
    if op == '-':
        res = simplify(x - y)
    elif op == '+':
        res = simplify(x + y)
    return res

def not_equal(x, y):
    return simplify(x != y)

def is_less(x, y):
    return simplify(x < y)

def is_greater(x, y):
    return simplify(x > y)

def is_less_equal(x, y):
    return simplify(x <= y)

def is_greater_equal(x, y):
    return simplify(x >= y)

def is_neg(x):
    return simplify(x < 0)

def is_pos(x):
    return simplify(x >= 0)


LOGIC_OP_FUNC_MAP = {
    '==': is_equal,
    '<>': not_equal,
    '!=': not_equal,
    '<': is_less,
    '>': is_greater,
    '<=': is_less_equal,
    '>=': is_greater_equal
}

def sym_not(sym):
    return Not(sym)

def bit_ith(sym, idx):
    return simplify(Extract(idx, idx, sym))

def most_significant_bit(val, dest_len):
    msb = bit_ith(val, dest_len - 1)
    return is_equal(msb, 1)

def smost_significant_bit(val, dest_len):
    smsb = bit_ith(val, dest_len - 2)
    return is_equal(smsb, 1)

def least_significant_bit(val, dest_len):
    lsb = bit_ith(val, 0)
    return is_equal(lsb, 1)


def bit_vec_wrap(name, length):
    return BitVec(name, length)


def check_pred_satisfiable(predicates):
    s = Solver()
    for pred in predicates:
        s.add(pred)
    r = s.check()
    if r == sat:
        return s.model()
    else:
        return False


def repeated_check_pred_satisfiable(predicates, num):
    res = []
    s = Solver()
    for pred in predicates:
        s.add(pred)
    while len(res) < num and s.check() == sat:
        m = s.model()
        res.append(m)
        # Create a new constraint the blocks the current model
        block = []
        for d in m:
            # d is a declaration
            if d.arity() > 0:
                raise Z3Exception("uninterpreted functions are not supported")
            # create a constant from declaration
            c = d()
            if is_array(c) or c.sort().kind() == Z3_UNINTERPRETED_SORT:
                raise Z3Exception("arrays and uninterpreted sorts are not supported")
            block.append(c != m[d])
        s.add(And(block))
    return res


def pp_z3_model_info(m):
    res = []
    for d in m.decls():
        s_val = m[d]
        res.append(d.name() + ': ' + str(s_val))
    return ', '.join(res)


def top_stack_addr(store):
    res = simplify(store[lib.REG]['rsp'][0])
    if res != None and sym_is_int_or_bitvecnum(res):
        res = res.as_long()
    return res


def bitwiseXNOR(sym, length):
    res = bit_ith(sym, 0)
    for i in range(1, length):
        curr = bit_ith(sym, i)
        res = simplify(~ (res ^ curr))
    return is_equal(res, 1)

def zero_ext(length, sym):
    return ZeroExt(length, sym)


def extract(high, low, sym):
    return simplify(Extract(high, low, sym))

def upper_half(sym):
    sym_len = sym.size()
    return simplify(Extract(sym_len - 1, sym_len // 2, sym))


def lower_half(sym):
    sym_len = sym.size()
    return simplify(Extract(sym_len // 2 - 1, 0, sym))

def truncate_to_size(dest, res):
    dest_len = utils.get_sym_length(dest)
    return simplify(Extract(dest_len - 1, 0, res))

def string_of_address(address):
    res = address
    if isinstance(address, int):
        res = hex(address)
    elif is_bit_vec_num(address):
        res = hex(address.as_long())
    elif not isinstance(address, str):
        res = str(address)
    return res

def sym_is_int_or_bitvecnum(address):
    return isinstance(address, (int, BitVecNumRef))


def int_from_sym(val):
    res = val.as_long()
    return res


def extract_bytes(high, low, sym):
    return Extract(high * 8 - 1, low * 8, sym)


def concat_sym(*args):
    return Concat(args)


def bit_vec_val_sym(val, length=utils.MEM_ADDR_SIZE):
    return BitVecVal(val, length)

def neg(sym):
    return simplify(-sym)

def not_op(sym):
    return simplify(~sym)

def update_sym_expr(expr, new_expr, rel='or'):
    res = expr
    if rel == 'or':
        res = simplify(Or(expr, new_expr))
    elif rel == 'and':
        res = simplify(And(expr, new_expr))
    elif rel == 'r':
        res = new_expr
    return res

def is_term_address(address):
    return is_equal(address, BitVec('x', utils.MEM_ADDR_SIZE))


def remove_memory_content(store, mem_address):
    if mem_address in store[lib.MEM]:
        del store[lib.MEM][mem_address]


def is_z3_bv_var(arg):
    return isinstance(arg, BitVecRef)

def is_bv_sym_var(arg):
    return isinstance(arg, BitVecRef) and not isinstance(arg, BitVecNumRef)

def bvnum_eq(lhs, rhs):
    res = None
    if lhs.size() != rhs.size():
        res = False
    else:
        res = is_equal(lhs, rhs)
    return res


def strict_bitvec_equal(left, right):
    res = True
    if isinstance(left, BitVecNumRef) and isinstance(right, BitVecNumRef):
        res = bvnum_eq(left, right)
    elif isinstance(left, BitVecNumRef):
        res = False
    elif isinstance(right, BitVecNumRef):
        res = False
    else:
        res = bvnum_eq(left, right)
    return res


def bitvec_eq(v_old, v):
    res = True
    if isinstance(v_old, BitVecNumRef) and isinstance(v, BitVecNumRef):
        res = bvnum_eq(v_old, v)
    elif isinstance(v_old, BitVecNumRef):
        res = False
    return res


def merge_sym(lhs, rhs, address_inst_map):
    res = rhs
    if isinstance(lhs, BitVecNumRef) and isinstance(rhs, BitVecNumRef):
        lhs_num = int_from_sym(lhs)
        rhs_num = int_from_sym(rhs)
        if rhs_num not in address_inst_map:
            if lhs_num != rhs_num:
                res = gen_sym(rhs.size())
                # if lhs_num >= global_var.elf_info.rodata_start_addr and lhs_num < global_var.elf_info.rodata_end_addr:
                #     res = gen_sym(rhs.size())
                # elif rhs_num < global_var.elf_info.rodata_start_addr or rhs_num >= global_var.elf_info.rodata_end_addr:
                #     res = gen_sym(rhs.size())
    elif isinstance(rhs, BitVecNumRef):
        rhs_num = int_from_sym(rhs)
        if rhs_num not in address_inst_map:
            res = gen_sym(rhs.size())
    return res


def is_bottom(sym_val, dest_len):
    return sym_val == bottom(dest_len)


def parse_predefined_constraint(constraint_config_file):
    res = {}
    with open(constraint_config_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                line = line.replace('\t', ' ')
                line_split = line.strip().split(' ', 1)
                ext_func_name = line_split[0].strip()
                constraint = line_split[1].strip()
                if ext_func_name in res:
                    res[ext_func_name].append(constraint)
                else:
                    res[ext_func_name] = [constraint]
    return res


def addr_in_rodata_section(int_addr):
    return global_var.binary_info.rodata_start_addr <= int_addr < global_var.binary_info.rodata_end_addr


def addr_in_data_section(int_addr):
    return global_var.binary_info.data_start_addr <= int_addr < global_var.binary_info.data_end_addr


def addr_in_text_section(int_addr):
    return global_var.binary_info.text_start_addr <= int_addr < global_var.binary_info.text_end_addr


def addr_in_bin_header(int_addr):
    return int_addr < global_var.binary_info.max_bin_header_address


def addr_in_heap(int_addr):
    return utils.MIN_HEAP_ADDR <= int_addr < utils.MAX_HEAP_ADDR


def addr_in_heap_section(int_addr):
    return utils.MIN_HEAP_ADDR <= int_addr < utils.MAX_HEAP_ADDR


def addr_in_stack_section(int_addr):
    return utils.MIN_STACK_FRAME_POINTER <= int_addr

