# Arno
Arno is a new programming language

# why
* baby's first virtual machine (register based)
* write it in rust
* statically typed
* can't stop, won't stop the scope creep

# VM semantics
* vm native types:
    * value - a tagged union of any type (except value)
    * rune (utf-8 encoded character)
    * int
    * float
    * function
    * table - associative arrays like lua, but typed keys and values
    * nil    - only a single value
    * thread - coroutine (possibly parallel)
    * chan - threadsafe typed fifo
    * type

* static-ish typing (must handle all branches for value)
* single branching control
* single looping control
* generic functions, compile on use
* multiple dispatch for global functions based on type (and inplace variants)
    * use gleams rules for extern
* tail call optimization

# syntax
what does it look like
* DeBruijn variables for partials/ freevars (gleam) `_` == `_0`, `_1`, `_2`, ...
* pipe operator (gleam)
    * an expression `x|sort()` => `sort(x)`
    * a  statement  `x|sort()` => `x = sort(x)`
    * `x|func(a, _, c)` => `func(a, x, c)`
* branch `?`
* loop `@`
* import (buy) `$`
* extern `$$`
```
fib(x:int):int {
    return ? x { # must explicitly return from functions
                 # blocks can implicitly return (when used as an expression)
        :0 or 1: 1 # anything between colons is the condition
        : _ < 0: 0 # using a freevar will eval
        ::fib(x-1) # default case
    }
}

# generic function
# this actually fails to compare int and float, since type(a) == type(b)
min<T>(a:T,b:T): {
    ? a < b; return a # can return early with 'return'
    b # implicitly return last expression
}

# function that returns a sorted table
sort(x:table):table {...}
# inplace variant. the passed type isn't actually different
sort(x:&table) {...}
# external function variant (for rust backend)
$rust 'path/to/file' sort and other funcs
# native library variant, renaming symbol to sort
$path/from/root sortTable as sort
```


# driver
command line options:
* -- with no arguments, open a repl session
* -o outfile -- save output to given filename, rather than generating a name
* source.ar|byte.no|dir|url|- ...
    * add a root if directory, compile if source, add runtime if byte
    * if a directory or url is given, add as a root
    * if only roots are given, then target `main.ar`
    * by default, save all intermediate steps and then run the generated binary
* -R -- ignore all previous roots
* -i -- don't save intermediate files, just run
    * with no other arguments, open repl and save history to `.arno_hist`
* -b -- compiles to bytecode, but don't add a runtime or run
* -c -- compiles to binary, but don't run
* -h -- print help
* -H histfile -- save repl history to histfile rather than `.arno_hist`
* -t count -- allow up to count system threads
* --clean -- remove intermediate files (incremental builds by default)

environment vars
* `ARNO_CACHE` - directory for cached arno libraries (default? `$XDG_CACHE_HOME/arno/` or `~/.cache/arno/`)
* `ARNO_ROOTS` - a list of urls to fetch code from (default? `https:github.com/,`)
* `ARNO_VER`, `ARNO_OS`, `ARNO_ARCH` - enable cross compiling (default `system`)


gitignore
```
main
*.no
.arno_hist
```

examples
```
arno . -o outfile # compile main.ar to binary as outfile in the current directory
arno -b ./*.ar # compile all *.ar in the current directory to bytecode
anro # start a repl session
```
# loader
where does code come from?
* `ARNO_ROOTS`, directory arguments or `-r` options specify locations for library code
* `ARNO_CACHE` - a local cache of remote roots
* `*.ar` - source files
* `*.no` - bytecode files (magic bytes `0x00babb1e`)
* [no ext] - binary files (runtime packaged with bytecode)

# parser
handwritten, check against trPEG

# compiler
compiles source to bytecode

# linker
Lines up externs between bytecode files
then combines runtime with bytecode.

# REPL
* gnu readline?
* save history

# VM implementation
Some details should be invisible to the user of the VM.

numeric types have size variants, maybe, or just fail on overflow
* smallint? immediate value for ints ~0 [-1, 3]
* int - u{8,16,32,64,128} i{8,16,32,64,128}
* float - f{32,64,128}

table may have alternative implementations based on key and value types.
(lua hashmap vs array).

coroutines or system thread? let the runtime (or compiler flags) decide

* cloze on return (when function escapes local scope lifetime), otherwise stack reference for nonlocal vars

# reference
* [lua 5.0 paper](https://www.lua.org/doc/jucs05.pdf)
* [pl](https://toombs-caeman.github.io/pl)
* [XDG directory spec](https://specifications.freedesktop.org/basedir-spec/latest/)
* [magic words](https://nedbatchelder.com/text/hexwords.html)
