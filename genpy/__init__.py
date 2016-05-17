"""Generator for Python code."""

from __future__ import division, absolute_import, print_function

__copyright__ = "Copyright (C) 2008 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


class Generable(object):
    def __str__(self):
        """Return a single string (possibly containing newlines) representing
        this code construct."""
        return "\n".join(l.rstrip() for l in self.generate())

    def generate(self):
        """Generate (i.e. yield) the lines making up this code construct."""

        raise NotImplementedError


# {{{ suite

def _flatten_suite(contents):
    if isinstance(contents, Suite):
        contents = contents.contents
    elif isinstance(contents, Generable):
        return [contents]

    result = []
    for el in contents:
        if isinstance(el, Suite):
            result.extend(_flatten_suite(el))
        else:
            result.append(el)

    return result


class Suite(Generable):
    def __init__(self, contents=[]):
        contents = _flatten_suite(contents)

        self.contents = contents[:]

        for item in contents:
            assert isinstance(item, Generable)

    def generate(self):
        for item in self.contents:
            for item_line in item.generate():
                yield "    " + item_line

    def append(self, data):
        self.contents.append(data)

    def extend(self, data):
        self.contents.extend(data)

    def insert(self, i, data):
        self.contents.insert(i, data)

    def extend_log_block(self, descr, data):
        self.contents.append(Comment(descr))
        self.contents.extend(data)
        self.contents.append(Line())


def suite_if_necessary(contents):
    if len(contents) == 1:
        return contents[0]
    else:
        return Suite(contents)

# }}}


# {{{ struct-like

class Class(Generable):
    """A class definition."""

    def __init__(self, name, bases, attributes):
        self.name = name
        self.bases = bases
        self.attributes = attributes

    def generate(self):
        bases = self.bases
        if not bases:
            bases = ["object"]

        yield "class %s(%s)" % (self.name, ", ".join(bases))
        for f in self.attributes:
            for f_line in f.generate():
                yield "    " + f_line

# }}}


# {{{ control flow/statement stuff

class If(Generable):
    def __init__(self, condition, then_, else_=None):
        self.condition = condition

        assert isinstance(then_, Generable)
        if else_ is not None:
            assert isinstance(else_, Generable)
            if not isinstance(else_, Suite):
                else_ = Suite(else_)

        if not isinstance(then_, Suite):
            then_ = Suite(then_)

        self.then_ = then_
        self.else_ = else_

    def generate(self):
        condition_lines = self.condition.split("\n")
        if len(condition_lines) > 1:
            yield "if ("
            for l in condition_lines:
                yield "        "+l
            yield "  ):"
        else:
            yield "if %s:" % self.condition

        for line in self.then_.generate():
            yield line

        if self.else_ is not None:
            yield "else:"
            for line in self.else_.generate():
                yield line


class Loop(Generable):
    def __init__(self, body):
        assert isinstance(body, Generable)
        self.body = body

    def generate(self):
        if self.intro_line() is not None:
            yield self.intro_line()

        for line in self.body.generate():
            yield line

        if self.outro_line() is not None:
            yield self.outro_line()

    def outro_line(self):
        return None


class CustomLoop(Loop):
    def __init__(self, intro_line, body, outro_line=None):
        self.intro_line_ = intro_line
        self.body = body
        self.outro_line_ = outro_line

    def intro_line(self):
        return self.intro_line_

    def outro_line(self):
        return self.outro_line_


class While(Loop):
    def __init__(self, condition, body):
        self.condition = condition
        super(While, self).__init__(body)

    def intro_line(self):
        return "while (%s):" % self.condition


class For(Loop):
    def __init__(self, vars, iterable, body):
        if not isinstance(vars, tuple):
            vars = (vars,)

        self.vars = vars
        self.iterable = iterable

        if not isinstance(body, Suite):
            body = Suite(body)

        super(For, self).__init__(body)

    def intro_line(self):
        return "for %s in %s:" % (", ".join(self.vars), self.iterable)


def make_multiple_ifs(conditions_and_blocks, base=None):
    if base == "last":
        _, base = conditions_and_blocks[-1]
        conditions_and_blocks = conditions_and_blocks[:-1]

    for cond, block in conditions_and_blocks[::-1]:
        base = If(cond, block, base)

    return base

# }}}


# {{{ simple statements

class Import(Generable):
    def __init__(self, module):
        self.module = module

    def generate(self):
        yield "import %s" % self.module


class ImportAs(Generable):
    def __init__(self, module, as_):
        self.module = module
        self.as_ = as_

    def generate(self):
        yield "import %s as %s" % (self.module, self.as_)


class FromImport(Generable):
    def __init__(self, module, names):
        self.module = module
        self.names = names

    def generate(self):
        yield "from %s import %s" % (self.module, ", ".join(self.names))


class Statement(Generable):
    def __init__(self, text):
        self.text = text

    def generate(self):
        yield self.text


class Assign(Generable):
    def __init__(self, lvalue, rvalue):
        self.lvalue = lvalue
        self.rvalue = rvalue

    def generate(self):
        yield "%s = %s" % (self.lvalue, self.rvalue)


class Line(Generable):
    def __init__(self, text=""):
        self.text = text

    def generate(self):
        yield self.text


class Return(Generable):
    def __init__(self, expr):
        self.expr = expr

    def generate(self):
        yield "return %s" % self.expr


class Raise(Generable):
    def __init__(self, expr):
        self.expr = expr

    def generate(self):
        yield "raise %s" % self.expr


class Assert(Generable):
    def __init__(self, expr):
        self.expr = expr

    def generate(self):
        yield "assert %s" % self.expr


class Yield(Generable):
    def __init__(self, expr):
        self.expr = expr

    def generate(self):
        yield "yield %s" % self.expr


class Comment(Generable):
    def __init__(self, text):
        self.text = text

    def generate(self):
        yield "# %s" % self.text

# }}}


class Function(Generable):
    def __init__(self, name, args, body):
        assert isinstance(body, Generable)
        self.name = name
        self.args = args
        if not isinstance(body, Suite):
            body = Suite(body)

        self.body = body

    def generate(self):
        yield "def %s(%s):" % (self.name, ", ".join(self.args))

        for line in self.body.generate():
            yield line

# vim: fdm=marker
