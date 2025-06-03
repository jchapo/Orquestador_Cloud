# Importaciones para facilitar el acceso a los menús
from .admin import show_admin_menu, handle_admin_choice
from .user import show_regular_user_menu, handle_user_choice
from .researcher import show_researcher_menu, handle_researcher_choice
#from .auditor import show_auditor_menu, handle_auditor_choice
#from .operator import show_operator_menu, handle_operator_choice

# Diccionario de manejadores de menú por rol
MENU_HANDLERS = {
    "admin": (show_admin_menu, handle_admin_choice),
    "user": (show_regular_user_menu, handle_user_choice),
    #"investigador_avanzado": (show_researcher_menu, handle_researcher_choice),
    "researcher": (show_researcher_menu, handle_researcher_choice)
    #"auditor": (show_auditor_menu, handle_auditor_choice),
    #"operator": (show_operator_menu, handle_operator_choice)
}

def get_menu_handler(role):
    """Obtiene las funciones de menú para un rol específico"""
    return MENU_HANDLERS.get(role, (None, None))

__all__ = [
    'show_admin_menu', 
    'handle_admin_choice',
    'get_menu_handler'
]