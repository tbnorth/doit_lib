import os
from functools import wraps


def one_task(**kwargs):
    """one_task - decorator - simple `doit` task definition

    Saves needing to define a function within the task function

    kwards are `doit` parameters like `task_dep`, `targets`, etc.

    LIMITATIONS:
        To include regular doit task_ definitions in dot output, decorate
        them with `one_task()`.  Even then, the 'task_dep' etc. relationships
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
