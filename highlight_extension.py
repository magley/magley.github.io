from jinja2 import nodes
from jinja2.ext import Extension
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from markupsafe import Markup


class HighlightExtension(Extension):
	tags = {"highlight"}


	def parse(self, parser):
		lineno = next(parser.stream).lineno
		language = parser.parse_expression()

		body = parser.parse_statements(
			["name:endhighlight"],
			drop_needle=True
		)

		return nodes.CallBlock(
			self.call_method("_highlight", [language]),
			[],
			[],
			body,
		).set_lineno(lineno)


	def _highlight(self, language, caller):
		code = caller()
		lexer = get_lexer_by_name(str(language))
		return Markup(highlight(code, lexer, HtmlFormatter()))