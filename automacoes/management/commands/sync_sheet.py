import os
import gspread
from django.core.management.base import BaseCommand
from django.utils import timezone
from automacoes.models import Automacao

# --- Ler variáveis de ambiente (com fallback) ---
SHEET_ID = os.getenv("GOOGLE_SHEET_ID") or os.getenv("SHEET_ID")
SA_FILE  = (
    os.getenv("GOOGLE_CREDENTIALS_FILE")
    or os.getenv("GOOGLE_SA_FILE")
    or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)

ABA_GRAVACAO     = "GRAVAÇÃO"
ABA_CORTES       = "CORTES, ROTEIROS E EDIÇÃO"
ABA_ENTREGAVEIS  = "ENTREGÁVEIS"
ABA_MATERIAIS    = "MATERIAIS"

# --- Compatibilidade com modelos antigos (STATUS_*) e novos (.Status.*) ---
def _status(name: str, default=None):
    """
    Tenta Automacao.Status.NAME; se não existir, tenta Automacao.STATUS_NAME;
    senão, usa 'default'.
    """
    if hasattr(Automacao, "Status") and hasattr(Automacao.Status, name):
        return getattr(Automacao.Status, name)
    legacy = f"STATUS_{name}"
    if hasattr(Automacao, legacy):
        return getattr(Automacao, legacy)
    return default

STATUS_PENDENTE    = _status("PENDENTE", None)
STATUS_EXECUCAO    = _status("EM_EXECUCAO", STATUS_PENDENTE)
STATUS_CONCLUIDA   = _status("CONCLUIDA", STATUS_PENDENTE)
STATUS_FALHOU      = _status("FALHOU",   STATUS_PENDENTE)

class Command(BaseCommand):
    help = "Sincroniza dados da planilha mestre (Google Sheets) com o banco"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--project")

    def handle(self, *args, **opts):
        dry = bool(opts.get("dry_run", False))
        project = opts.get("project") or "-"

        self.stdout.write("[sync_sheet] Iniciando...")
        self.stdout.write(f"  dry_run={dry}  project={project}")

        if not SA_FILE or not SHEET_ID:
            raise RuntimeError(
                "Variáveis ausentes. Defina GOOGLE_CREDENTIALS_FILE (ou GOOGLE_SA_FILE/GOOGLE_APPLICATION_CREDENTIALS) "
                "e GOOGLE_SHEET_ID (ou SHEET_ID)."
            )

        # cria o registro da execução (booleans de verdade!)
        auto = Automacao.objects.create(
            tipo="sync_sheet",
            projeto=project,
            dry_run=dry,
            status=STATUS_PENDENTE,
            sucesso=False,
            mensagem="",
            erros="",
        )

        try:
            # marca em execução
            if STATUS_EXECUCAO is not None:
                auto.status = STATUS_EXECUCAO
                auto.save(update_fields=["status"])

            # conecta ao Google Sheets
            gc = gspread.service_account(filename=SA_FILE)
            sh = gc.open_by_key(SHEET_ID)

            # --- GRAVAÇÃO ---
            ws = sh.worksheet(ABA_GRAVACAO)
            rows = ws.get_all_records()

            grav_total = len(rows)
            ok_keys = {"curso","disciplina","serie","carga_horaria",
                       "aulas_gravadas","situacao_gravacao","percentual"}
            missing = ok_keys - set(map(str.lower, rows[0].keys())) if rows else set()
            if missing:
                raise ValueError(f"Colunas ausentes em GRAVAÇÃO: {missing}")

            with_progress = sum(
                1 for r in rows
                if str(r.get("percentual", "0")).strip().replace("%", "").replace(",", ".") not in ("0", "0.0", "0.00")
            )
            self.stdout.write(f"[gravação] linhas: {grav_total}  com progresso>0: {with_progress}")

            # TODO: ler demais abas e (se not dry) persistir no banco

            # sucesso
            auto.status   = STATUS_CONCLUIDA
            auto.sucesso  = True
            auto.mensagem = f"Leitura concluída (dry_run={dry}). GRAVAÇÃO: {grav_total} linhas."
        except Exception as e:
            auto.status   = STATUS_FALHOU
            auto.sucesso  = False
            auto.erros    = str(e)
            self.stderr.write(self.style.ERROR(str(e)))
        finally:
            auto.finished_at = timezone.now()
            auto.save(update_fields=["status","sucesso","mensagem","erros","finished_at"])
            self.stdout.write("[sync_sheet] Finalizado")
