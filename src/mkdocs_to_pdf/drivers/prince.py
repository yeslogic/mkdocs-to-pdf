import re
from logging import Logger

# Prince's built-in defaults differ from browsers' in a few places that
# browser-oriented themes (e.g. mkdocs-material) rely on. These rules come
# first, so any theme or custom stylesheet still overrides them.
_COMPAT_CSS = """
details, summary { display: block; }
h1 { font-size: 2em; } h2 { font-size: 1.5em; } h3 { font-size: 1.17em; }
h4 { font-size: 1em; } h5 { font-size: .83em; } h6 { font-size: .67em; }
"""

# The print stylesheet gives every section `min-height: 100vh`. With any
# padding or margin on top, that is taller than one page: WeasyPrint clips
# the box at the page end, while Prince continues it onto a blank page, as
# CSS fragmentation specifies. Sections still start on a new page.
_COMPAT_CSS += """
article:not(#doc-cover), section + section { min-height: auto !important; }
"""


class PrinceRenderer(object):
    """Renders the combined HTML with Prince (https://www.princexml.com/)
    through the prince-pdf package, which bundles the Prince engine."""

    @classmethod
    def setup(self, engine: str, prince_path: str, logger: Logger):
        if engine != 'prince':
            return None

        try:
            import prince_pdf
        except ImportError:
            raise RuntimeError(
                'The `prince` engine needs the prince-pdf package: '
                'pip install "mkdocs-to-pdf[prince]"')

        return self(prince_pdf, prince_path, logger)

    def __init__(self, prince_pdf, prince_path: str, logger: Logger):
        self._prince_pdf = prince_pdf
        # None runs the bundled engine (or the one PRINCE_PATH selects).
        self._prince_path = prince_path or None
        self._logger = logger

    def write_pdf(self, html_string: str, output: str):
        self._logger.info(' Rendering with `Prince`.')

        html_string = re.sub(
            r'<head[^>]*>',
            lambda m: f'{m.group(0)}<style>{_COMPAT_CSS}</style>',
            html_string, count=1)

        self._prince_pdf.html_to_pdf(
            html_string, output,
            executable=self._prince_path,
            on_message=self._log)

    def _log(self, message):
        text = f'  {message.location}: {message.text}' \
            if message.location else f'  {message.text}'
        if message.severity == 'err':
            self._logger.error(text)
        elif message.severity == 'wrn':
            self._logger.warning(text)
        else:
            self._logger.debug(text)
