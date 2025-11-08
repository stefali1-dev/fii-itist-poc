"""Request handlers for different endpoints."""
from .home import handle_home
from .formular import handle_formular
from .results import handle_results
from .default import handle_default
from .get_formular import handle_get_formular

__all__ = ['handle_home', 'handle_formular', 'handle_results', 'handle_default', "handle_get_formular"]
