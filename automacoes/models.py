from django.db import models
from django.utils import timezone


class Automacao(models.Model):
    class Tipo(models.TextChoices):
        SYNC_SHEET = "sync_sheet", "sync_sheet"

    class Status(models.TextChoices):
        PENDENTE    = "pendente", "Pendente"
        EM_EXECUCAO = "em_execucao", "Em execução"
        CONCLUIDA   = "concluida", "Concluída"
        FALHOU      = "falhou", "Falhou"
        PAUSADA     = "pausada", "Pausada"

    tipo = models.CharField(max_length=32, choices=Tipo.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    projeto = models.CharField(max_length=200, blank=True, null=True)
    dry_run = models.BooleanField(default=False)

    mensagem = models.TextField(blank=True, default="")
    erros = models.TextField(blank=True, default="")
    sucesso = models.BooleanField(default=False)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} ({self.status})"

    class Meta:
        ordering = ("-started_at",)
