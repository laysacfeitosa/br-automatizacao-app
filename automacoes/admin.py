from django.contrib import admin
from .models import Automacao

@admin.register(Automacao)
class AutomacaoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'tipo', 'projeto', 'status', 'dry_run', 'started_at', 'finished_at')
    list_filter   = ('status', 'tipo', 'dry_run', 'started_at')
    search_fields = ('tipo', 'projeto', 'mensagem')
    readonly_fields = ('started_at', 'finished_at')
