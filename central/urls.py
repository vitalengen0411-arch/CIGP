from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from pocos.views import (
    detalhe_poco,
    excluir_evento,
    fotos_evento,
    historico_poco,
    imagem_evento,
    lista_etas,
    lista_pocos,
    mapa_sistemas,
    relatorio_poco,
)


urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="admin:index",
            permanent=False,
        ),
        name="inicio",
    ),
    path(
        "admin/pocos/",
        RedirectView.as_view(
            pattern_name="admin:pocos_poco_changelist",
            permanent=False,
        ),
        name="entrada_menu_pocos",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "pocos/",
        lista_pocos,
        name="lista_pocos",
    ),
    path(
        "pocos/<int:pk>/",
        detalhe_poco,
        name="detalhe_poco",
    ),
    path(
        "pocos/<int:pk>/relatorio/",
        relatorio_poco,
        name="relatorio_poco",
    ),
    path(
        "pocos/<int:pk>/historico/",
        historico_poco,
        name="historico_poco",
    ),
    path(
        "pocos/<int:pk>/historico/<int:evento_pk>/excluir/",
        excluir_evento,
        name="excluir_evento",
    ),
    path(
        "pocos/<int:pk>/historico/<int:evento_pk>/fotos/",
        fotos_evento,
        name="fotos_evento",
    ),
    path(
        "pocos/<int:pk>/historico/<int:evento_pk>/fotos/<int:foto_pk>/imagem/",
        imagem_evento,
        name="imagem_evento",
    ),
    path(
        "etas/",
        lista_etas,
        name="lista_etas",
    ),
    path(
        "mapa-dos-sistemas/",
        mapa_sistemas,
        name="mapa_sistemas",
    ),
]