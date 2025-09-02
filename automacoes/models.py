from django.db import models

class Automacao(models.Model):
    STATUS_PENDENTE   = 'pendente'
    STATUS_EXECUCAO   = 'execucao'
    STATUS_CONCLUIDA  = 'concluida'
    STATUS_FALHOU     = 'falhou'
    STATUS_PAUSADA    = 'pausada'
    
    STATUS_CHOICES = [
        (STATUS_PENDENTE,  'Pendente'),
        (STATUS_EXECUCAO,  'Em execução'),
        (STATUS_CONCLUIDA, 'Concluída'),
        (STATUS_FALHOU,    'Falhou'),
        (STATUS_PAUSADA,   'Pausada'),
    ]

    tipo        = models.CharField(max_length=50, default='sync_sheet')  # qual automação
    projeto     = models.CharField(max_length=120, blank=True)           # opcional (ex.: SEDUC TEC 1.0)
    dry_run     = models.BooleanField(default=False)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDENTE)

    started_at  = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    mensagem    = models.TextField(blank=True)   # resumo/log
    sucesso     = models.PositiveIntegerField(default=0)
    erros       = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Automação'
        verbose_name_plural = 'Automações'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.tipo} [{self.get_status_display()}] {self.started_at:%d/%m %H:%M}'
