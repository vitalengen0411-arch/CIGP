from calendar import monthrange
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


def campo_decimal(nome, casas=2):
    return models.DecimalField(
        nome,
        max_digits=12,
        decimal_places=casas,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0"))],
    )


class Sistema(models.Model):
    cidade = models.CharField(
        "Sistema / Cidade",
        max_length=100,
        unique=True,
    )

    codigo = models.CharField(
        "Código do sistema",
        max_length=3,
        unique=True,
    )

    class Meta:
        verbose_name = "Sistema"
        verbose_name_plural = "Sistemas"
        ordering = ["cidade"]

    def __str__(self):
        return f"{self.cidade} — {self.codigo}"


class Poco(models.Model):
    sistema = models.ForeignKey(
        Sistema,
        verbose_name="Sistema",
        on_delete=models.PROTECT,
        related_name="pocos",
        blank=True,
        null=True,
    )

    # Identificação
    identificacao = models.CharField(
        "Identificação do poço",
        max_length=20,
    )

    cidade = models.CharField(
        "Cidade",
        max_length=100,
    )

    codigo_sistema = models.CharField(
        "Código do sistema",
        max_length=3,
    )

    localidade_endereco = models.TextField(
        "Localidade / Endereço",
        blank=True,
    )

    situacao_operacional = models.CharField(
        "Situação operacional",
        max_length=30,
        choices=[
            ("operando", "Operando"),
            ("parado", "Parado"),
            ("manutencao", "Em manutenção"),
            ("desativado", "Desativado"),
        ],
        blank=True,
    )

    # Características do poço
    profundidade_poco = campo_decimal(
        "Profundidade do poço (m)"
    )

    diametro_poco = campo_decimal(
        "Diâmetro do poço (polegadas)"
    )

    destino_agua = models.CharField(
        "Destino da água",
        max_length=20,
        choices=[
            ("reservatorio", "Reservatório"),
            ("rede", "Rede"),
        ],
        blank=True,
    )

    posicao_filtros = models.TextField(
        "Posição dos filtros do poço (m)",
        blank=True,
        help_text=(
            "Informe os intervalos de profundidade. "
            "Exemplo: de 80 a 90 m; de 100 a 110 m."
        ),
    )

    possui_reducao = models.BooleanField(
        "Possui redução no poço?",
        blank=True,
        null=True,
    )

    diametro_reducao = campo_decimal(
        "Diâmetro após a redução (polegadas)"
    )

    quantidade_tubos = models.PositiveIntegerField(
        "Quantidade de tubos",
        blank=True,
        null=True,
    )

    tipo_tubo = models.CharField(
        "Material dos tubos",
        max_length=30,
        choices=[
            ("pvc_geomecanico", "PVC geomecânico"),
            ("aco_galvanizado", "Ferro galvanizado"),
            ("pvc_rigido", "PVC rígido"),
        ],
        blank=True,
    )

    # Conjunto motor-bomba
    marca_cmb = models.CharField(
        "Marca do CMB",
        max_length=100,
        blank=True,
    )

    modelo_cmb = models.CharField(
        "Modelo do CMB",
        max_length=100,
        blank=True,
    )

    potencia_cmb = campo_decimal("Potência do CMB")

    unidade_potencia = models.CharField(
        "Unidade de potência",
        max_length=2,
        choices=[
            ("cv", "cv"),
            ("hp", "hp"),
            ("kW", "kW"),
        ],
        blank=True,
    )

    tensao_nominal = campo_decimal(
        "Tensão nominal (V)"
    )

    crivo = campo_decimal("Crivo (m)")

    # Operação mensal
    mes_referencia = models.DateField(
        "Mês de referência da operação",
        blank=True,
        null=True,
        help_text=(
            "Informe o primeiro dia do mês. "
            "Exemplo: 01/10/2026 para outubro de 2026."
        ),
    )

    horas_trabalhadas = campo_decimal(
        "Horas trabalhadas no mês (h)"
    )

    vazao = campo_decimal(
        "Vazão (m³/h)",
        casas=3,
    )

    # Níveis do poço
    nivel_estatico = campo_decimal(
        "Nível estático (m)"
    )

    nivel_dinamico = campo_decimal(
        "Nível dinâmico (m)"
    )

    # Campos antigos mantidos no banco
    exploracao_vazao = campo_decimal(
        "Condição de exploração — Vazão (m³/h)",
        casas=3,
    )

    exploracao_nivel_dinamico = campo_decimal(
        "Condição de exploração — Nível dinâmico (m)"
    )

    exploracao_colocacao_bomba = campo_decimal(
        "Condição de exploração — Colocação da bomba (m)"
    )

    # Observações
    observacoes_poco = models.TextField(
        "Observações do poço",
        blank=True,
    )

    observacoes_cmb = models.TextField(
        "Observações do CMB",
        blank=True,
    )

    observacoes_operacao = models.TextField(
        "Observações da operação",
        blank=True,
    )

    # Datas do cadastro
    criado_em = models.DateTimeField(
        "Data de inclusão",
        auto_now_add=True,
        null=True,
        blank=True,
    )

    atualizado_em = models.DateTimeField(
        "Última atualização",
        auto_now=True,
    )

    # Cálculos automáticos
    @property
    def dias_trabalhados(self):
        if (
            self.horas_trabalhadas is None
            or self.mes_referencia is None
        ):
            return None

        dias_do_mes = monthrange(
            self.mes_referencia.year,
            self.mes_referencia.month,
        )[1]

        return self.horas_trabalhadas / Decimal(dias_do_mes)

    @property
    def volume_aduzido(self):
        if self.vazao is None or self.horas_trabalhadas is None:
            return None

        return self.vazao * self.horas_trabalhadas

    @property
    def rebaixamento(self):
        if self.nivel_dinamico is None or self.nivel_estatico is None:
            return None

        return self.nivel_dinamico - self.nivel_estatico

    class Meta:
        verbose_name = "Poço"
        verbose_name_plural = "Poços"
        ordering = ["cidade", "identificacao"]

        constraints = [
            models.UniqueConstraint(
                fields=["codigo_sistema", "identificacao"],
                name="poco_unico_por_sistema",
            )
        ]

    def __str__(self):
        return (
            f"{self.identificacao} — {self.cidade} "
            f"({self.codigo_sistema})"
        )


class HistoricoPoco(models.Model):
    poco = models.ForeignKey(
        Poco,
        on_delete=models.PROTECT,
        related_name="historicos",
        verbose_name="Poço",
    )

    registrado_em = models.DateTimeField(
        "Data do registro",
        auto_now_add=True,
    )

    tipo_evento = models.CharField(
        "Tipo de evento",
        max_length=30,
        choices=[
            ("cadastro", "Cadastro inicial"),
            ("atualizacao", "Atualização do cadastro"),
            ("instalacao_novo_cmb", "Instalação de novo CMB"),
            ("quadro_comando", "Quadro de Comando - QC"),
            ("cabo_partido", "Cabo partido"),
            ("tubo_furado", "Tubo furado"),
            ("cmb_antigo", "CMB antigo"),
            ("outros", "Outros"),
            ("instalacao", "Instalação de CMB"),
            ("retirada", "Retirada de CMB"),
            ("manutencao", "Manutenção"),
            ("outro", "Outro evento"),
        ],
        default="atualizacao",
    )

    descricao = models.TextField(
        "Descrição do evento",
        blank=True,
    )

    responsavel = models.CharField(
        "Responsável pelo registro",
        max_length=150,
        blank=True,
    )

    dados = models.JSONField(
        "Dados do poço na ocasião",
        default=dict,
        blank=True,
    )

    class Meta:
        verbose_name = "Histórico do poço"
        verbose_name_plural = "Históricos dos poços"
        ordering = ["-registrado_em", "-pk"]

    def __str__(self):
        return (
            f"{self.poco.identificacao} — "
            f"{self.get_tipo_evento_display()}"
        )


class CondicaoExploracao(models.Model):
    poco = models.ForeignKey(
        Poco,
        on_delete=models.CASCADE,
        related_name="condicoes_exploracao",
        verbose_name="Poço",
    )

    data_coleta = models.DateField(
        "Data da coleta",
        blank=True,
        null=True,
    )

    vazao = campo_decimal(
        "Vazão (m³/h)",
        casas=3,
    )

    nivel_dinamico = campo_decimal(
        "Nível dinâmico (m)",
    )

    colocacao_bomba = campo_decimal(
        "Colocação da bomba/submersa (m)",
    )

    class Meta:
        verbose_name = "Condição de exploração"
        verbose_name_plural = "Condições de exploração"

        ordering = [
            models.F("colocacao_bomba").asc(nulls_last=True),
            "pk",
        ]

    def __str__(self):
        return (
            f"Condição de exploração — "
            f"{self.poco.identificacao}"
        )


class FotoEvento(models.Model):
    evento = models.ForeignKey(
        HistoricoPoco,
        on_delete=models.CASCADE,
        related_name="fotos",
        verbose_name="Evento",
    )

    imagem = models.ImageField(
        "Foto",
        upload_to="eventos/%Y/%m/",
    )

    enviada_em = models.DateTimeField(
        "Data do envio",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Foto do evento"
        verbose_name_plural = "Fotos dos eventos"
        ordering = ["enviada_em", "pk"]

    def __str__(self):
        return (
            f"Foto do evento {self.evento_id} "
            f"— {self.evento.poco.identificacao}"
        )
class Eta(models.Model):
    sistema = models.ForeignKey(
        Sistema,
        on_delete=models.PROTECT,
        related_name="etas",
        verbose_name="Sistema",
    )

    nome = models.CharField(
        "Nome da ETA",
        max_length=150,
        help_text="Exemplo: ETA 1, ETA 2 ou ETA de Alcântara.",
    )

    endereco = models.TextField(
        "Endereço",
        blank=True,
    )

    situacao_operacional = models.CharField(
        "Situação operacional",
        max_length=20,
        choices=[
            ("", "Não informada"),
            ("operando", "Operando"),
            ("parada", "Parada"),
            ("desativada", "Desativada"),
            ("manutencao", "Manutenção"),
        ],
        blank=True,
        default="",
    )

    observacoes = models.TextField(
        "Observações gerais",
        blank=True,
    )

    criado_em = models.DateTimeField(
        "Data de inclusão",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "Última atualização",
        auto_now=True,
    )

    class Meta:
        verbose_name = "ETA"
        verbose_name_plural = "ETAs"
        ordering = ["sistema__cidade", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["sistema", "nome"],
                name="eta_nome_unico_por_sistema",
            ),
        ]

    def __str__(self):
        return f"{self.nome} — {self.sistema.cidade}"