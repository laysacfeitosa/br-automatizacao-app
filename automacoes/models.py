from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


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
        
class ProjetoDados(models.Model):
    orgao = models.CharField(max_length=200, unique=True)
    receita_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    data_de_inicio = models.DateField(null=True, blank=True)
    prazo_de_vencimento = models.DateField(null=True, blank=True)
    total_de_aulas = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dados do Projeto"
        verbose_name_plural = "Dados do Projeto"

    def __str__(self):
        return self.orgao


class GravacaoLinha(models.Model):
    serie = models.CharField(max_length=200, blank=True, default="")
    curso = models.CharField(max_length=200)
    disciplina = models.CharField(max_length=200)
    carga_horaria = models.PositiveIntegerField(null=True, blank=True)
    aulas_gravadas = models.PositiveIntegerField(null=True, blank=True)
    # 0..100 (ex.: 87.50)
    percentual = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    situacao_gravacao = models.CharField(max_length=200, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Linha de Gravação"
        verbose_name_plural = "Gravação (linhas)"
        unique_together = (("serie", "curso", "disciplina"),)
        indexes = [
            models.Index(fields=["curso", "disciplina"]),
        ]

    def __str__(self):
        return f"{self.serie} • {self.curso} • {self.disciplina}"


class EdicaoLinha(models.Model):
    serie = models.CharField(max_length=200, blank=True, default="")
    curso = models.CharField(max_length=200)
    disciplina = models.CharField(max_length=200)
    cortes_disponiveis = models.PositiveIntegerField(null=True, blank=True)
    roteiros_feitos = models.PositiveIntegerField(null=True, blank=True)
    roteiros_revisados = models.PositiveIntegerField(null=True, blank=True)
    cortes_pendentes = models.PositiveIntegerField(null=True, blank=True)
    situacao_edicao = models.CharField(max_length=200, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Linha de Edição"
        verbose_name_plural = "Cortes/Roteiros/Edição (linhas)"
        unique_together = (("serie", "curso", "disciplina"),)
        indexes = [
            models.Index(fields=["curso", "disciplina"]),
        ]

    def __str__(self):
        return f"{self.serie} • {self.curso} • {self.disciplina}"


class MateriaisLinha(models.Model):
    serie = models.CharField(max_length=200, blank=True, default="")
    curso = models.CharField(max_length=200)
    disciplina = models.CharField(max_length=200)
    # conforme sua decisão: apenas status (dois booleans)
    produzidos = models.BooleanField(default=False)
    formatados = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Linha de Materiais"
        verbose_name_plural = "Materiais (linhas)"
        unique_together = (("serie", "curso", "disciplina"),)
        indexes = [
            models.Index(fields=["curso", "disciplina"]),
        ]

    def __str__(self):
        return f"{self.serie} • {self.curso} • {self.disciplina}"


class EntregavelLinha(models.Model):
    entregavel = models.CharField(max_length=200, unique=True)
    itens_do_entregavel = models.PositiveIntegerField(null=True, blank=True)
    percentual_do_orcamento = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    valor_do_orcamento = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entregável"
        verbose_name_plural = "Entregáveis"

    def __str__(self):
        return self.entregavel        
