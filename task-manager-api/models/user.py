"""Model de Usuários (User) com hashing seguro de senha e serialização protegida."""
import hashlib
from werkzeug.security import check_password_hash, generate_password_hash
from config.settings import Config, utc_now
from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=Config.DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self) -> dict:
        """Retorna os dados públicos do usuário (sem expor o hash de senha)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, pwd: str) -> None:
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd: str) -> bool:
        if not self.password:
            return False
        if self.password.startswith(("scrypt:", "pbkdf2:")):
            return check_password_hash(self.password, pwd)
        legacy_md5 = hashlib.md5(pwd.encode()).hexdigest()
        return self.password == legacy_md5

    def is_admin(self) -> bool:
        return self.role == "admin"
