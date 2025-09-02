from django.core.management.base import BaseCommand
from django.utils import timezone
from automacoes.models import Automacao

class Command(BaseCommand):
    help = 'Sincroniza a planilha mestre (Google Sheets) com o banco.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False)
        parser.add_argument('--project', dest='project', default=None)

    def handle(self, *args, **opts):
        self.stdout.write('[sync_sheet] Iniciando...')
        self.stdout.write(f"  dry_run={opts['dry_run']}  project={opts.get('project')}")

        # cria registro da execução
        run = Automacao.objects.create(
            tipo='sync_sheet',
            projeto=opts.get('project') or '',
            dry_run=opts['dry_run'],
            status=Automacao.STATUS_EXECUCAO,
        )

        try:
            # >>> Aqui entrará o ETL de verdade (ler Sheets, escrever no DB).
            # Por enquanto, é só um “placeholder”:
            linhas_processadas = 0  # substitua quando integrar

            # marca como concluído
            run.status = Automacao.STATUS_CONCLUIDA
            run.mensagem = f'OK (placeholder). dry_run={opts["dry_run"]}. linhas={linhas_processadas}'
            run.sucesso = linhas_processadas
            run.finished_at = timezone.now()
            run.save(update_fields=['status', 'mensagem', 'sucesso', 'finished_at'])

            self.stdout.write(self.style.SUCCESS('[sync_sheet] Finalizado com sucesso'))

        except Exception as e:
            # em caso de erro, marca falha e relança
            run.status = Automacao.STATUS_FALHOU
            run.mensagem = str(e)
            run.erros = 1
            run.finished_at = timezone.now()
            run.save(update_fields=['status', 'mensagem', 'erros', 'finished_at'])
            raise