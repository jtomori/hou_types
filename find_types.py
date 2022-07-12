import re
import ast
from collections import namedtuple
from ast import dump, get_docstring


# A type for holding source code and docstring type hints
TypePair = namedtuple("TypePair", ["src", "doc"])


class Analyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.type_pairs_set = set()

        # Pattern for finding docstring type hint
        self.pattern = re.compile('.* ->(.*)$', re.MULTILINE)

    def visit_FunctionDef(self, node) -> None:
        docstring = get_docstring(node)

        # If a function has a docstring, has a return type annotation 
        # and there is "->" in the docstring
        if not (docstring and node.returns and "->" in docstring):
            self.generic_visit(node)
            return

        # Look for type hint annotation in docstring
        match = self.pattern.search(docstring)
        if not match:
            self.generic_visit(node)
            return

        src_type = node.returns.s
        doc_type = match.groups()[0].strip()

        # Add to the set
        type_map = TypePair(src=src_type, doc=doc_type)
        self.type_pairs_set.add(type_map)

        # Visit child nodes
        self.generic_visit(node)


def skip(pair: TypePair) -> bool:
    return \
        "void" in pair.src or \
        "std::vector" in pair.src or \
        "InterpreterObject" in pair.src or \
        "std::map" in pair.src or \
        "UT_Tuple" in pair.src or \
        "std::pair" in pair.src or \
        "HOM_IterableList" in pair.src or \
        "HOM_EnumValue &" in pair.src or \
        pair.doc == ''  # Cases where return type is on the next line in the docstring


def print_pairs(pairs) -> None:
    for pair in pairs:
        print(f'"{pair.src}" = {pair.doc}')


def main() -> None:
    with open("/opt/hfs19.0.657/houdini/python3.7libs/hou.py", "r") as src:
        tree = ast.parse(src.read())
    
    analyzer = Analyzer()
    analyzer.visit(tree)
    pairs = analyzer.type_pairs_set  # First batch of type pairs

    # Filter out some types, see the skip function
    pairs_skipped = tuple(pair for pair in pairs if not skip(pair))

    # Sort by source type to find duplicates
    pairs_sorted = sorted(pairs_skipped, key=lambda x: x.src)

    #Print out results
    print_pairs(pairs_sorted)


if __name__ == "__main__":
    main()
