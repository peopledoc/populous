import re


# match a variable with attributes ($var.attr), except if it's escaped
VARS_REGEX = re.compile(r"(?<!\\)\$(?P<var>\w[\w.]*(?<!\.))+")
SUBSTITUTE = "{\g<var>}"


def parse_vars(value):
    if not isinstance(value, str):
        return value

    if not "$" in value:
        return value

    # escape present '{' and '}'
    value = value.replace('{', '{{').replace('}', '}}')
    template = re.sub(VARS_REGEX, SUBSTITUTE, value)

    if value == template:
        return value

    return Expression(template)


class Expression(object):

    def __init__(self, template=""):
        self.template = template

    def __str__(self):
        return self.evaluate()

    def evaluate(self, **vars_):
        return self.template.format(**vars_)
