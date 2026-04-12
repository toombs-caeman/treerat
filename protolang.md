This is a language framework specifically meant to do much of the heavy lifting for creating a new programming language.

Written in rust.

* defines a tokenizer syntax
    * user must provide token definitions for their language
* defines a grammar syntax
    * user must provide a grammar definition
* provides a tree walk interpreter
    * user must define evaluation for each node in rust
* provides [LSP](https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/)
    * syntax highlighting
    * jump to definition
* provides [DAP](https://microsoft.github.io/debug-adapter-protocol/) compatible debugger
    * step through tree walk
* provides REPL
