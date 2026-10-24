"""Serviço de notificações configurado via variáveis de ambiente (sem credenciais hardcoded)."""
import smtplib
from config.settings import Config, logger, utc_now


class NotificationService:
    def __init__(self):
        self.notifications = []
        self.email_host = Config.SMTP_HOST
        self.email_port = Config.SMTP_PORT
        self.email_user = Config.SMTP_USER
        self.email_password = Config.SMTP_PASSWORD

    def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self.email_user or not self.email_password:
            logger.info("SMTP não configurado; notificação registrada localmente para %s", to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except Exception as exc:
            logger.error("Erro ao enviar email: %s", exc)
            return False

    def notify_task_assigned(self, user, task) -> None:
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": utc_now(),
            }
        )

    def notify_task_overdue(self, user, task) -> None:
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id: int) -> list:
        return [n for n in self.notifications if n["user_id"] == user_id]
