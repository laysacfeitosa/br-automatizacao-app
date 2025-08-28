from django.contrib import admin

from django.contrib import admin
from .models import Automacao

@admin.register(Automacao)
class AutomacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'status', 'criado_em', 'atualizado_em')
    list_filter = ('status', 'criado_em')
    search_fields = ('nome', 'descricao')
    ordering = ('-criado_em',)
