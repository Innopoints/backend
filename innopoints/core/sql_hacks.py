"""Certain SQLAlchemy workarounds."""

from sqlalchemy.sql import Alias, ColumnElement
from sqlalchemy.ext.compiler import compiles


# pylint: disable=missing-docstring,invalid-name

# Source: https://github.com/sqlalchemy/sqlalchemy/issues/3566#issuecomment-441931331

class as_row(ColumnElement):
    def __init__(self, expr):
        assert isinstance(expr, Alias)
        self.expr = expr


@compiles(as_row)
def _gen_as_row(element, compiler, **kw):
    return compiler.visit_alias(element.expr, ashint=True, **kw)
