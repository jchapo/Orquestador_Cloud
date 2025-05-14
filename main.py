from auth import Authenticator
from menus import get_menu_handler
import sys
import time

def main():
    auth = Authenticator()
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        login_result = auth.login()
        
        if login_result:
            break
        else:
            attempts += 1
            
            if attempts < max_attempts:
                input("Presione Enter para intentar nuevamente...")
                auth.clear_screen()
            else:
                auth.show_max_attempts_animation()
                sys.exit(1)
    
    # Menú principal
    while True:
        auth.clear_screen()
        print("\n=== Menú Principal ===")
        
        role = auth.current_user["role"]
        show_menu, handle_choice = get_menu_handler(role)
        
        if not show_menu or not handle_choice:
            print(f"❌ Rol desconocido: {role}")
            break
        
        choice = show_menu()
        
        if choice.lower() == 'q':
            auth.clear_screen()
            
            # Frames de la animación progresiva
            frames = [
                "⚙️ Cerrando procesos...",
                "✅ ¡Sesión finalizada!"
            ]
                     
            for frame in frames:
                auth.clear_screen()
                print("\n"*5)  # Centrar verticalmente
                print(frame.center(50))
                print("\n"*5)
                time.sleep(0.5)
            sys.exit(1)
            
        handle_choice(choice, auth)
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    main()