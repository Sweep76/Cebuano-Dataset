import argparse
from .parser import Parser
from .visitors import SemanticAnalyzer


def run_parser(text: str):
    parser = Parser()
    errors, tree = parser.parse(text)

    long = len(parser.errors)
    if long == 0:
        print("No errors")
    for x in range(long):
        print("Error #" + str(x + 1))
        print(errors[x].error)
        if errors[x].wrong_value is not None:
            print("Error value: " + str(errors[x].wrong_value))
        print("Solution #" + str(x + 1))
        print(errors[x].correct)
        if errors[x].right_value is not None:
            print("Right values: " + ", ".join(errors[x].right_value))

    semantic_analyzer = SemanticAnalyzer()
    try:
        one = semantic_analyzer.visit(tree)
    except Exception as e:
        print(e)
        raise
    print(one)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input string")
    args = parser.parse_args()
    run_parser(args.input)
