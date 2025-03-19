# binary format
* magic number
* spec version
* language name
* interpreter version
    * either another treerat transformation
    * or an external language that's the transpiled target
    * this is wrong
* driver rules - what command line arguments does the compiler support, what are the entrypoints
* loader rules - where does source and other data come from
* grammar rules - parse source code into commands for parse-time interpreter
* interpreters
    * front-end - receive commands and emit IR fragments
    * middle-end - receive complete IR and emit built object
        * this is intended to be compatible with llvm
        * the language could specify llvm as the middle end to generate machine code and leave out the runtime
    * runtime - optional, for interpreted languages, specify the runtime. For fully compiled languages this is null
* compile time interpreter
