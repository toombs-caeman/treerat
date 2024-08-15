from base import *
from typing import Any, Callable
import struct

class opcode:
    """
    A descriptor to wrap opcode definitions.

    `code` is a unique byte that identifies the compiled opcode
    `func` is a function that implements the opcode
    `argfmt` is a string that follows the struct convention for unpacking arguments to that function.

    """
    def __new__(cls, code:bytes|str|int, argfmt='', func:Callable|None=None):
        # This is a bit of python magic
        if func is None:
            return lambda f:opcode(code, argfmt, f)
        o = object.__new__(cls)
        o.__init__(code, argfmt, func)
        return o

    def __init__(self, code:bytes|str|int, argfmt:str='', func:Callable|None=None):
        # normalize code to be bytes of length 1
        match code:
            case str():
                code = bytes.fromhex(code)
            case int():
                code = code.to_bytes()
        if len(code) != 1:
            raise CompileError('assigned bytecode {hex(byte)} out of allowed range')
        if func is None:
            raise CompileError('opcode {hex(byte)} has no implementation')

        self.code = code
        self.func = func
        self.argfmt = argfmt
        self.size = 1 + struct.calcsize(self.argfmt)

    def __str__(self):
        return self.func.__name__
    def __get__(self, obj, objtype=None):
        return self
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __bytes__(self):
        return self.code
    def unpack_from(self, buffer, offset=0):
        #if (b:=buffer[offset:offset+1]) != self.code:
        #    raise EvalError(f'Tried to unpack instruction {self.code}:{self} but found {b}.')
        return (self, *struct.unpack_from(self.argfmt, buffer, offset+1))


class ByteVM(Evaluator):
    """
    A base class for a bytecode vm.

    Subclasses need to define:
    * compiler methods with names matching each AST kind
    * virtual machine instructions using the @opcode decorator

    Really, this class is two things: a tree to bytecode compiler and a vm.

    This class assumes that instructions are exactly one byte long.

    There are some protections in play
    * stack and code segments are represented separately, so you can't accidentally overflow one into another.
        * in a real machine these would just be contiguous memory
    * stack will throw an error if you try to write outside
    """
    STACK_LIMIT = 256

    def __init__(self, ast:node|bytes|bytearray|None=None):
        # registers are instance properties
        self.IP = 0  # instruction pointer
        self.ACC = 0 # accumulator
        self.SP = 0  # stack pointer
        # the stack is a mutable array of bytes
        self.stack = bytearray(self.STACK_LIMIT)
        # code segment is a mutable array of bytes. compile ast if given.
        #self.code = bytearray(b'' if ast is None else self.compile(ast))
        self.code = self.compile(ast)

        # collect opcodes
        funcs = [op
                for k in dir(self)
                if isinstance((op:=getattr(self, k)), opcode)]
        self.__opcodes = {bytes(func)[0]:func for func in funcs}
        if len(funcs) != len(self.__opcodes):
            raise CompileError('duplicate byte codes detected')



    def __call__(self, ast:node|None=None, vis:Visualizer|None=None):
        self.vis = vis
        if ast is not None:
            self.code = bytearray(self.compile(ast))

        self.IP = 0
        self.SP = 0

        while self.IP < len(self.code):
            self.step()

        if self.SP:
            return self.peek()

    def compile(self, *args) -> bytes:
        return b''.join(self._compile(a) for a in args)

    def _compile(self, a:node|bytes|bytearray|str|int|None) -> bytes:
        match a:
            case bytes()|bytearray():
                return a
            case node():
                # compiling ast is delegated by kind to a method with the matching name
                return getattr(self, a.kind)(*a)
            case str():
                # strings are treated as a hex encoding (ex 'FF' -> b'\xFF')
                # use a byte literal (b'hello') if you want a different encoding
                return bytes.fromhex(a)
            case int():
                return a.to_bytes()
            case None:
                return b''
            case _:
                # as a final option we can try to compile any object that converts to bytes
                # this is used to directly convert bytecodes
                return bytes(a)

    def step(self):
        """process a single instruction"""
        # TODO instrument with Vis
        opcode = self.code[self.IP]
        if opcode not in self.__opcodes:
            raise EvalError(f'unrecognized bytecode {opcode}')
        op, *args = self.__opcodes[opcode].unpack_from(self.code, self.IP)
        self.IP += op.size
        op(self, *args)

    # common stack operations
    def push(self, value, fmt='B'):
        """push a value to the stack with bounds checks."""
        size = struct.calcsize(fmt)
        if self.SP + size >= self.STACK_LIMIT:
            raise EvalError('stack overflow')
        struct.pack_into(fmt, self.stack, self.SP, value)
        self.SP += size

    def peek(self, fmt='B') -> Any:
        """peek a value to the stack with bounds checks."""
        size = struct.calcsize(fmt)
        if len(fmt) > 1:
            raise EvalError('pop should only pop a single value')
        if self.SP < size:
            raise EvalError('stack empty')
        return struct.unpack_from(fmt, self.stack, self.SP-size)[0]

    def pop(self, fmt='B') -> int:
        """pop a value to the stack with bounds checks."""
        size = struct.calcsize(fmt)
        if len(fmt) > 1:
            raise EvalError('pop should only pop a single value')
        if self.SP < size:
            raise EvalError('stack empty')
        self.SP -= size
        return struct.unpack_from(fmt, self.stack, self.SP)[0]

    def decompile(self, code:bytes=...):
        """return the bytecode as a human readable string."""
        if code is ...:
            code = self.code

        lines = []
        IP = 0
        while IP < len(code):
            op = self.__opcodes[code[IP]].unpack_from(code, IP)
            lines.append(' '.join(map(str, op)))
            IP += op[0].size

        return '\n'.join(f'    {i}' for i in lines)


if __name__ == "__main__":
    class TestVM(ByteVM):

        @opcode(0)
        def drop(self):
            """drop value from the stack"""
            self.SP -= 1

        @opcode(1, 'B')
        def push_byte(self, value):
            """push a byte from instructions to the stack"""
            self.push(value)

        @opcode(2)
        def add(self):
            top = self.pop()
            under = self.pop()
            self.push(top + under)

        @opcode(3)
        def unsafe_add(self):
            self.SP -= 1
            self.stack[self.SP-1] += self.stack[self.SP]

        @opcode(4)
        def print(self):
            print(self.stack[self.SP-1])

        @opcode('FE')
        def greeting(self):
            print("It's a new day...")

        @opcode(0xFF)
        def goodbye(self):
            print('bye!')

        def start(self) -> bytes:
            # the following is equivalent to
            #   return bytes.fromhex('FE010501030204FF')
            return self.compile(
                self.greeting,
                self.push_byte, 5,
                self.push_byte, 3,
                self.add,
                self.print,
                self.goodbye
                )

    import parser
    P = parser.PackratParser("""%start <- 'ok'""")
    ast = P('ok')
    vm = TestVM(ast)
    print(f"compiled: {vm.code.hex().upper()}")
    print(f'decompiled:\n{vm.decompile()}')
    print('running:')
    vm()


