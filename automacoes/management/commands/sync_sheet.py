import os
import gspread
from django.core.management.base import BaseCommand
from django.utils import timezone
from automacoes.models import Automacao

# ---- ENV: compatível com o que você configurou no Render ----
SHEET_ID = os.getenv("GOOGLE_SHEET_ID") or os.getenv("SHEET_ID")
SA_FILE  = (
    os.getenv("GOOGLE_CREDENTIALS_FILE")
    or os.getenv("GOOGLE_SA_FILE")
    or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
)

# ---- Nomes das abas (iguais aos da planilha) ----
ABA_GRAVACAO     = "GRAVAÇÃO"
ABA_CORTES       = "CORTES, ROTEIROS E EDIÇÃO"
ABA_ENTREGAVEIS  = "ENTREGÁVEIS"
ABA_MATERIAIS    = "MATERIAIS"

class Command(BaseCommand):
    help = "Sincroniza dados da planilha mestre"

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
                "Variáveis de ambiente ausentes. "
                "Defina GOOGLE_CREDENTIALS_FILE (ou GOOGLE_SA_FILE/GOOGLE_APPLICATION_CREDENTIALS) "
                "e GOOGLE_SHEET_ID (ou SHEET_ID)."
            )

        # Registro da execução (começa pendente)
        auto = Automacao.objects.create(
            tipo="sync_sheet",
            status=Automacao.Status.PENDENTE,
            dry_run=dry,          # <-- boolean
            projeto=project,
            sucesso=False,        # <-- boolean
            mensagem="",
            erros="",
        )

        try:
            # Marca em execução
            auto.status = Automacao.Status.EM_EXECUCAO if hasattr(Automacao.Status, "EM_EXECUCAO") else Automacao.Status.PENDENTE
            auto.save(update_fields=["status"])

            # Conecta no Sheets
            gc = gspread.service_account(filename=SA_FILE)
            sh = gc.open_by_key(SHEET_ID)

            # ---------- GRAVAÇÃO ----------
            ws = sh.worksheet(ABA_GRAVACAO)
            rows = ws.get_all_records()  # usa a linha 1 como header

            grav_total = len(rows)
            # Validação mínima dos campos esperados
            ok_keys = {"curso","disciplina","serie","carga_horaria",
                       "aulas_gravadas","situacao_gravacao","percentual"}
            missing = ok_keys - set(map(str.lower, rows[0].keys())) if rows else set()
            if missing:
                raise ValueError(f"Colunas ausentes em GRAVAÇÃO: {missing}")

            # Resumo simples
            with_progress = sum(
                1 for r in rows
                if str(r.get("percentual", "0")).strip().replace("%", "").replace(",", ".") not in ("0", "0.0", "0.00")
            )
            self.stdout.write(f"[gravação] linhas: {grav_total}  com progresso>0: {with_progress}")

            # TODO: Ler as demais abas (CORTES..., ENTREGÁVEIS, MATERIAIS) e preparar os inserts/updates

            if not dry:
                # TODO: Persistir no banco as leituras feitas (próxima etapa)
                pass

            # Sucesso
            auto.status = Automacao.Status.CONCLUIDA
            auto.sucesso = True                   # <-- boolean
            auto.mensagem = f"Leitura concluída (dry_run={dry}). GRAVAÇÃO: {grav_total} linhas."
        except Exception as e:
            auto.status = Automacao.Status.FALHOU
            auto.sucesso = False                  # <-- boolean
            auto.erros = str(e)                   # <-- texto, não inteiro
            self.stderr.write(self.style.ERROR(str(e)))
        finally:
            auto.finished_at = timezone.now()
            auto.save(update_fields=["status","sucesso","mensagem","erros","finished_at"])
            self.stdout.write("[sync_sheet] Finalizado")