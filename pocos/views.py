from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import Poco
from .relatorios import gerar_pdf_poco
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import HistoricoPoco


@login_required(login_url="/admin/login/")
def lista_pocos(request):
    pocos = Poco.objects.all()

    return render(
        request,
        "pocos/lista.html",
        {"pocos": pocos},
    )


@login_required(login_url="/admin/login/")
def detalhe_poco(request, pk):
    poco = get_object_or_404(Poco, pk=pk)

    return render(
        request,
        "pocos/detalhe.html",
        {"poco": poco},
    )


@login_required(login_url="/admin/login/")
def relatorio_poco(request, pk):
    poco = get_object_or_404(Poco, pk=pk)
    arquivo = gerar_pdf_poco(poco)

    nome = slugify(
        f"Registro-{poco.codigo_sistema}-{poco.identificacao}"
    )

    return FileResponse(
        arquivo,
        as_attachment=True,
        filename=f"{nome}.pdf",
        content_type="application/pdf",
    )

@login_required(login_url="/admin/login/")
@xframe_options_sameorigin
def historico_poco(request, pk):
    poco = get_object_or_404(Poco, pk=pk)

    historicos = list(poco.historicos.all())

    registros_cmb = []

    for item in historicos:
        estado_inicial = (
            item.tipo_evento == "outro"
            and item.descricao.startswith(
                "Estado do cadastro antes da primeira"
            )
        )

        if item.tipo_evento in (
            "cadastro",
            "instalacao",
            "retirada",
        ) or estado_inicial:
            registros_cmb.append(item)

    return render(
        request,
        "pocos/historico.html",
        {
            "poco": poco,
            "historicos": historicos,
        },
    )

@login_required(login_url="/admin/login/")
@permission_required(
    "pocos.delete_historicopoco",
    raise_exception=True,
)
@require_POST
def excluir_evento(request, pk, evento_pk):
    evento = get_object_or_404(
        HistoricoPoco,
        pk=evento_pk,
        poco_id=pk,
    )

    evento.delete()

    endereco = reverse("historico_poco", args=[pk])

    if request.POST.get("mini") == "1":
        endereco += "?mini=1"

    return redirect(endereco)

@login_required(login_url="/admin/login/")
@xframe_options_sameorigin
def fotos_evento(request, pk, evento_pk):
    evento = get_object_or_404(
        HistoricoPoco,
        pk=evento_pk,
        poco_id=pk,
    )

    return render(
        request,
        "pocos/fotos_evento.html",
        {
            "poco": evento.poco,
            "evento": evento,
            "fotos": evento.fotos.all(),
        },
    )

@login_required(login_url="/admin/login/")
def imagem_evento(request, pk, evento_pk, foto_pk):
    from django.http import FileResponse, Http404

    from .models import FotoEvento

    foto = get_object_or_404(
        FotoEvento,
        pk=foto_pk,
        evento_id=evento_pk,
        evento__poco_id=pk,
    )

    try:
        arquivo = foto.imagem.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("Foto não encontrada.")

    resposta = FileResponse(
        arquivo,
        as_attachment=False,
        filename=foto.imagem.name.rsplit("/", 1)[-1],
    )

    resposta["Cache-Control"] = "private, no-store"

    return resposta

@login_required(login_url="/admin/login/")
def lista_etas(request):
    from django.contrib import admin
    from django.core.exceptions import PermissionDenied

    from .models import Eta, Sistema

    if not request.user.is_staff:
        raise PermissionDenied(
            "Seu usuário não possui acesso a esta página."
        )

    sistemas = Sistema.objects.filter(
        codigo__in=["302", "363"],
    ).order_by("cidade")

    sistema_selecionado = request.GET.get(
        "sistema", ""
    ).strip()

    codigo_pesquisado = request.GET.get(
        "codigo", ""
    ).strip()

    sistemas_filtrados = sistemas

    etas = (
        Eta.objects
        .select_related("sistema")
        .filter(sistema__codigo__in=["302", "363"])
        .order_by("sistema__cidade", "nome")
    )

    if sistema_selecionado:
        sistemas_filtrados = sistemas_filtrados.filter(
            codigo=sistema_selecionado,
        )

        etas = etas.filter(
            sistema__codigo=sistema_selecionado,
        )

    if codigo_pesquisado:
        sistemas_filtrados = sistemas_filtrados.filter(
            codigo=codigo_pesquisado,
        )

        etas = etas.filter(
            sistema__codigo=codigo_pesquisado,
        )

    contexto = admin.site.each_context(request)

    contexto.update({
        "title": "ETAs",
        "sistemas_filtro": sistemas,
        "sistemas_etas": sistemas_filtrados,
        "etas": etas,
        "sistema_selecionado": sistema_selecionado,
        "codigo_pesquisado": codigo_pesquisado,
    })

    return render(
        request,
        "etas/lista.html",
        contexto,
    )
@login_required(login_url="/admin/login/")
def mapa_sistemas(request):
    return render(
        request,
        "mapa/mapa_sistemas.html",
    )