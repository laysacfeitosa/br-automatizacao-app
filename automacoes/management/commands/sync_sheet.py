import os
from decimal import Decimal, InvalidOperation

import gspread
from django.core.management.base import BaseCommand
from django.utils import timezone

from automacoes.models import Automacao, GravacaoLinha

def first_env(*names: str) -> str | None:
    """Retorna o primeiro env var não vazio dentre os nomes informados."""
    for n in names:
        v = os.getenv(n)
        if v and str(v).strip():
            return v
    return None


def to_int(x, default=None):
    """Converte para int tratando '', None, '1.234', '1,234' etc."""
    if x is None:
        return default
    s = str(x).strip()
    if not s:
        return default
    s = s.replace(".", "").replace(",", ".")
    try:
        # aceita "32", "32.0"
        return int(float(s))
    except ValueError:
        return default


def to_decimal(x, default=None):
    """Converte para Decimal('…') com vírgula/ponto."""
    if x is None:
        return default
    s = str(x).strip()
    if not s:
        return default
    s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return default


def parse_percent(x, default=None):
    """Converte '100%', '62,50%' -> Decimal('100.00'). Sem símbolo: tenta como número."""
    if x is None:
        return default
    s = str(x).strip().replace("%", "")
    d = to_decimal(s, default)
    if d is None:
        return default
    # normaliza para duas casas
    return d.quantize(Decimal("0.01"))


# -------------------------
# Config da Planilha
# -------------------------
SHEET_ID = first_env("GOOGLE_SHEET_ID", "SHEET_ID")
SA_FILE = first_env(
    "GOOGLE_CREDENTIALS_FILE",  # como está no Render
    "GOOGLE_SA_FILE",           # como você usou localmente antes
    "GOOGLE_APPLICATION_CREDENTIALS",
)

ABA_GRAVACAO = "GRAVAÇÃO"
# as demais abas virão nas próximas etapas:
# ABA_CORTES = "CORTES, ROTEIROS E EDIÇÃO"
# ABA_ENTREGAVEIS = "ENTREGÁVEIS"
# ABA_MATERIAIS = "MATERIAIS"


class Command(BaseCommand):
    help = "Sincroniza dados da planilha mestre (por enquanto: GRAVAÇÃO)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", default=False)
        parser.add_argument("--project", dest="project", default="-")

    # --------------- ETL ---------------
    def handle(self, *args, **opts):
        self.stdout.write("[sync_sheet] Iniciando...")
        self.stdout.write(f"  dry_run={opts['dry_run']}  project={opts.get('project')}")

        # registra execução
        run = Automacao.objects.create(
            tipo="sync_sheet",
            projeto=opts.get("project") or "-",
            dry_run=opts["dry_run"],
            status=getattr(Automacao, "STATUS_EXECUCAO", "Em execução"),
            started_at=timezone.now(),
        )

        try:
            # 1) Conecta na planilha
            if not SA_FILE or not SHEET_ID:
                raise RuntimeError(
                    "Variáveis de ambiente ausentes: "
                    "GOOGLE_CREDENTIALS_FILE/GOOGLE_SHEET_ID (ou equivalentes)."
                )
            gc = gspread.service_account(filename=SA_FILE)
            sh = gc.open_by_key(SHEET_ID)

            # 2) Lê a aba GRAVAÇÃO
            ws = sh.worksheet(ABA_GRAVACAO)
            rows = ws.get_all_records()  # usa linha 1 como header
            total = len(rows)

            # 3) Normaliza e mapeia linhas -> objetos GravacaoLinha
            # Espera colunas: curso, disciplina, serie, carga_horaria, aulas_gravadas,
            #                 situacao_gravacao, percentual
            objetivos = []
            skipped = 0  # quantas linhas vamos pular (vazias/sem dados)

            for r in rows:
                # como o get_all_records usa o header como chave, cuidamos de variação de caixa/acentos
                def gk(*keys):
                    for k in keys:
                        if k in r:
                            return r.get(k)
                        lk = k.lower()
                        if lk in r:
                            return r.get(lk)
                    return None

                curso = (gk("curso", "Curso") or "").strip()
                disciplina = (gk("disciplina", "Disciplina") or "").strip()

                # se a linha está claramente vazia (sem curso e sem disciplina), pulamos
                if not curso and not disciplina:
                    skipped += 1
                    continue

                    # defaults NÃO nulos para campos obrigatórios
                serie          = to_int(gk("serie", "Série"), default=0)
                carga_horaria  = to_int(gk("carga_horaria", "carga horaria", "CH"), default=0)
                aulas_gravadas = to_int(gk("aulas_gravadas", "aulas gravadas"), default=0)

                situacao = (gk("situacao_gravacao", "Situação_gravação", "situação_gravação", "situacao_gravação") or "").strip()
                percentual = parse_percent(gk("percentual", "PERCENTUAL", "%"), default=Decimal("0"))

                linha = GravacaoLinha(
                    curso=curso,
                    disciplina=disciplina,
                    serie=serie,
                    carga_horaria=carga_horaria,
                    aulas_gravadas=aulas_gravadas,
                    situacao_gravacao=situacao,
                    percentual=percentual,
                )
                objetivos.append(linha)

            if skipped:
                self.stdout.write(f"[gravação] linhas puladas (vazias/sem curso/disciplina): {skipped}")

            # 4) Mostra resumo
            com_progresso = sum(
                1
                for o in objetivos
                if (o.percentual or Decimal(0)) > Decimal(0)
            )
            self.stdout.write(f"[gravação] linhas lidas: {total} | com progresso > 0: {com_progresso}")

            # 5) Persiste se não for dry-run
            if not opts["dry_run"]:
                # política inicial simples: FULL RELOAD da staging
                GravacaoLinha.objects.all().delete()
                GravacaoLinha.objects.bulk_create(objetivos, batch_size=500)
                self.stdout.write(self.style.SUCCESS(f"[gravação] gravadas {len(objetivos)} linhas"))

            # 6) Marca execução OK
            run.status = getattr(Automacao, "STATUS_CONCLUIDA", "Concluída")
            run.sucesso = True
            run.mensagem = f"GRAVAÇÃO: lidas={total}, progresso>0={com_progresso}, persisted={'no' if opts['dry_run'] else 'yes'}"

        except Exception as e:
            # marca falha e propaga
            run.status = getattr(Automacao, "STATUS_FALHOU", "FALHOU")
            run.sucesso = False
            run.erros = str(e)
            self.stderr.write(self.style.ERROR(str(e)))
            raise

        finally:
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "sucesso", "mensagem", "erros", "finished_at"])
            self.stdout.write("[sync_sheet] Finalizado")
