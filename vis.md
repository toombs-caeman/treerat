# Compilers
Computers are extremely fast, but can actually only follow extremely basic instructions.
When we want the computer to do more complex tasks, we have to define these tasks in terms of the basic instructions.
However, doing this by hand is tedious, so programming languages were created to translate between the simplified way the user would like to explain the task and the extremely detailed instructions that the computer needs to operate.

A program which does this translation of a language and saves the result for later (as an executable) is called a compiler.
If the program instead immediately tells the machine to do the task, it is usually called an interpreter, though the distinction between a compiler and an interpreter is pretty fuzzy actually. I'll use the terms pretty interchaneably here.

Compilers must produce fast and correct instructions, while still allowing the source language to be as expressive as possible, but these qualities are often in conflict with each other. This has resulted in a long academic tradition studying compilers. While necessary for performance critical applications (and to enable more complex languages), the long tradition and niche terminology can make the topic unapproachable or 'magical', when really the core of the topic is extremely simple.

In this post I'd like to walk through the major components of a compiler, and allow you, the reader, to design and run your own language right here in the browser.

## sections
* define grammar / parser
    * parsing expression grammars
    * define grammar
    * show resulting parser definition
* example in the source langauge
    * syntax highlighting
    * AST
* define node evaluators
* tree walk interpreters

# What is a Grammar
The input or source code which a compiler processes is just text, but not all text will be meaningful in this context.
The "grammar" of a language defines what shapes of text are allowed to be meaningful.

For example in math, the expression `1 + 2` is meaningful, but `1 + * /` is not. `x + 1` may be meaningful since it does follow the mathematical grammar, but it only actually has meaning if `x` is defined.

The fact that the grammar defines what "might be meaningful" and "what definitely isn't meaningful" might seem strange, but it defining this kind of interface allows for grammars to be used very efficiently.


## example grammar
```grammar
stmt    : print / assign
%print  : 'print' %expr
%assign : %var '=' %expr

expr    : (mul / div) / (add / sub) / var / val / group
%group  : '(' %expr ')'
%mul    : %expr.1 '*' %expr
%div    : %expr.1 '/' %expr
%add    : %expr.2 '+' %expr
%sub    : %expr.2 '-' %expr
%var    : %[a-z]+
%val    : %('-'? [0-9]+ ('.' [0-9]*)?)

%main   : ('\n' | %expr '\n')*
space   : ' ' {skip}
```

# define grammar
> generate syntax highlighter
# write code
> generate syntax tree
# define vm in js
state + implementation for each node
> vis the tree walk (vm state, current node, scrub)
# define binpack for each node
> vis bytecode vm (vm stae, instruction pointer, scrub)
