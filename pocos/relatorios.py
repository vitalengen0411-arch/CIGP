from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.db.models import Q
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def formatar_valor(valor):
    if valor is None or valor == "":
        return "Não informado"

    if isinstance(valor, bool):
        return "Sim" if valor else "Não"

    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)

        return valor.strftime("%d/%m/%Y %H:%M")

    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    if isinstance(valor, Decimal):
        return format(valor, "f").replace(".", ",")

    return str(valor)


def formatar_vazao(valor):
    if valor is None or valor == "":
        return "Não informado"

    texto = format(Decimal(str(valor)), "f")

    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")

    return texto.replace(".", ",")


def gerar_pdf_poco(poco):
    arquivo = BytesIO()

    documento = SimpleDocTemplate(
        arquivo,
        pagesize=A4,
        rightMargin=1.3 * cm,
        leftMargin=1.3 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.3 * cm,
        title=f"Registro do poço {poco.identificacao}",
    )

    estilos = getSampleStyleSheet()

    estilos["Normal"].fontSize = 8
    estilos["Normal"].leading = 10
    estilos["Normal"].spaceAfter = 0
    estilos["Normal"].splitLongWords = True

    estilos["Title"].fontSize = 12
    estilos["Title"].leading = 15
    estilos["Title"].spaceAfter = 5

    estilos["Heading2"].fontSize = 10
    estilos["Heading2"].leading = 12
    estilos["Heading2"].spaceBefore = 7
    estilos["Heading2"].spaceAfter = 4
    estilos["Heading2"].keepWithNext = True

    def paragrafo(texto):
        return Paragraph(
            escape(str(texto)).replace("\n", "<br/>"),
            estilos["Normal"],
        )

    conteudo = [
        Paragraph(
            "Central de Informações da Gerência de Pinheiro — CIGP",
            estilos["Title"],
        ),
        Paragraph(
            f"Registro do poço {escape(str(poco.identificacao))}",
            estilos["Heading2"],
        ),
        paragrafo(
            "Última atualização: "
            + formatar_valor(poco.atualizado_em)
        ),
        Spacer(1, 0.15 * cm),
    ]

    def aplicar_estilo(tabela, cabecalho=False):
        comandos = [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#cbd5da"),
            ),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        if cabecalho:
            comandos.append(
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#e5eef2"),
                )
            )
        else:
            comandos.append(
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#f5f8fa"),
                )
            )

        tabela.setStyle(TableStyle(comandos))

    def valor_campo(nome):
        campo = poco._meta.get_field(nome)
        valor = getattr(poco, nome)

        if nome == "cidade" and poco.sistema_id:
            valor = poco.sistema.cidade

        elif nome == "codigo_sistema" and poco.sistema_id:
            valor = poco.sistema.codigo

        if campo.choices and valor not in (None, ""):
            valor = getattr(poco, f"get_{nome}_display")()

        if nome == "mes_referencia" and valor:
            return valor.strftime("%m/%Y")

        if nome == "diametro_reducao":
            if poco.possui_reducao is False:
                return "Não se aplica"

        if nome in ("vazao", "exploracao_vazao"):
            return formatar_vazao(valor)

        return formatar_valor(valor)

    def adicionar_secao(titulo, campos, calculos=None):
        conteudo.append(
            Paragraph(titulo, estilos["Heading2"])
        )

        linhas = []

        for nome in campos:
            campo = poco._meta.get_field(nome)

            linhas.append([
                paragrafo(campo.verbose_name),
                paragrafo(valor_campo(nome)),
            ])

        for nome, valor, unidade in calculos or []:
            if valor is None:
                texto = "Não informado"
            else:
                texto = (
                    f"{valor:.2f}".replace(".", ",")
                    + f" {unidade}"
                )

            linhas.append([
                paragrafo(nome),
                paragrafo(texto),
            ])

        tabela = Table(
            linhas,
            colWidths=[
                documento.width * 0.38,
                documento.width * 0.62,
            ],
            hAlign="LEFT",
        )

        aplicar_estilo(tabela)
        conteudo.append(tabela)
        conteudo.append(Spacer(1, 0.12 * cm))

    adicionar_secao(
        "Identificação e localização",
        [
            "identificacao",
            "cidade",
            "codigo_sistema",
            "localidade_endereco",
        ],
    )

    adicionar_secao(
        "Características do poço",
        [
            "situacao_operacional",
            "destino_agua",
            "profundidade_poco",
            "diametro_poco",
            "quantidade_tubos",
            "tipo_tubo",
            "posicao_filtros",
            "possui_reducao",
            "diametro_reducao",
            "nivel_estatico",
            "nivel_dinamico",
            "observacoes_poco",
        ],
        calculos=[
            (
                "Rebaixamento do poço (m)",
                poco.rebaixamento,
                "m",
            ),
        ],
    )

    conteudo.append(
        paragrafo(
            "Rebaixamento = nível dinâmico − nível estático."
        )
    )

    adicionar_secao(
        "Conjunto motor-bomba — CMB",
        [
            "marca_cmb",
            "modelo_cmb",
            "potencia_cmb",
            "unidade_potencia",
            "tensao_nominal",
            "crivo",
        ],
    )

    conteudo.append(
        Paragraph(
            "Condições de exploração",
            estilos["Heading2"],
        )
    )

    linhas_exploracao = [
        [
            paragrafo("Data da coleta"),
            paragrafo("Vazão (m³/h)"),
            paragrafo("Nível dinâmico (m)"),
            paragrafo("Colocação da bomba/submersa (m)"),
        ]
    ]

    for item in poco.condicoes_exploracao.all():
        linhas_exploracao.append([
            paragrafo(
                item.data_coleta.strftime("%d/%m/%Y")
                if item.data_coleta is not None
                else "Não informada"
            ),
            paragrafo(formatar_vazao(item.vazao)),
            paragrafo(formatar_valor(item.nivel_dinamico)),
            paragrafo(formatar_valor(item.colocacao_bomba)),
        ])

    if len(linhas_exploracao) > 1:
        tabela_exploracao = Table(
            linhas_exploracao,
            colWidths=[
                documento.width * 0.20,
                documento.width * 0.20,
                documento.width * 0.25,
                documento.width * 0.35,
            ],
            repeatRows=1,
            hAlign="LEFT",
        )

        aplicar_estilo(tabela_exploracao, cabecalho=True)
        conteudo.append(tabela_exploracao)
    else:
        conteudo.append(
            paragrafo(
                "Nenhuma condição de exploração cadastrada."
            )
        )

    conteudo.append(Spacer(1, 0.12 * cm))

    adicionar_secao(
        "Operação mensal",
        [
            "mes_referencia",
            "horas_trabalhadas",
            "vazao",
        ],
        calculos=[
            (
                "Média de horas trabalhadas por dia",
                poco.dias_trabalhados,
                "h/dia",
            ),
            (
                "Volume aduzido no mês",
                poco.volume_aduzido,
                "m³",
            ),
        ],
    )

    conteudo.append(
        paragrafo(
            "Média de horas por dia = horas trabalhadas no mês "
            "÷ quantidade de dias do mês de referência. "
            "Volume aduzido = vazão × horas trabalhadas, "
            "considerando a vazão constante no período."
        )
    )

    # Eventos informados na seção Evento para o histórico.
    # Inclui também os tipos de eventos usados anteriormente.
    tipos_eventos = [
        "instalacao_novo_cmb",
        "quadro_comando",
        "cabo_partido",
        "tubo_furado",
        "cmb_antigo",
        "outros",
        "instalacao",
        "retirada",
        "manutencao",
        "outro",
    ]

    eventos_recentes = list(
        poco.historicos
        .filter(
            Q(dados__evento_manual=True)
            | Q(tipo_evento__in=tipos_eventos)
        )
        .exclude(
            tipo_evento="outro",
            descricao__startswith=(
                "Estado do cadastro antes da primeira"
            ),
        )
        .order_by("-registrado_em", "-pk")[:3]
    )

    conteudo.append(
        Paragraph(
            "Últimos eventos do histórico",
            estilos["Heading2"],
        )
    )

    if eventos_recentes:
        linhas_eventos = [
            [
                paragrafo("Data do registro"),
                paragrafo("Evento"),
                paragrafo("Descrição"),
            ]
        ]

        for evento in eventos_recentes:
            dados = evento.dados or {}

            if dados.get("evento_manual"):
                descricao = dados.get(
                    "descricao_evento",
                    evento.descricao,
                )
            else:
                # Retira os textos automáticos acrescentados
                # ao final das descrições no formato antigo.
                partes = []

                for parte in (evento.descricao or "").split("\n\n"):
                    texto = parte.strip()

                    if not texto:
                        continue

                    if texto.startswith("Campos alterados:"):
                        continue

                    if texto == "Condições de exploração atualizadas.":
                        continue

                    if texto.startswith("Fotos anexadas ao evento:"):
                        continue

                    if texto == "Cadastro inicial do poço.":
                        continue

                    partes.append(parte)

                descricao = "\n\n".join(partes)

            linhas_eventos.append([
                paragrafo(formatar_valor(evento.registrado_em)),
                paragrafo(evento.get_tipo_evento_display()),
                paragrafo(descricao or "Sem descrição."),
            ])

        tabela_eventos = Table(
            linhas_eventos,
            colWidths=[
                documento.width * 0.20,
                documento.width * 0.25,
                documento.width * 0.55,
            ],
            repeatRows=1,
            splitInRow=1,
            hAlign="LEFT",
        )

        aplicar_estilo(tabela_eventos, cabecalho=True)
        conteudo.append(tabela_eventos)
    else:
        conteudo.append(
            paragrafo("Nenhum evento informado até o momento.")
        )

    conteudo.append(Spacer(1, 0.12 * cm))

    adicionar_secao(
        "Datas do cadastro",
        [
            "criado_em",
            "atualizado_em",
        ],
    )

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#536d78"))

        canvas.drawString(
            documento.leftMargin,
            0.7 * cm,
            "CIGP — Registro do Poço",
        )

        canvas.drawRightString(
            A4[0] - documento.rightMargin,
            0.7 * cm,
            f"Página {doc.page}",
        )

        canvas.restoreState()

    documento.build(
        conteudo,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    arquivo.seek(0)
    return arquivo