from bytecode import *
import struct

class Class:
    """
    A class file consists of a single ClassFile structure: 

    ClassFile {
        u4             magic;
        u2             minor_version;
        u2             major_version;
        u2             constant_pool_count;
        cp_info        constant_pool[constant_pool_count-1];
        u2             access_flags;
        u2             this_class;
        u2             super_class;
        u2             interfaces_count;
        u2             interfaces[interfaces_count];
        u2             fields_count;
        field_info     fields[fields_count];
        u2             methods_count;
        method_info    methods[methods_count];
        u2             attributes_count;
        attribute_info attributes[attributes_count];
    }
    https://docs.oracle.com/javase/specs/jvms/se7/html/jvms-4.html
    """
    def __init__(self, data:bytes):
        # assert that magic number is ok
        self.magic, self.minor_version, self.major_version, self.constant_pool_count = struct.unpack_from('4sHHH', data, 0)

        # use const_pool_count to unpack contant pool

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            return cls(f.read())
        
        

class JVM(ByteVM):
    """
    an implementation of the JVM.

    TODO this is very incomplete

    The hope is to be able to load actual class files from javac, inspect with .decompile(), and run them with visualizations.

    see also
        jvm.csv
        jvm_builder.py
        https://en.wikipedia.org/wiki/List_of_Java_bytecode_instructions
    """
    def __init__(self, ast:node|bytes|bytearray|None=None):
        super().__init__(ast)
        self.arrays:list[list] = []

    # HELPERS
    def loadclass(self, classfile):
        raise NotImplemented
    # java struct types to struct format specifiers
    structs = {
            'byte'  :('c', struct.calcsize('c')),
            'short' :('h', struct.calcsize('h')),
            'int'   :('i', struct.calcsize('i')),
            'long'  :('q', struct.calcsize('q')),
            'float' :('f', struct.calcsize('f')),
            'double':('d', struct.calcsize('d')),
            'bool'  :('?', struct.calcsize('?')),
            'char'  :('', struct.calcsize('')), # not sure here, 2 bytes per character?
            }
    def spush(self, kind, value):
        """push struct"""
        fmt, size = self.structs[kind]
        struct.pack_into(fmt, self.stack, self.SP, value)
        self.SP += size

    def spop(self, kind):
        """pop struct"""
        fmt, size = self.structs[kind]
        self.SP -= size
        return struct.unpack_from(fmt, self.stack, self.SP)

    def ipopidx(self):
        idx = self.ipop() << 8
        idx += self.ipop()
        return idx

    # OPCODES

    @opcode(0x32)
    def aaload(self):
        """Load onto the stack a reference from an array."""
        index = self.pop()
        arrayref = self.pop()
        value = self.arrays[arrayref][index]
        self.push(value)


    @opcode(0x53)
    def aastore(self):
        """Store a reference in an array."""
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()
        self.arrays[arrayref][index] = value



    @opcode(0x01)
    def aconst_null(self):
        """Push a null reference onto the stack."""
        self.push(0)


    @opcode(0x19, 'B')
    def aload(self, index):
        """Load a reference onto the stack from a local variable #index."""
        # TODO
        self.push(objectref)


    @opcode(0x2a)
    def aload_0(self):
        """Load a reference onto the stack from local variable 0."""
        # TODO
        self.push(objectref)


    @opcode(0x2b)
    def aload_1(self):
        """Load a reference onto the stack from local variable 1."""
        # TODO
        self.push(objectref)


    @opcode(0x2c)
    def aload_2(self):
        """Load a reference onto the stack from local variable 2."""
        # TODO
        self.push(objectref)


    @opcode(0x2d)
    def aload_3(self):
        """Load a reference onto the stack from local variable 3."""
        # TODO
        self.push(objectref)


    @opcode(0xbd, 'h')
    def anewarray(self, index):
        """Create a new array of references of length count and component type identified by the class reference index (indexbyte1 << 8 | indexbyte2) in the constant pool."""
        # TODO
        count = self.pop()
        self.push(arrayref)


    @opcode(0xb0)
    def areturn(self):
        """Return a reference from a method."""
        # TODO
        objectref = self.pop()
        self.SP = 0


    @opcode(0xbe)
    def arraylength(self):
        """Get the length of an array."""
        # TODO
        arrayref = self.pop()
        self.push(length)


    @opcode(0x3a, 'B')
    def astore(self, index):
        """Store a reference into a local variable #index."""
        # TODO
        objectref = self.pop()


    @opcode(0x4b)
    def astore_0(self):
        """Store a reference into local variable 0."""
        # TODO
        objectref = self.pop()


    @opcode(0x4c)
    def astore_1(self):
        """Store a reference into local variable 1."""
        # TODO
        objectref = self.pop()


    @opcode(0x4d)
    def astore_2(self):
        """Store a reference into local variable 2."""
        # TODO
        objectref = self.pop()


    @opcode(0x4e)
    def astore_3(self):
        """Store a reference into local variable 3."""
        # TODO
        objectref = self.pop()


    @opcode(0xbf)
    def athrow(self):
        """Throws an error or exception (notice that the rest of the stack is cleared, leaving only a reference to the throwable)."""
        # TODO
        objectref = self.pop()
        self.SP = 0
        self.push(objectref)


    @opcode(0x33)
    def baload(self):
        """Load a byte or boolean value from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x54)
    def bastore(self):
        """Store a byte or boolean value into an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x10, 'b')
    def bipush(self, byte):
        """Push a byte onto the stack as an integer value."""
        # TODO
        self.push(value)


    @opcode(0xca)
    def breakpoint(self):
        """Reserved for breakpoints in java debuggers; should not appear in any class file."""
        # TODO



    @opcode(0x34)
    def caload(self):
        """Load a char from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x55)
    def castore(self):
        """Store a char into an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0xc0, 'h')
    def checkcast(self, index):
        """Checks whether an objectref is of a certain type, the class reference of which is in the constant pool at index (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        objectref = self.pop()
        self.push(objectref)


    @opcode(0x90)
    def d2f(self):
        """Convert a double to a float."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x8e)
    def d2i(self):
        """Convert a double to an int."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x8f)
    def d2l(self):
        """Convert a double to a long."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x63)
    def dadd(self):
        """Add two doubles."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x31)
    def daload(self):
        """Load a double from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x52)
    def dastore(self):
        """Store a double into an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x98)
    def dcmpg(self):
        """Compare two doubles, 1 on nan."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x97)
    def dcmpl(self):
        """Compare two doubles, -1 on nan."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x0e)
    def dconst_0(self):
        """Push the constant 0.0 (a double) onto the stack."""
        # TODO
        self.push(0.0)


    @opcode(0x0f)
    def dconst_1(self):
        """Push the constant 1.0 (a double) onto the stack."""
        # TODO
        self.push(1.0)


    @opcode(0x6f)
    def ddiv(self):
        """Divide two doubles."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x18, 'd')
    def dload(self, index):
        """Load a double value from a local variable #index."""
        # TODO
        self.push(value)


    @opcode(0x26)
    def dload_0(self):
        """Load a double from local variable 0."""
        # TODO
        self.push(value)


    @opcode(0x27)
    def dload_1(self):
        """Load a double from local variable 1."""
        # TODO
        self.push(value)


    @opcode(0x28)
    def dload_2(self):
        """Load a double from local variable 2."""
        # TODO
        self.push(value)


    @opcode(0x29)
    def dload_3(self):
        """Load a double from local variable 3."""
        # TODO
        self.push(value)


    @opcode(0x6b)
    def dmul(self):
        """Multiply two doubles."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x77)
    def dneg(self):
        """Negate a double."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x73)
    def drem(self):
        """Get the remainder from a division between two doubles."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xaf)
    def dreturn(self):
        """Return a double from a method."""
        # TODO
        value = self.pop()
        self.SP = 0


    @opcode(0x39, 'd')
    def dstore(self, index):
        """Store a double value into a local variable #index."""
        # TODO
        value = self.pop()


    @opcode(0x47)
    def dstore_0(self):
        """Store a double into local variable 0."""
        # TODO
        value = self.pop()


    @opcode(0x48)
    def dstore_1(self):
        """Store a double into local variable 1."""
        # TODO
        value = self.pop()


    @opcode(0x49)
    def dstore_2(self):
        """Store a double into local variable 2."""
        # TODO
        value = self.pop()


    @opcode(0x4a)
    def dstore_3(self):
        """Store a double into local variable 3."""
        # TODO
        value = self.pop()


    @opcode(0x67)
    def dsub(self):
        """Subtract a double from another."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x59)
    def dup(self):
        """Duplicate the value on top of the stack."""
        # TODO
        value = self.pop()
        self.push(value)
        self.push(value)


    @opcode(0x5a)
    def dup_x1(self):
        """Insert a copy of the top value into the stack two values from the top. value1 and value2 must not be of the type double or long.."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        self.push(value1)
        self.push(value2)
        self.push(value1)


    @opcode(0x5b)
    def dup_x2(self):
        """Insert a copy of the top value into the stack two (if value2 is double or long it takes up the entry of value3, too) or three values (if value2 is neither double nor long) from the top."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        value3 = self.pop()
        self.push(value1)
        self.push(value3)
        self.push(value2)
        self.push(value1)


    @opcode(0x5c)
    def dup2(self):
        """Duplicate top two stack words (two values, if value1 is not double nor long; a single value, if value1 is double or long)."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        self.push(value2)
        self.push(value1)
        self.push(value2)
        self.push(value1)


    @opcode(0x5d)
    def dup2_x1(self):
        """Duplicate two words and insert beneath third word (see explanation above)."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        value3 = self.pop()
        self.push(value2)
        self.push(value1)
        self.push(value3)
        self.push(value2)
        self.push(value1)


    @opcode(0x5e)
    def dup2_x2(self):
        """Duplicate two words and insert beneath fourth word."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        value3 = self.pop()
        value4 = self.pop()
        self.push(value2)
        self.push(value1)
        self.push(value4)
        self.push(value3)
        self.push(value2)
        self.push(value1)


    @opcode(0x8d)
    def f2d(self):
        """Convert a float to a double."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x8b)
    def f2i(self):
        """Convert a float to an int."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x8c)
    def f2l(self):
        """Convert a float to a long."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x62)
    def fadd(self):
        """Add two floats."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x30)
    def faload(self):
        """Load a float from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x51)
    def fastore(self):
        """Store a float in an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x96)
    def fcmpg(self):
        """Compare two floats, 1 on nan."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x95)
    def fcmpl(self):
        """Compare two floats, -1 on nan."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x0b)
    def fconst_0(self):
        """Push 0.0f on the stack."""
        # TODO
        self.push(0.0, 'f')


    @opcode(0x0c)
    def fconst_1(self):
        """Push 1.0f on the stack."""
        # TODO
        self.push(1.0, 'f')


    @opcode(0x0d)
    def fconst_2(self):
        """Push 2.0f on the stack."""
        # TODO
        self.push(2.0, 'f')


    @opcode(0x6e)
    def fdiv(self):
        """Divide two floats."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x17, 'f')
    def fload(self, index):
        """Load a float value from a local variable #index."""
        # TODO
        self.push(value)


    @opcode(0x22)
    def fload_0(self):
        """Load a float value from local variable 0."""
        # TODO
        self.push(value)


    @opcode(0x23)
    def fload_1(self):
        """Load a float value from local variable 1."""
        # TODO
        self.push(value)


    @opcode(0x24)
    def fload_2(self):
        """Load a float value from local variable 2."""
        # TODO
        self.push(value)


    @opcode(0x25)
    def fload_3(self):
        """Load a float value from local variable 3."""
        # TODO
        self.push(value)


    @opcode(0x6a)
    def fmul(self):
        """Multiply two floats."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x76)
    def fneg(self):
        """Negate a float."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x72)
    def frem(self):
        """Get the remainder from a division between two floats."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xae)
    def freturn(self):
        """Return a float."""
        # TODO
        value = self.pop()
        self.SP = 0


    @opcode(0x38, 'f')
    def fstore(self, index):
        """Store a float value into a local variable #index."""
        # TODO
        value = self.pop()


    @opcode(0x43)
    def fstore_0(self):
        """Store a float value into local variable 0."""
        # TODO
        value = self.pop()


    @opcode(0x44)
    def fstore_1(self):
        """Store a float value into local variable 1."""
        # TODO
        value = self.pop()


    @opcode(0x45)
    def fstore_2(self):
        """Store a float value into local variable 2."""
        # TODO
        value = self.pop()


    @opcode(0x46)
    def fstore_3(self):
        """Store a float value into local variable 3."""
        # TODO
        value = self.pop()


    @opcode(0x66)
    def fsub(self):
        """Subtract two floats."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xb4, 'h')
    def getfield(self, index):
        """Get a field value of an object objectref, where the field is identified by field reference in the constant pool index (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        objectref = self.pop()
        self.push(value)


    @opcode(0xb2, 'h')
    def getstatic(self, index):
        """Get a static field value of a class, where the field is identified by field reference in the constant pool index (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        self.push(value)


    @opcode(0xa7, 'h')
    def goto(self, branch):
        """Goes to another instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO



    @opcode(0xc8, 'L')
    def goto_w(self, branch):
        """Goes to another instruction at branchoffset (signed int constructed from unsigned bytes branchbyte1 << 24 | branchbyte2 << 16 | branchbyte3 << 8 | branchbyte4)."""
        # TODO



    @opcode(0x91)
    def i2b(self):
        """Convert an int into a byte."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x92)
    def i2c(self):
        """Convert an int into a character."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x87)
    def i2d(self):
        """Convert an int into a double."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x86)
    def i2f(self):
        """Convert an int into a float."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x85)
    def i2l(self):
        """Convert an int into a long."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x93)
    def i2s(self):
        """Convert an int into a short."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x60)
    def iadd(self):
        """Add two ints."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x2e)
    def iaload(self):
        """Load an int from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x7e)
    def iand(self):
        """Perform a bitwise and on two integers."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x4f)
    def iastore(self):
        """Store an int into an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x02)
    def iconst_m1(self):
        """Load the int value −1 onto the stack."""
        # TODO
        self.push(-1)


    @opcode(0x03)
    def iconst_0(self):
        """Load the int value 0 onto the stack."""
        # TODO
        self.push(0)


    @opcode(0x04)
    def iconst_1(self):
        """Load the int value 1 onto the stack."""
        # TODO
        self.push(1)


    @opcode(0x05)
    def iconst_2(self):
        """Load the int value 2 onto the stack."""
        # TODO
        self.push(2)


    @opcode(0x06)
    def iconst_3(self):
        """Load the int value 3 onto the stack."""
        # TODO
        self.push(3)


    @opcode(0x07)
    def iconst_4(self):
        """Load the int value 4 onto the stack."""
        # TODO
        self.push(4)


    @opcode(0x08)
    def iconst_5(self):
        """Load the int value 5 onto the stack."""
        # TODO
        self.push(5)


    @opcode(0x6c)
    def idiv(self):
        """Divide two integers."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xa5, 'h')
    def if_acmpeq(self, branch):
        """If references are equal, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa6, 'h')
    def if_acmpne(self, branch):
        """If references are not equal, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0x9f, 'h')
    def if_icmpeq(self, branch):
        """If ints are equal, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa2, 'h')
    def if_icmpge(self, branch):
        """If value1 is greater than or equal to value2, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa3, 'h')
    def if_icmpgt(self, branch):
        """If value1 is greater than value2, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa4, 'h')
    def if_icmple(self, branch):
        """If value1 is less than or equal to value2, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa1, 'h')
    def if_icmplt(self, branch):
        """If value1 is less than value2, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0xa0, 'h')
    def if_icmpne(self, branch):
        """If ints are not equal, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()


    @opcode(0x99, 'h')
    def ifeq(self, branch):
        """If value is 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x9c, 'h')
    def ifge(self, branch):
        """If value is greater than or equal to 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x9d, 'h')
    def ifgt(self, branch):
        """If value is greater than 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x9e, 'h')
    def ifle(self, branch):
        """If value is less than or equal to 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x9b, 'h')
    def iflt(self, branch):
        """If value is less than 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x9a, 'h')
    def ifne(self, branch):
        """If value is not 0, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0xc7, 'h')
    def ifnonnull(self, branch):
        """If value is not null, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0xc6, 'h')
    def ifnull(self, branch):
        """If value is null, branch to instruction at branchoffset (signed short constructed from unsigned bytes branchbyte1 << 8 | branchbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0x84, 'Bb')
    def iinc(self, index, const):
        """Increment local variable #index by signed byte const."""
        # TODO



    @opcode(0x15, 'B')
    def iload(self, index):
        """Load an int value from a local variable #index."""
        # TODO
        self.push(value)


    @opcode(0x1a)
    def iload_0(self):
        """Load an int value from local variable 0."""
        # TODO
        self.push(value)


    @opcode(0x1b)
    def iload_1(self):
        """Load an int value from local variable 1."""
        # TODO
        self.push(value)


    @opcode(0x1c)
    def iload_2(self):
        """Load an int value from local variable 2."""
        # TODO
        self.push(value)


    @opcode(0x1d)
    def iload_3(self):
        """Load an int value from local variable 3."""
        # TODO
        self.push(value)


    @opcode(0xfe)
    def impdep1(self):
        """Reserved for implementation-dependent operations within debuggers; should not appear in any class file."""
        # TODO



    @opcode(0xff)
    def impdep2(self):
        """Reserved for implementation-dependent operations within debuggers; should not appear in any class file."""
        # TODO



    @opcode(0x68)
    def imul(self):
        """Multiply two integers."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x74)
    def ineg(self):
        """Negate int."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0xc1, 'h')
    def instanceof(self, index):
        """Determines if an object objectref is of a given type, identified by class reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        objectref = self.pop()
        self.push(result)


    @opcode(0xba, 'h')
    def invokedynamic(self, index):
        """Invokes a dynamic method and puts the result on the stack (might be void); the method is identified by method reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        for_count = self.pop()
        arg2 = self.pop()
        arg1 = self.pop()
        self.push(result)


    @opcode(0xb9, 'hB')
    def invokeinterface(self, index, count):
        """Invokes an interface method on object objectref and puts the result on the stack (might be void); the interface method is identified by method reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        for_count = self.pop()
        arg2 = self.pop()
        arg1 = self.pop()
        objectref = self.pop()
        self.push(result)


    @opcode(0xb7, 'h')
    def invokespecial(self, index):
        """Invoke instance method on object objectref and puts the result on the stack (might be void); the method is identified by method reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        for_count = self.pop()
        arg2 = self.pop()
        arg1 = self.pop()
        objectref = self.pop()
        self.push(result)


    @opcode(0xb8, 'h')
    def invokestatic(self, index):
        """Invoke a static method and puts the result on the stack (might be void); the method is identified by method reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        for_count = self.pop()
        arg2 = self.pop()
        arg1 = self.pop()
        self.push(result)


    @opcode(0xb6, 'h')
    def invokevirtual(self, index):
        """Invoke virtual method on object objectref and puts the result on the stack (might be void); the method is identified by method reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        for_count = self.pop()
        arg2 = self.pop()
        arg1 = self.pop()
        objectref = self.pop()
        self.push(result)


    @opcode(0x80)
    def ior(self):
        """Bitwise int or."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x70)
    def irem(self):
        """Logical int remainder."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xac)
    def ireturn(self):
        """Return an integer from a method."""
        # TODO
        value = self.pop()
        self.SP = 0


    @opcode(0x78)
    def ishl(self):
        """Int shift left."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x7a)
    def ishr(self):
        """Int arithmetic shift right."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x36, 'B')
    def istore(self, index):
        """Store int value into variable #index."""
        # TODO
        value = self.pop()


    @opcode(0x3b)
    def istore_0(self):
        """Store int value into variable 0."""
        # TODO
        value = self.pop()


    @opcode(0x3c)
    def istore_1(self):
        """Store int value into variable 1."""
        # TODO
        value = self.pop()


    @opcode(0x3d)
    def istore_2(self):
        """Store int value into variable 2."""
        # TODO
        value = self.pop()


    @opcode(0x3e)
    def istore_3(self):
        """Store int value into variable 3."""
        # TODO
        value = self.pop()


    @opcode(0x64)
    def isub(self):
        """Int subtract."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x7c)
    def iushr(self):
        """Int logical shift right."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x82)
    def ixor(self):
        """Int xor."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x8a)
    def l2d(self):
        """Convert a long to a double."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x89)
    def l2f(self):
        """Convert a long to a float."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x88)
    def l2i(self):
        """Convert a long to a int."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0x61)
    def ladd(self):
        """Add two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x2f)
    def laload(self):
        """Load a long from an array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x7f)
    def land(self):
        """Bitwise and of two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x50)
    def lastore(self):
        """Store a long to an array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x94)
    def lcmp(self):
        """Push 0 if the two longs are the same, 1 if value1 is greater than value2, -1 otherwise."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x09)
    def lconst_0(self):
        """Push 0l (the number zero with type long) onto the stack."""
        # TODO
        self.push(0, 'l')


    @opcode(0x0a)
    def lconst_1(self):
        """Push 1l (the number one with type long) onto the stack."""
        # TODO
        self.push(1, 'l')


    @opcode(0x12, 'B')
    def ldc(self, index):
        """Push a constant #index from a constant pool (string, int, float, class, java.lang.invoke.methodtype, java.lang.invoke.methodhandle, or a dynamically-computed constant) onto the stack."""
        # TODO
        self.push(value)


    @opcode(0x13, 'h')
    def ldc_w(self, index):
        """Push a constant #index from a constant pool (string, int, float, class, java.lang.invoke.methodtype, java.lang.invoke.methodhandle, or a dynamically-computed constant) onto the stack (wide index is constructed as indexbyte1 << 8 | indexbyte2)."""
        # TODO
        self.push(value)


    @opcode(0x14, 'h')
    def ldc2_w(self, index):
        """Push a constant #index from a constant pool (double, long, or a dynamically-computed constant) onto the stack (wide index is constructed as indexbyte1 << 8 | indexbyte2)."""
        # TODO
        self.push(value)


    @opcode(0x6d)
    def ldiv(self):
        """Divide two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x16, 'B')
    def lload(self, index):
        """Load a long value from a local variable #index."""
        # TODO
        self.push(value, 'l')


    @opcode(0x1e)
    def lload_0(self):
        """Load a long value from a local variable 0."""
        # TODO
        self.push(value)


    @opcode(0x1f)
    def lload_1(self):
        """Load a long value from a local variable 1."""
        # TODO
        self.push(value)


    @opcode(0x20)
    def lload_2(self):
        """Load a long value from a local variable 2."""
        # TODO
        self.push(value)


    @opcode(0x21)
    def lload_3(self):
        """Load a long value from a local variable 3."""
        # TODO
        self.push(value)


    @opcode(0x69)
    def lmul(self):
        """Multiply two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x75)
    def lneg(self):
        """Negate a long."""
        # TODO
        value = self.pop()
        self.push(result)


    @opcode(0xab, 'LLB')
    def lookupswitch(self, default, npairs, matchpairs):
        """A target address is looked up from a table using a key and execution continues from the instruction at that address."""
        # TODO
        key = self.pop()


    @opcode(0x81)
    def lor(self):
        """Bitwise or of two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x71)
    def lrem(self):
        """Remainder of division of two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xad)
    def lreturn(self):
        """Return a long value."""
        # TODO
        value = self.pop()
        self.SP = 0


    @opcode(0x79)
    def lshl(self):
        """Bitwise shift left of a long value1 by int value2 positions."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x7b)
    def lshr(self):
        """Bitwise shift right of a long value1 by int value2 positions."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x37, 'B')
    def lstore(self, index):
        """Store a long value in a local variable #index."""
        # TODO
        value = self.pop()


    @opcode(0x3f)
    def lstore_0(self):
        """Store a long value in a local variable 0."""
        # TODO
        value = self.pop()


    @opcode(0x40)
    def lstore_1(self):
        """Store a long value in a local variable 1."""
        # TODO
        value = self.pop()


    @opcode(0x41)
    def lstore_2(self):
        """Store a long value in a local variable 2."""
        # TODO
        value = self.pop()


    @opcode(0x42)
    def lstore_3(self):
        """Store a long value in a local variable 3."""
        # TODO
        value = self.pop()


    @opcode(0x65)
    def lsub(self):
        """Subtract two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x7d)
    def lushr(self):
        """Bitwise shift right of a long value1 by int value2 positions, unsigned."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0x83)
    def lxor(self):
        """Bitwise xor of two longs."""
        # TODO
        value2 = self.pop()
        value1 = self.pop()
        self.push(result)


    @opcode(0xc2)
    def monitorenter(self):
        """Enter monitor for object ("grab the lock" – start of synchronized() section)."""
        # TODO
        objectref = self.pop()


    @opcode(0xc3)
    def monitorexit(self):
        """Exit monitor for object ("release the lock" – end of synchronized() section)."""
        # TODO
        objectref = self.pop()


    @opcode(0xc5, 'hB')
    def multianewarray(self, index, dimensions):
        """Create a new array of dimensions dimensions of type identified by class reference in constant pool index (indexbyte1 << 8 | indexbyte2); the sizes of each dimension is identified by count1, [count2, etc.]."""
        # TODO
        for_count = self.pop()
        count2 = self.pop()
        count1 = self.pop()
        self.push(arrayref)


    @opcode(0xbb, 'h')
    def new(self, index):
        """Create new object of type identified by class reference in constant pool index (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        self.push(objectref)


    @opcode(0xbc, 'B')
    def newarray(self, atype):
        """Create new array with count elements of primitive type identified by atype."""
        # TODO
        count = self.pop()
        self.push(arrayref)


    @opcode(0x00)
    def nop(self):
        """Perform no operation."""
        # TODO



    @opcode(0x57)
    def pop(self):
        """Discard the top value on the stack."""
        return super().pop()


    @opcode(0x58)
    def pop2(self):
        """Discard the top two values on the stack (or one value, if it is a double or long)."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()


    @opcode(0xb5, 'h')
    def putfield(self, index):
        """Set field to value in an object objectref, where the field is identified by a field reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        value = self.pop()
        objectref = self.pop()


    @opcode(0xb3, 'h')
    def putstatic(self, index):
        """Set static field to value in a class, where the field is identified by a field reference index in constant pool (indexbyte1 << 8 | indexbyte2)."""
        # TODO
        value = self.pop()


    @opcode(0xb1)
    def return_(self):
        """Return void from method."""
        # TODO
        self.SP = 0


    @opcode(0x35)
    def saload(self):
        """Load short from array."""
        # TODO
        index = self.pop()
        arrayref = self.pop()
        self.push(value)


    @opcode(0x56)
    def sastore(self):
        """Store short to array."""
        # TODO
        value = self.pop()
        index = self.pop()
        arrayref = self.pop()


    @opcode(0x11, 'h')
    def sipush(self, value):
        """Push a short onto the stack as an integer value."""
        # TODO
        self.push(value)


    @opcode(0x5f)
    def swap(self):
        """Swaps two top words on the stack (note that value1 and value2 must not be double or long)."""
        # TODO
        value1 = self.pop()
        value2 = self.pop()
        self.push(value1)
        self.push(value2)


    @opcode(0xaa, 'LLLB')
    def tableswitch(self, default, lowbyte,highbyte, jumpoffsets):
        """Continue execution from an address in the table at offset index."""
        # TODO
        index = self.pop()


    @opcode(0xc4, 'Bh')
    def wide(self, opcode, index):
        """
        Execute opcode.

        where opcode is either iload, fload, aload, lload, dload, istore, fstore, astore, lstore, dstore, or ret
        but assume the index is 16 bit.

        or execute iinc, where the index is 16 bits and the constant to increment by is a signed 16 bit short."""
        # TODO


if __name__ == "__main__":
    c = Class.from_file('HelloWorld.class')
    print(c.magic)
    print(c.minor_version)
    print(c.major_version)
    print(c.constant_pool_count)
    with open('HelloWorld.class', 'rb') as f:
        vm = JVM(f.read())
        print(vm.decompile())
