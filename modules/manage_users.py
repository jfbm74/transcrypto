#!/usr/bin/env python3
"""
Gestión sencilla de usuarios ZentraText:

    python manage_users.py listar
    python manage_users.py eliminar <usuario>
    python manage_users.py crear_admin
    python manage_users.py cambiar_password <usuario> <nueva_clave>
"""

import sys
from app import create_app
from modules.auth.models import User, db

app = create_app()

# ----------------------------------------------------------------------
def list_users():
    """Muestra todos los usuarios con sus datos básicos."""
    with app.app_context():
        users = User.query.all()
        print("\nLista de usuarios:")
        print("-" * 60)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<5}")
        print("-" * 60)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} "
                  f"{'Sí' if user.is_admin else 'No'}")
        print("-" * 60)
        print(f"Total: {len(users)} usuarios\n")

# ----------------------------------------------------------------------
def change_password(username, new_password):
    """Actualiza la contraseña de un usuario existente."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌  El usuario '{username}' no existe.")
            return
        user.set_password(new_password)
        db.session.commit()
        print(f"✅  Contraseña actualizada para '{username}'.")

# ----------------------------------------------------------------------
def delete_user(username):
    """Elimina usuario y sus transcripciones (con confirmación para admins)."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"El usuario '{username}' no existe.")
            return

        if user.is_admin:
            confirm = input(
                f"¿Estás seguro de eliminar al usuario administrador "
                f"'{username}'? (s/N): "
            )
            if confirm.lower() != 's':
                print("Operación cancelada.")
                return

        # Borrar transcripciones asociadas
        from modules.transcription.models import Transcription
        transcriptions = Transcription.query.filter_by(user_id=user.id).all()
        for t in transcriptions:
            db.session.delete(t)

        db.session.delete(user)
        db.session.commit()
        print(f"Usuario '{username}' eliminado junto con "
              f"{len(transcriptions)} transcripciones.")

# ----------------------------------------------------------------------
def create_admin():
    """Crea el usuario administrador por defecto si no existe."""
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        if admin:
            print("El usuario administrador ya existe.")
            return
        admin = User(username="admin", email="admin@example.com", is_admin=True)
        admin.set_password("adminpassword")
        db.session.add(admin)
        db.session.commit()
        print("Usuario administrador creado con éxito.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_help = (
            "Uso:\n"
            "  listar                                – Muestra todos los usuarios\n"
            "  eliminar <username>                  – Elimina un usuario\n"
            "  cambiar_password <username> <clave>  – Cambia la contraseña\n"
            "  crear_admin                          – Crea un usuario admin\n"
        )
        print(cmd_help)
        sys.exit(1)

    command = sys.argv[1]

    if command == "listar":
        list_users()

    elif command == "eliminar" and len(sys.argv) == 3:
        delete_user(sys.argv[2])

    elif command == "cambiar_password" and len(sys.argv) == 4:
        change_password(sys.argv[2], sys.argv[3])

    elif command == "crear_admin":
        create_admin()

    else:
        print("Comando o argumentos incorrectos.\n")
        sys.argv = [sys.argv[0]]
        sys.exit(1)