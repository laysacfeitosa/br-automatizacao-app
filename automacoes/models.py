from django.db import models

from django.db import models

class Automacao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_execucao', 'Em execução'),
        ('concluida', 'Concluída'),
        ('falhou', 'Falhou'),
        ('pausada', 'Pausada'),
    ]

    nome = models.CharField('Nome', max_length=120)
    descricao = models.TextField('Descrição', blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Automação'
        verbose_name_plural = 'Automações'

    def __str__(self):
        return self.nome
