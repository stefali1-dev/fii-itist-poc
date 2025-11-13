"""Request handlers for different endpoints."""
from .home import handle_home
from .form import handle_form
from .results import handle_results
from .default import handle_default

__all__ = ['handle_home', 'handle_form', 'handle_results', 'handle_default']
