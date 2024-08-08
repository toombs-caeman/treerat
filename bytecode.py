from base import *
from typing import Any, Callable

class opcode:
    """A descriptor to wrap opcode definitions."""
    def __new__(cls, code:bytes, func:Callable|None=None):
        # This is a bit of python magic
        if func is None:
            return lambda f:opcode(code, f)
        o = object.__new__(cls)
        o.__init__(code, func)
        return o
    def __init__(self, code:bytes, func:...=None):
        # normalize code to be bytes of length 1
        match code:
            case str():
                code = bytes.fromhex(code)
            case int():
                code = code.to_bytes()
        if len(code) != 1:
            raise CompileError('assigned bytecode {hex(byte)} out of allowed range')
        self.code = code
        self.func = func
    def __get__(self, obj, objtype=None):
        return self
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def to_bytes(self):
        return self.code
    def __bytes__(self):
        return self.code

class ByteVM(Evaluator):
    """
    A base class for a bytecode vm.

    Subclasses need to define:
    * compiler methods with names matching each AST kind
    * virtual machine instructions using the @opcode decorator

    This class assumes that instructions are exactly one byte long.

    There are some protections in play
    * stack, const and code segments are represented separately, so you can't accidentally overflow one into another.
        * in a real machine these would just be contiguous memory
    * const is immutable
    * stack will throw an error if you try to write outside
    """
    STACK_LIMIT = 256

    def __init__(self, ast:node|None=None):
        # registers are instance properties
        self.IP = 0  # instruction pointer
        self.ACC = 0 # accumulator
        self.SP = 0  # stack pointer
        # the stack is a mutable array of bytes
        self.stack = bytearray(self.STACK_LIMIT)
        # const segment can be written during compilation but is made immutable before execution
        self.const = bytearray()
        # code segment is a mutable array of bytes. compile ast if given.
        self.code = bytearray(b'' if ast is None else self.compile(ast))

        # collect opcodes
        funcs = [op
                for k in dir(self)
                if isinstance((op:=getattr(self, k)), opcode)]
        self.__opcodes = {bytes(func)[0]:func for func in funcs}
        if len(funcs) != len(self.__opcodes):
            raise CompileError('duplicate byte codes detected')



    def __call__(self, ast:node|None=None, vis:Visualizer|None=None):
        self.IP = 0
        self.SP = 0
        if ast is not None:
            self.const = bytearray()
            self.code = bytearray(self.compile(ast))
        # make const immutable
        self.const = bytes(self.const)

        while self.IP < len(self.code):
            self.step()

        if self.SP:
            return self.peek()

    def compile(self, __o:node) -> bytes:
        match __o:
            case bytes()|bytearray():
                return __o
            case node():
                # compiling ast is delegated by kind to a method with the matching name
                return getattr(self, __o.kind)(*__o)
            case str():
                # strings are treated as a hex encoding (ex 'FF' -> b'\xFF')
                # use a byte literal (b'hello') if you want a different encoding
                return bytes.fromhex(__o)
            case int():
                return __o.to_bytes()
            case _:
                # as a final option we can try to compile any object that converts to bytes
                # this is used to directly convert bytecodes
                return bytes(__o)

    def step(self):
        """process a single instruction"""
        # TODO instrument with Vis
        bytecode = self.code[self.IP]
        self.IP += 1
        if bytecode not in self.__opcodes:
            raise EvalError(f'unrecognized bytecode {bytecode}')
        self.__opcodes[bytecode](self)

    # common stack operations
    def push(self, value):
        """push a value to the stack with bounds checks."""
        if self.SP >= self.STACK_LIMIT:
            raise EvalError('stack overflow')
        self.stack[self.SP] = value
        self.SP += 1

    def peek(self) -> Any:
        """peek a value to the stack with bounds checks."""
        if self.SP >= self.STACK_LIMIT:
            raise EvalError('stack overflow')
        if self.SP <= 0:
            raise EvalError('stack empty')
        return self.stack[self.SP]

    def pop(self) -> Any:
        """pop a value to the stack with bounds checks."""
        if self.SP <= 0:
            raise EvalError('stack empty')
        self.SP -= 1
        return self.stack[self.SP]

    def decompile(self, code:bytes=...):
        # TODO
        if code is ...:
            code = self.code
        out = (
            self.__opcodes[i].func.__name__
            if i in self.__opcodes else
            i.to_bytes().hex()
            for i in code
        )

        return '\n'.join(f'    {i}' for i in out)


if __name__ == "__main__":
    class TestVM(ByteVM):

        @opcode(0)
        def drop(self):
            """drop value from the stack"""
            self.SP -= 1

        @opcode(1)
        def push_value(self):
            """push a byte from instructions to the stack"""
            self.stack[self.SP] = self.code[self.IP]
            self.SP += 1
            self.IP += 1

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
            instr = [
                self.greeting,
                self.push_value, 5,
                self.push_value, 3,
                self.add,
                self.print,
                self.goodbye,
                ]
            return b''.join(self.compile(I) for I in instr)

    import parser
    P = parser.PackratParser("""%start <- 'ok'""")
    ast = P('ok')
    vm = TestVM(ast)
    #print('decompiled source:')
    #print(vm.decompile())
    print(f"compiled bytecode {vm.code.hex().upper()}")
    vm()


