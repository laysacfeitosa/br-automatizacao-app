import os
import gspread
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
        
SHEET_ID = os.getenv("SHEET_ID")
SA_FILE = os.getenv("GOOGLE_SA_FILE") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

ABA_GRAVACAO = "GRAVAÇÃO"
ABA_CORTES = "CORTES, ROTEIROS E EDIÇÃO"
ABA_ENTREGAVEIS = "ENTREGÁVEIS"
ABA_MATERIAIS = "MATERIAIS"

class Command(BaseCommand):
    help = "Sincroniza dados da planilha mestre"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--project")

    def handle(self, *args, **opts):
        auto = Automacao.objects.create(
            tipo="sync_sheet",
            status=Automacao.Status.PENDENTE,
            dry_run=opts["dry_run"],
            projeto=opts.get("project") or "-"
        )

        try:
            self.stdout.write("[sync_sheet] Iniciando...")
            gc = gspread.service_account(filename=SA_FILE)
            sh = gc.open_by_key(SHEET_ID)

            # --- GRAVAÇÃO ---
            ws = sh.worksheet(ABA_GRAVACAO)
            rows = ws.get_all_records()  # usa a linha 1 como header

            # Exemplo simples de validação
            grav_total = len(rows)
            ok_keys = {"curso","disciplina","serie","carga_horaria",
                       "aulas_gravadas","situacao_gravacao","percentual"}

            # garante que as chaves existem (nomes exatos)
            missing = ok_keys - set(map(str.lower, rows[0].keys())) if rows else set()
            if missing:
                raise ValueError(f"Colunas ausentes em GRAVAÇÃO: {missing}")

            # Só imprimir um resumo por enquanto (dry-run)
            done = sum(1 for r in rows
                       if str(r.get("percentual","0")).strip().replace("%","") not in ("0","0,00","0.00"))

            self.stdout.write(f"[gravação] linhas: {grav_total}  com progresso>0: {done}")

            # TODO: repetir a leitura para as outras abas conforme os nomes acima

            if not opts["dry_run"]:
                # TODO: aqui a gente insere/atualiza no banco (próxima etapa)
                pass

            auto.status = Automacao.Status.CONCLUIDA
            auto.sucesso = True
            auto.mensagem = "Leitura concluída"
        except Exception as e:
            auto.status = Automacao.Status.FALHOU
            auto.sucesso = False
            auto.erros = str(e)
            self.stderr.write(self.style.ERROR(str(e)))
        finally:
            auto.finished_at = timezone.now()
            auto.save()
            self.stdout.write("[sync_sheet] Finalizado")    