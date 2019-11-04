import os
import sys
from functools import wraps


def one_task(**kwargs):
    """one_task - decorator - simple `doit` task definition

    Saves needing to define a function within the task function

    kwards are `doit` parameters like `task_dep`, `targets`, etc.

    USAGE:
        doit -f foo.py
          or
        doit list -f foo.py
        where foo.py imports and uses @one_task()

    Set environent variable GRAPH_DOIT for graphviz dot output, e.g.
        export GRAPH_DOIT=1
        doit list -f foo.py | python doit_lib.py | dot -Tpng >tasks.png
    NOTE:
        PowerShell redirection turns everything into UTF-16, which dot
        doesn't understand, so use cmd instead if using dot output
    LIMITATIONS:
        To include regular doit task_ definitions in dot output, decorate
        them with `one_task()`.  Even then, the 'file_dep' etc. relationships
        in the task_ def are not seen / reported as graph edges.
    """
    if 'active' in kwargs:
        # active is not a `doit` parameter, but an extension here to make it
        # easy to turn tasks off
        if kwargs['active']:
            # if active is True (usually not specified) just delete the kwarg
            del kwargs['active']
        else:
            # if active is False, return no-op
            return lambda function: None

    def one_task_maker(function):
        d = {'actions': [function]}
        d.update(kwargs)
        if os.environ.get("GRAPH_DOIT"):
            print(
                "DOT:CHAIN:%s %s"
                % (function.__name__, function.__doc__.split('\n')[0].strip())
            )
            for node in d.get('file_dep', []):
                node = node.replace('.', '_')
                print("DOT:%s -> %s" % (node, function.__name__))
            for node in d.get('task_dep', []):
                print("DOT:%s -> %s" % (node, function.__name__))
            for node in d.get('targets', []):
                node = node.replace('.', '_')
                print("DOT:%s -> %s" % (function.__name__, node))

        if function.__name__.startswith("task_"):
            # doit task, having (maybe) reported it for dot, leave it alone
            return function

        @wraps(function)
        def function_task():
            return d

        # `doit` checks this attribute on functions that don't start with task_
        function_task.create_doit_tasks = function_task
        return function_task

    return one_task_maker


def _t(text):
    if text.startswith('task_'):
        return text[5:]
    else:
        return text


def to_dot(lines):
    """Extract dot graph from text (command line output)"""
    graph = ['digraph "G" {']
    chain = []
    for line in lines:
        line = line.strip()
        if line.startswith("DOT:CHAIN:"):
            name, desc = line.split(None, 1)
            name = _t(name.replace('DOT:CHAIN:', ''))
            chain.append(name)
            graph.append('%s [tooltip="%s"]' % (name, desc))
        elif line.startswith("DOT:"):
            n0, n1 = map(_t, line.split(' -> ', 1))
            n0 = n0.replace('DOT:', '')
            graph.append('%s -> %s' % (n0, n1))
    graph.append(' -> '.join(chain))
    graph.append('}')
    return '\n'.join(graph)


def main():
    sys.stdout.write(to_dot(sys.stdin))


if __name__ == "__main__":
    main()
