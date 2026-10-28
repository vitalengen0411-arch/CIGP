from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .forms import CondicaoExploracaoForm, PocoForm
from .historico import registrar_historico
from .models import CondicaoExploracao, FotoEvento, Poco, Sistema


class CondicaoExploracaoInline(admin.TabularInline):
    model = CondicaoExploracao
    form = CondicaoExploracaoForm

    fields = (
        "data_coleta",
        "vazao",
        "nivel_dinamico",
        "colocacao_bomba",
    )

    extra = 0

    verbose_name = "Condição de exploração"
    verbose_name_plural = "Condições de exploração"


@admin.register(Poco)
class PocoAdmin(admin.ModelAdmin):
    form = PocoForm
    inlines = (CondicaoExploracaoInline,)

    change_list_template = "lista_admin.html"
    change_form_template = "editar_poco_admin.html"

    list_display = (
        "acao_historico",
        "data_inclusao",
        "ultima_vazao",
        "sigla",
        "nome_sistema",
        "codigo",
        "unidade_negocio",
        "abrir_registro",
        "status_poco",
        "indicador_status",
    )

    list_display_links = None
    list_select_related = ("sistema",)

    search_fields = ()
    actions = None
    list_filter = ()

    readonly_fields = (
        "dias_operacao",
        "aduzido_mes",
        "rebaixamento_calculado",
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Identificação e localização",
            {
                "fields": (
                    "identificacao",
                    "sistema",
                    "cidade",
                    "codigo_sistema",
                    "localidade_endereco",
                ),
            },
        ),
        (
            "Características do poço",
            {
                "fields": (
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
                    "rebaixamento_calculado",
                    "observacoes_poco",
                ),
            },
        ),
        (
            "Conjunto Motor-Bomba — CMB",
            {
                "fields": (
                    "marca_cmb",
                    "modelo_cmb",
                    "potencia_cmb",
                    "unidade_potencia",
                    "tensao_nominal",
                    "crivo",
                ),
            },
        ),
        (
            "Operação mensal",
            {
                "fields": (
                    "mes_referencia",
                    "horas_trabalhadas",
                    "dias_operacao",
                    "vazao",
                    "aduzido_mes",
                ),
                "description": (
                    "A média de horas por dia é calculada conforme "
                    "o mês de referência. O volume aduzido é "
                    "calculado pela vazão multiplicada pelas horas."
                ),
            },
        ),
        (
            "Evento para o histórico",
            {
                "fields": (
                    "tipo_evento",
                    "descricao_evento",
                    "fotos_evento",
                ),
                "description": (
                    "Preencha esta seção para registrar um evento "
                    "no histórico. As fotos são opcionais, com limite "
                    "de 15 por evento. Para apenas atualizar o cadastro, "
                    "deixe esta seção vazia."
                ),
            },
        ),
        (
            "Datas do cadastro",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                ),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        contexto = dict(extra_context or {})

        contexto["sistemas_filtro"] = (
            Sistema.objects
            .exclude(codigo__in=["302", "363"])
            .order_by("cidade")
        )

        contexto["situacoes_filtro"] = (
            Poco._meta.get_field("situacao_operacional").choices
        )

        contexto["sistema_selecionado"] = request.GET.get(
            "sistema__id__exact",
            "",
        )

        contexto["sigla_pesquisada"] = request.GET.get(
            "identificacao__icontains",
            "",
        )

        contexto["situacao_selecionada"] = request.GET.get(
            "situacao_operacional__exact",
            "",
        )

        return super().changelist_view(
            request,
            extra_context=contexto,
        )

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # Salva o cadastro sem criar um evento automático.
        super().save_model(request, obj, form, change)

    @transaction.atomic
    def save_related(self, request, form, formsets, change):
        # Salva também as condições de exploração.
        super().save_related(request, form, formsets, change)

        poco = form.instance

        tipo_evento = (
            form.cleaned_data.get("tipo_evento") or ""
        ).strip()

        descricao_evento = (
            form.cleaned_data.get("descricao_evento") or ""
        ).strip()

        fotos = form.cleaned_data.get("fotos_evento") or []

        # Sem preenchimento na seção do evento,
        # salva apenas o cadastro e seus dados relacionados.
        if not tipo_evento and not descricao_evento and not fotos:
            return

        # Permite registrar descrição ou fotos sem escolher
        # um tipo, classificando o evento como Outros.
        tipo_evento = tipo_evento or "outros"

        responsavel = (
            request.user.get_full_name()
            or request.user.get_username()
        )

        evento = registrar_historico(
            poco=poco,
            responsavel=responsavel,
            tipo_evento=tipo_evento,
            descricao=descricao_evento,
        )

        # Identifica o evento informado pelo usuário.
        # Os demais dados ficam preservados internamente.
        dados = dict(evento.dados)

        dados["evento_manual"] = True
        dados["descricao_evento"] = descricao_evento

        dados["condicoes_exploracao"] = [
            {
                "data_coleta": (
                    item.data_coleta.isoformat()
                    if item.data_coleta is not None
                    else None
                ),
                "vazao": (
                    str(item.vazao)
                    if item.vazao is not None
                    else None
                ),
                "nivel_dinamico": (
                    str(item.nivel_dinamico)
                    if item.nivel_dinamico is not None
                    else None
                ),
                "colocacao_bomba": (
                    str(item.colocacao_bomba)
                    if item.colocacao_bomba is not None
                    else None
                ),
            }
            for item in poco.condicoes_exploracao.all()
        ]

        evento.dados = dados
        evento.save(update_fields=["dados"])

        # Sem fotos, o evento é salvo normalmente.
        for foto in fotos:
            FotoEvento.objects.create(
                evento=evento,
                imagem=foto,
            )

    class Media:
        js = ("pocos/calculos.js?v=2",)

    @admin.display(description="Ação")
    def acao_historico(self, obj):
        return format_html(
            '<a href="{}" title="Histórico do poço" '
            'aria-label="Histórico do poço" '
            'style="display:inline-flex;align-items:center;'
            'justify-content:center;width:32px;height:32px;'
            'background:#007bff;color:white;border-radius:4px;'
            'text-decoration:none;">'
            '<svg width="18" height="18" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" '
            'aria-hidden="true">'
            '<path d="M3 11a9 9 0 1 1 2.6 7.4"/>'
            '<path d="M3 4v7h7"/>'
            '<path d="M12 7v5l3 2"/>'
            '</svg></a>',
            reverse("historico_poco", args=[obj.pk]),
        )

    @admin.display(
        description="Data de inclusão",
        ordering="criado_em",
    )
    def data_inclusao(self, obj):
        if obj.criado_em is None:
            return "Não informada"

        data = obj.criado_em

        if timezone.is_aware(data):
            data = timezone.localtime(data)

        return data.strftime("%d/%m/%Y")

    @admin.display(description="Última vazão", ordering="vazao")
    def ultima_vazao(self, obj):
        if obj.vazao is None:
            return "Não informada"

        valor = format(obj.vazao, "f")

        if "." in valor:
            valor = valor.rstrip("0").rstrip(".")

        valor = valor.replace(".", ",")

        return f"{valor} m³/h"

    @admin.display(description="Sigla", ordering="identificacao")
    def sigla(self, obj):
        return obj.identificacao

    @admin.display(
        description="Sistema",
        ordering="sistema__cidade",
    )
    def nome_sistema(self, obj):
        if obj.sistema_id:
            return obj.sistema.cidade

        return obj.cidade

    @admin.display(
        description="Código",
        ordering="sistema__codigo",
    )
    def codigo(self, obj):
        if obj.sistema_id:
            return obj.sistema.codigo

        return obj.codigo_sistema

    @admin.display(description="Unidade de negócio")
    def unidade_negocio(self, obj):
        return "Pinheiro"

    @admin.display(description="Registro")
    def abrir_registro(self, obj):
        return format_html(
            '<a href="{}" '
            'style="display:inline-block;padding:6px 10px;'
            'background:#287bb5;color:white;border-radius:4px;'
            'text-decoration:none;white-space:nowrap;">'
            'Abrir registro</a>',
            reverse("detalhe_poco", args=[obj.pk]),
        )

    @admin.display(
        description="Status",
        ordering="situacao_operacional",
    )
    def status_poco(self, obj):
        nomes = {
            "operando": "Operando",
            "parado": "Parado",
            "desativado": "Desativado",
            "manutencao": "Manutenção",
        }

        return nomes.get(
            obj.situacao_operacional,
            "Não informado",
        )

    @admin.display(description="")
    def indicador_status(self, obj):
        cores = {
            "operando": "#68a832",
            "parado": "#d64541",
            "desativado": "#ffffff",
            "manutencao": "#f0bd28",
        }

        cor = cores.get(
            obj.situacao_operacional,
            "#ffffff",
        )

        nome = self.status_poco(obj)

        return format_html(
            '<span role="img" aria-label="{}" title="{}" '
            'style="display:inline-block;width:18px;height:18px;'
            'border-radius:50%;background:{};'
            'border:1px solid #aab7bf;vertical-align:middle;">'
            '</span>',
            nome,
            nome,
            cor,
        )

    @admin.display(description="Média de horas trabalhadas por dia")
    def dias_operacao(self, obj):
        if obj.dias_trabalhados is None:
            return "Não informado"

        valor = f"{obj.dias_trabalhados:.2f}".replace(".", ",")
        return f"{valor} h/dia"

    @admin.display(description="Volume aduzido do mês")
    def aduzido_mes(self, obj):
        if obj.volume_aduzido is None:
            return "Não informado"

        valor = f"{obj.volume_aduzido:.2f}".replace(".", ",")
        return f"{valor} m³"

    @admin.display(description="Rebaixamento do poço")
    def rebaixamento_calculado(self, obj):
        if obj.rebaixamento is None:
            return "Não informado"

        valor = f"{obj.rebaixamento:.2f}".replace(".", ",")
        return f"{valor} m"


@admin.register(Sistema)
class SistemaAdmin(admin.ModelAdmin):
    list_display = ("cidade", "codigo")
    search_fields = ("cidade", "codigo")


admin.site.site_header = (
    "Central de Informações da Gerência de Pinheiro — CIGP"
)
admin.site.site_title = "CIGP"
admin.site.index_title = ""
admin.site.index_template = "central_index.html"
admin.site.enable_nav_sidebar = False


if admin.site.is_registered(Group):
    admin.site.unregister(Group)

if admin.site.is_registered(User):
    admin.site.unregister(User)

    from .models import Eta


@admin.register(Eta)
class EtaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "sistema",
        "situacao_operacional",
        "atualizado_em",
    )

    search_fields = (
        "nome",
        "sistema__cidade",
        "sistema__codigo",
    )

    list_filter = (
        "sistema",
        "situacao_operacional",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Identificação da ETA",
            {
                "fields": (
                    "nome",
                    "sistema",
                    "endereco",
                    "situacao_operacional",
                    "observacoes",
                ),
            },
        ),
        (
            "Datas do cadastro",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                ),
            },
        ),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "sistema":
            kwargs["queryset"] = Sistema.objects.filter(
                codigo__in=["302", "363"],
            ).order_by("cidade")

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )