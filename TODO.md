# layercake
## forth (ANSI C -> cf)
* set up nvim for hex editing
    * [syntax highlighter](https://news.ycombinator.com/item?id=47846688)
    * [hex.nvim](https://github.com/RaafatTurki/hex.nvim)
    * xxd
* minimal forth
    * [jonesforth](https://github.com/nornagon/jonesforth/blob/master/jonesforth.S)
    * [ansi c port](https://gist.github.com/lbruder/10007431)
* add 'sus' and 'sus2 (filename --)' word (suspend)
    * dumps program state as an executable program to stdout then exits
    * include stack, dictionary, heap, etc.
* add 'eputc' output to stderr
* read/write file
* the self hosting compiler is just a normal program
    * `: main ... ; sus main exit`)
    * `forthc program.forth > program`

* add heap objects
    * the heap also needs to be suspended
    * [malloc/free](https://danluu.com/malloc-tutorial/)
    * tagged union
    * tagged pointer?
    * sized homogenous array
    * hashmap
    * set
    * ring buffer
    * result(ok/err)
    * string?
    * word dict as a type?

* add (external) testing rig
    * make?
    * write tests for cf

## forth advanced (ANSI C -> cf)
* set up external testing rig?
* add 'trimwords'
    * used to compact word dictionary
    * eliminate any word not reachable from a set marked to keep
    * `: finalize 'main' trim sus main exit ;`
* add the stuff using c libraries that would be annoying to implement myself
    * unicode char support?
    * threads and threadsafe primitives
    * interrupt handling?
* chan (ring with mutex)
* async / coroutines
* arena allocators
    * [wiki?](https://en.wikipedia.org/wiki/Region-based_memory_management)
    * clean up all allocated objects at once
    * need a way to move objects out to the general heap
* write tests for advanced features

## language utils (cf -> rv)
* define ast datatype
    * treewalk `: eval (ast --)`
* add a pika parser `: pika (grammar str -- result<ast>)`
    * define as alternate word dictionaries?
    * at this point we probably want to abandon forth syntax
    * lets call the new language 'red velvet' or 'rv'
* format for name resolution
    * `: resolve (ast -- egg)`
* add egraphs (might need to dip into c for this)
    * see egglog
    * `: saturate (egg -- egg)`
    * `: typecheck (egg rules -- egg)`
* type checking algo?
* write tests

From this point on, this will be the 
from this point on, language definitions can easily be done in rv


#
* parser
    * one final push on getting pika and packrat to parity, pika needs rework
    * animation/visualization
* types
    * what they do

* graphs
    * create generic graph rewriting DSL?
        * extract from grammar normalizer
    * https://egraphs-good.github.io/
