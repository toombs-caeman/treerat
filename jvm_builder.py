import csv
import re
"""
Load the wikipedia table for javas bytecode instructions and generate python code for a ByteVM class

https://en.wikipedia.org/wiki/List_of_Java_bytecode_instructions
"""
# examples: "1: var", "2: var1, var2"
otherbytes = re.compile(r'[a-zA-Z][a-zA-Z0-9]+')
# example "value → result"
stackop = re.compile(r'$|')

# example 0.0f
number = re.compile('^([0-9.]+)([a-zA-Z])$')

with open('jvm.csv') as f:
    tab = csv.reader(f, delimiter='\t')
    for name, opcode, _, other, stack, description in tab:
        name = name.strip()
        # return is a reserved word so we cannot directly name a function this.
        if name == 'return':
            name = 'return_'
        opcode = opcode.strip()


        # parse arguments and argument format string from other
        opargs = []
        fargs = ['self']
        for match in otherbytes.finditer(other):
            arg = match.group()
            match arg:
                case 'indexbyte1'|'branchbyte1':
                    opargs.append('h')
                    fargs.append(arg[:-5])
                case 'indexbyte2'|'branchbyte2':
                    pass
                case '0':
                    opargs.append('x')
                case 'count':
                    opargs.append('B')
                    fargs.append(arg)
                case _:
                    # u for unknown, this isn't a valid format
                    opargs.append('u')
                    fargs.append(arg)
        opargs = f"0x{opcode}, {''.join(opargs)!r}" if opargs else f"0x{opcode}"
        fargs = ', '.join(fargs)

        body = []
        # stack operations
        if '→' in stack:
            pop, push = stack.split('→')
            for var in reversed(pop.split(',')):
                var = var.strip(' []')
                if var == '...':
                    var = 'for_count'
                if var:
                    body.append(f"{var} = self.pop()")
            for var in push.split(', '):
                var = var.strip()
                if not var:
                    continue
                if (M := number.match(var)):
                    v, f = M.groups()
                    body.append(f'self.push({v}, {f.lower()!r})')
                    continue
                if var == '[empty]':
                    body.append('self.SP = 0')
                    continue
                body.append(f'self.push({var})')

        # make description nice
        description = description.strip().capitalize() + '.'


        ident = '        '
        print(f'''
    @opcode({opargs})
    def {name.strip()}({fargs}):
        """{description}"""
        # TODO
{"\n".join(ident + x for x in body)}
''')
