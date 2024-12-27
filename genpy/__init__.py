"""
.. autoclass:: Generable
.. autoclass:: Suite
    :show-inheritance:
.. autoclass:: Collection
    :show-inheritance:

Block nodes
-----------

.. autoclass:: Class
    :show-inheritance:
.. autoclass:: If
    :show-inheritance:
.. autoclass:: Loop
    :show-inheritance:
.. autoclass:: CustomLoop
    :show-inheritance:
.. autoclass:: While
    :show-inheritance:
.. autoclass:: For
    :show-inheritance:
.. autoclass:: Function
    :show-inheritance:
.. autofunction:: make_multiple_ifs

Single (logical) line Nodes
---------------------------

.. autoclass:: Import
    :show-inheritance:
.. autoclass:: ImportAs
    :show-inheritance:
.. autoclass:: FromImport
    :show-inheritance:
.. autoclass:: Statement
    :show-inheritance:
.. autoclass:: Assign
    :show-inheritance:
.. autoclass:: Line
    :show-inheritance:
.. autoclass:: Return
    :show-inheritance:
.. autoclass:: Raise
    :show-inheritance:
.. autoclass:: Assert
    :show-inheritance:
.. autoclass:: Yield
    :show-inheritance:
.. autoclass:: Pass
    :show-inheritance:
.. autoclass:: Comment
    :show-inheritance:
"""

__copyright__ = "Copyright (C) 2015 Andreas Kloeckner"

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

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import Literal


class Generable(ABC):
    """A base class for AST nodes capable of generating code.

    .. automethod:: __str__
    .. automethod:: generate
    """

    def __str__(self) -> str:
        """Return a single string (possibly containing newlines) representing
        this code construct."""
        return "\n".join(line.rstrip() for line in self.generate())

    @abstractmethod
    def generate(self) -> Iterator[str]:
        """Generate (i.e. yield) the lines making up this code construct."""


# {{{ suite

def _flatten_suite(contents: Iterable[Generable] | Generable) -> list[Generable]:
    if isinstance(contents, Suite):
        contents = contents.contents
    elif isinstance(contents, Generable):
        return [contents]

    assert not isinstance(contents, Generable)

    result = []
    for el in contents:
        if isinstance(el, Suite):
            result.extend(_flatten_suite(el))
        else:
            result.append(el)

    return result


class Suite(Generable):
    """
    .. automethod:: __init__
    .. automethod:: generate
    .. automethod:: append
    .. automethod:: extend
    .. automethod:: insert
    .. automethod:: extend_log_block
    """

    def __init__(self, contents: Iterable[Generable] | Generable | None = None) -> None:
        if contents is None:
            contents = []
        contents = _flatten_suite(contents)

        if not contents:
            contents = [Pass()]

        self.contents = contents[:]

        for item in contents:
            assert isinstance(item, Generable)

    def generate(self) -> Iterator[str]:
        for item in self.contents:
            for item_line in item.generate():
                yield f"    {item_line}"

    def append(self, data: Generable) -> None:
        self.contents.append(data)

    def extend(self, data: Iterable[Generable]) -> None:
        self.contents.extend(data)

    def insert(self, i: int, data: Generable) -> None:
        self.contents.insert(i, data)

    def extend_log_block(self, descr: str, data: Iterable[Generable]) -> None:
        self.contents.append(Comment(descr))
        self.contents.extend(data)
        self.contents.append(Line())


class Collection(Suite):
    """Like :class:`Suite`, but does not lead to indentation."""

    def generate(self) -> Iterator[str]:
        for item in self.contents:
            yield from item.generate()


def suite_if_necessary(contents: Sequence[Generable]) -> Generable:
    if len(contents) == 1:
        return contents[0]
    else:
        return Suite(contents)

# }}}


# {{{ struct-like

class Class(Generable):
    """A class definition.

    .. automethod:: __init__
    """

    def __init__(self,
                 name: str,
                 bases: Iterable[str],
                 attributes: Iterable[Generable]) -> None:
        self.name = name
        self.bases = tuple(bases)
        self.attributes = tuple(attributes)

    def generate(self) -> Iterator[str]:
        bases = self.bases
        if not bases:
            bases = ("object",)

        yield "class {}({}):".format(self.name, ", ".join(bases))
        for f in self.attributes:
            for f_line in f.generate():
                yield f"    {f_line}"

# }}}


# {{{ control flow/statement stuff

class If(Generable):
    """An ``if/then/else`` block.

    .. automethod:: __init__
    """

    def __init__(self,
                 condition: str,
                 then_: Generable,
                 else_: Generable | None = None) -> None:
        assert isinstance(then_, Generable)
        if not isinstance(then_, Suite):
            then_ = Suite(then_)

        if else_ is not None:
            assert isinstance(else_, Generable)
            if not isinstance(else_, Suite):
                else_ = Suite(else_)

        self.condition = condition
        self.then_ = then_
        self.else_ = else_

    def generate(self) -> Iterator[str]:
        condition_lines = self.condition.split("\n")
        if len(condition_lines) > 1:
            yield "if ("
            for line in condition_lines:
                yield f"        {line}"
            yield "  ):"
        else:
            yield f"if {self.condition}:"

        for line in self.then_.generate():
            yield line

        if self.else_ is not None:
            yield "else:"
            for line in self.else_.generate():
                yield line


class Loop(Generable, ABC):
    """An abstract base class for loops. class for loop blocks.

    .. automethod:: __init__
    .. automethod:: intro_line
    .. automethod:: outro_line
    """

    def __init__(self, body: Generable) -> None:
        assert isinstance(body, Generable)
        self.body = body

    def generate(self) -> Iterator[str]:
        intro_line = self.intro_line()
        if intro_line is not None:
            yield intro_line

        yield from self.body.generate()

        outro_line = self.outro_line()
        if outro_line is not None:
            yield outro_line

    @abstractmethod
    def intro_line(self) -> str | None:
        pass

    def outro_line(self) -> str | None:
        return None


class CustomLoop(Loop):
    """
    .. automethod:: __init__
    """

    def __init__(self,
                 intro_line: str | None,
                 body: Generable,
                 outro_line: str | None = None) -> None:
        super().__init__(body)
        self.intro_line_ = intro_line
        self.outro_line_ = outro_line

    def intro_line(self) -> str | None:
        return self.intro_line_

    def outro_line(self) -> str | None:
        return self.outro_line_


class While(Loop):
    """
    .. automethod:: __init__
    """

    def __init__(self, condition: str, body: Generable):
        self.condition = condition
        super().__init__(body)

    def intro_line(self) -> str | None:
        return f"while ({self.condition}):"


class For(Loop):
    """
    .. automethod:: __init__
    """

    def __init__(self,
                 vars: str | tuple[str, ...],
                 iterable: str,
                 body: Generable) -> None:
        if not isinstance(vars, tuple):
            vars = (vars,)

        if not isinstance(body, Suite):
            body = Suite(body)

        super().__init__(body)
        self.vars = vars
        self.iterable = iterable

    def intro_line(self) -> str | None:
        return "for {} in {}:".format(", ".join(self.vars), self.iterable)


def make_multiple_ifs(
        conditions_and_blocks: Sequence[tuple[str, Generable]],
        base: Generable | Literal["last"] | None = None) -> Generable | None:
    if base == "last":
        _, base = conditions_and_blocks[-1]
        conditions_and_blocks = conditions_and_blocks[:-1]

    for cond, block in conditions_and_blocks[::-1]:
        base = If(cond, block, base)

    return base

# }}}


# {{{ simple statements

class Import(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, module: str) -> None:
        self.module = module

    def generate(self) -> Iterator[str]:
        yield f"import {self.module}"


class ImportAs(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, module: str, as_: str) -> None:
        self.module = module
        self.as_ = as_

    def generate(self) -> Iterator[str]:
        yield f"import {self.module} as {self.as_}"


class FromImport(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, module: str, names: Iterable[str]) -> None:
        self.module = module
        self.names = tuple(names)

    def generate(self) -> Iterator[str]:
        yield "from {} import {}".format(self.module, ", ".join(self.names))


class Statement(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def generate(self) -> Iterator[str]:
        yield self.text


class Assign(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, lvalue: str, rvalue: str) -> None:
        self.lvalue = lvalue
        self.rvalue = rvalue

    def generate(self) -> Iterator[str]:
        yield f"{self.lvalue} = {self.rvalue}"


class Line(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, text: str = "") -> None:
        self.text = text

    def generate(self) -> Iterator[str]:
        yield self.text


class Return(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    def generate(self) -> Iterator[str]:
        yield f"return {self.expr}"


class Raise(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    def generate(self) -> Iterator[str]:
        yield f"raise {self.expr}"


class Assert(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    def generate(self) -> Iterator[str]:
        yield f"assert {self.expr}"


class Yield(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    def generate(self) -> Iterator[str]:
        yield f"yield {self.expr}"


class Pass(Generable):
    """
    .. automethod:: __init__
    """

    def generate(self) -> Iterator[str]:
        yield "pass"


class Comment(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def generate(self) -> Iterator[str]:
        yield f"# {self.text}"

# }}}


class Function(Generable):
    """
    .. automethod:: __init__
    """

    def __init__(self,
                 name: str,
                 args: Iterable[str],
                 body: Generable,
                 decorators: Iterable[str] = ()) -> None:
        assert isinstance(body, Generable)
        if not isinstance(body, Suite):
            body = Suite(body)

        self.name = name
        self.args = tuple(args)
        self.decorators = tuple(decorators)
        self.body = body

    def generate(self) -> Iterator[str]:
        yield from self.decorators

        yield "def {}({}):".format(self.name, ", ".join(self.args))

        yield from self.body.generate()

# vim: fdm=marker
