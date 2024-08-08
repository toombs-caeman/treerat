function cache(fn) {
    function cache_wrapper(...args){
        var key = args.join('');
        if(!fn.cache.hasOwnProperty(key)){
            fn.cache[key] = fn(...args);
        }
        return fn.cache[key];
    }
    cache_wrapper.clear = function() { fn.cache = {}; }
    cache_wrapper.clear()
    return cache_wrapper
}

function Dot(idx) {
    if
}
var Choice = cache(function(idx, ...exprs) {
    console.log(exprs)
    for (var i = 0; i < exprs.length; i++) {
        var x = exprs[i](idx)
        if (x) { return x; }
    }
});

function snode(kind, start, stop, ...args) {
    var n = node(kind, ...args);
    v.start = start
    v.stop = stop
    return n
}
function node(kind, ...args) {
    return {
        'kind':kind,
        'children':args,
    }
};
function node2graph(n) {
    // prepare a node tree for visualization with vizjs
    var edges = [];
    var nodes = [];
    var id = 0;
    function newId() { id += 1; return id; }
    function N(n, id) {
        nodes.push({ name:id, attributes: { label:n.kind } });
        for (var i = 0; i < n.children.length; i++) {
            var child = n.children[i];
            var cid = newId();
            edges.push({tail:id, head:cid});
            if (child.hasOwnProperty('children')) {
                N(child, cid);
            } else {
                nodes.push({
                    name:cid,
                    attributes: {
                        label:JSON.stringify(child),
                        shape:'box',
                    }
                });
            }
        };
    };
    N(n, newId());
    return { directed: true, edges: edges, nodes: nodes };
}

fixedpoint = {
            'start': node('Node', 'start', node('Sequence', node('Label', 'Spacing'), node('Argument', node('OneOrMore', node('Label', 'Definition'))), node('Label', 'EOF'))),
            'Definition': node('Node', 'Definition', node('Sequence', node('Argument', node('Choice', node('Label', 'Label'), node('Label', 'Node'))), node('Label', 'LEFTARROW'), node('Argument', node('Label', 'ParseExpr')))),
            'ParseExpr': node('Choice', node('Argument', node('Label', 'Choice')), node('Argument', node('Label', 'Sequence')), node('Choice', node('Argument', node('Label', 'Lookahead')), node('Argument', node('Label', 'NotLookahead')), node('Argument', node('Label', 'Argument'))), node('Choice', node('Argument', node('Label', 'ZeroOrOne')), node('Argument', node('Label', 'ZeroOrMore')), node('Argument', node('Label', 'OneOrMore'))), node('Argument', node('Label', 'Primary'))),
            'Choice': node('Node', 'Choice', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '1')), node('OneOrMore', node('Sequence', node('Label', 'SLASH'), node('Argument', node('Index', node('Label', 'ParseExpr'), '1')))))),
            'Sequence': node('Node', 'Sequence', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '2')), node('OneOrMore', node('Argument', node('Index', node('Label', 'ParseExpr'), '2'))))),
            'Lookahead': node('Node', 'Lookahead', node('Sequence', node('Label', 'AMP'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'NotLookahead': node('Node', 'NotLookahead', node('Sequence', node('Label', 'BANG'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'Argument': node('Node', 'Argument', node('Sequence', node('Label', 'ARG'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'ZeroOrOne': node('Node', 'ZeroOrOne', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'QUESTION'))),
            'ZeroOrMore': node('Node', 'ZeroOrMore', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'STAR'))),
            'OneOrMore': node('Node', 'OneOrMore', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'PLUS'))),
            'Primary': node('Choice', node('Sequence', node('Label', 'OPEN'), node('Argument', node('Label', 'ParseExpr')), node('Label', 'CLOSE')), node('Argument', node('Label', 'Index')), node('Sequence', node('Argument', node('Label', 'Label')), node('NotLookahead', node('Label', 'LEFTARROW'))), node('Argument', node('Label', 'String')), node('Argument', node('Label', 'CharClass')), node('Argument', node('Label', 'Dot'))),
            'Node': node('Node', 'Node', node('Sequence', node('Label', 'ARG'), node('Argument', node('Label', 'Label')))),
            'Index': node('Node', 'Index', node('Sequence', node('Argument', node('Label', 'Label')), node('String', ':'), node('Argument', node('OneOrMore', node('CharClass', '0-9'))), node('Label', 'Spacing'))),
            'Label': node('Node', 'Label', node('Sequence', node('Argument', node('Sequence', node('CharClass', 'a-z', 'A-Z', '_'), node('ZeroOrMore', node('CharClass', 'a-z', 'A-Z', '_', '0-9')))), node('Label', 'Spacing'))),
            'Spacing': node('ZeroOrMore', node('Choice', node('Label', 'SPACE'), node('Label', 'Comment'))),
            'Comment': node('Sequence', node('String', '#'), node('ZeroOrMore', node('Sequence', node('NotLookahead', node('Label', 'EOL')), node('Dot',))), node('Choice', node('Label', 'EOL'), node('Label', 'EOF'))),
            'LEFTARROW': node('Sequence', node('String', '<-'), node('Label', 'Spacing')),
            'SLASH': node('Sequence', node('String', '/'), node('Label', 'Spacing')),
            'ARG': node('Sequence', node('String', '%'), node('Label', 'Spacing')),
            'AMP': node('Sequence', node('String', '&'), node('Label', 'Spacing')),
            'BANG': node('Sequence', node('String', '!'), node('Label', 'Spacing')),
            'QUESTION': node('Sequence', node('String', '?'), node('Label', 'Spacing')),
            'STAR': node('Sequence', node('String', '*'), node('Label', 'Spacing')),
            'PLUS': node('Sequence', node('String', '+'), node('Label', 'Spacing')),
            'OPEN': node('Sequence', node('Argument', node('String', '(')), node('Label', 'Spacing')),
            'CLOSE': node('Sequence', node('String', ')'), node('Label', 'Spacing')),
            'Dot': node('Node', 'Dot', node('Sequence', node('String', '.'), node('Label', 'Spacing'))),
            'SPACE': node('Choice', node('String', ' '), node('String', '\t'), node('Label', 'EOL')),
            'EOL': node('Choice', node('String', '\r\n'), node('String', '\r'), node('String', '\n')),
            'EOF': node('NotLookahead', node('Dot',)),
            'CharClass': node('Node', 'CharClass', node('Sequence', node('String', '['), node('Choice', node('Argument', node('Sequence', node('Label', 'Char'), node('String', '-'), node('Label', 'Char'))), node('Argument', node('Label', 'Char'))), node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', ']')), node('Choice', node('Argument', node('Sequence', node('Label', 'Char'), node('String', '-'), node('Label', 'Char'))), node('Argument', node('Label', 'Char'))))), node('String', ']'), node('Label', 'Spacing'))),
            'String': node('Node', 'String', node('Sequence', node('Choice', node('Sequence', node('String', '"'), node('Argument', node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', '"')), node('Label', 'Char')))), node('String', '"')), node('Sequence', node('String', "'"), node('Argument', node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', "'")), node('Label', 'Char')))), node('String', "'"))), node('Label', 'Spacing'))),
            'Char': node('Argument', node('Choice', node('Sequence', node('String', '\\'), node('CharClass', ']', '[', 'n', 'r', 't', "'", '"', '\\')), node('Sequence', node('String', '\\'), node('CharClass', '0-2'), node('CharClass', '0-7'), node('CharClass', '0-7')), node('Sequence', node('String', '\\'), node('CharClass', '0-7'), node('ZeroOrOne', node('CharClass', '0-7'))), node('Sequence', node('NotLookahead', node('String', '\\')), node('Dot',))))}
