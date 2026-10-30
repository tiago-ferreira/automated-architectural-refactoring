"""Model de Usuários com queries parametrizadas e hashing seguro de senhas."""
from typing import Any, Dict, List, Optional
from werkzeug.security import check_password_hash, generate_password_hash
from config.database import PASSWORD_HASH_PREFIXES, get_db
from config.settings import Config


def _row_to_usuario_public_dict(row) -> Dict[str, Any]:
    """Serializa o usuário sem expor senha ou hash."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def _verify_password(stored_password: str, provided_password: str) -> bool:
    if not stored_password or not stored_password.startswith(PASSWORD_HASH_PREFIXES):
        return False
    return check_password_hash(stored_password, provided_password)


def get_todos_usuarios() -> List[Dict[str, Any]]:
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_usuario_public_dict(row) for row in cursor.fetchall()]


def get_usuario_por_id(usuario_id: int) -> Optional[Dict[str, Any]]:
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return _row_to_usuario_public_dict(row) if row else None


def email_ja_cadastrado(email: str) -> bool:
    cursor = get_db().cursor()
    cursor.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone() is not None


def login_usuario(email: str, senha: str) -> Optional[Dict[str, Any]]:
    cursor = get_db().cursor()
    cursor.execute(
        "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    if row and _verify_password(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None


def criar_usuario(
    nome: str, email: str, senha: str, tipo: str = Config.DEFAULT_USER_ROLE
) -> int:
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return int(cursor.lastrowid)
