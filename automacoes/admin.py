from django.contrib import admin
from .models import Automacao
from .models import (
    ProjetoDados, GravacaoLinha, EdicaoLinha, MateriaisLinha, EntregavelLinha
)

@admin.register(Automacao)
class AutomacaoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'tipo', 'projeto', 'status', 'dry_run', 'started_at', 'finished_at')
    list_filter   = ('status', 'tipo', 'dry_run', 'started_at')
    search_fields = ('tipo', 'projeto', 'mensagem')
    readonly_fields = ('started_at', 'finished_at')

@admin.register(ProjetoDados)
class ProjetoDadosAdmin(admin.ModelAdmin):
    list_display = ("orgao", "receita_total", "data_de_inicio", "prazo_de_vencimento", "total_de_aulas", "updated_at")
    search_fields = ("orgao",)


@admin.register(GravacaoLinha)
class GravacaoLinhaAdmin(admin.ModelAdmin):
    list_display = ("serie", "curso", "disciplina", "carga_horaria", "aulas_gravadas", "percentual", "situacao_gravacao", "updated_at")
    search_fields = ("serie", "curso", "disciplina")
    list_filter = ("situacao_gravacao",)


@admin.register(EdicaoLinha)
class EdicaoLinhaAdmin(admin.ModelAdmin):
    list_display = ("serie", "curso", "disciplina", "cortes_disponiveis", "roteiros_feitos", "roteiros_revisados", "cortes_pendentes", "situacao_edicao", "updated_at")
    search_fields = ("serie", "curso", "disciplina")
    list_filter = ("situacao_edicao",)


@admin.register(MateriaisLinha)
class MateriaisLinhaAdmin(admin.ModelAdmin):
    list_display = ("serie", "curso", "disciplina", "produzidos", "formatados", "updated_at")
    search_fields = ("serie", "curso", "disciplina")
    list_filter = ("produzidos", "formatados")


@admin.register(EntregavelLinha)
class EntregavelLinhaAdmin(admin.ModelAdmin):
    list_display = ("entregavel", "itens_do_entregavel", "percentual_do_orcamento", "valor_do_orcamento", "updated_at")
    search_fields = ("entregavel",)