# automacoes/management/commands/sync_sheet.py
from django.core.management.base import BaseCommand, CommandParser

class Command(BaseCommand):
    help = "Sincroniza dados da planilha para o banco (stub de teste)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Não grava no BD; apenas executa leitura/validações."
        )
        parser.add_argument(
            "--project",
            default=None,
            help="Opcional: filtra por projeto específico."
        )

    def handle(self, *args, **options):
        dry = options.get("dry_run", False)
        project = options.get("project")

        self.stdout.write(self.style.NOTICE("[sync_sheet] Iniciando..."))
        self.stdout.write(f"  dry_run={dry}  project={project}")

        # TODO: aqui depois entra a lógica real (ler Google Sheets e gravar no BD)

        self.stdout.write(self.style.SUCCESS("[sync_sheet] Finalizado com sucesso"))
        return 0