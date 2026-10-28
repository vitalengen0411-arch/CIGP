import json

from django.core.serializers import serialize

from .models import HistoricoPoco


def registrar_historico(
    poco,
    responsavel,
    tipo_evento="atualizacao",
    descricao="",
):
    # Converte os dados para um formato que preserva
    # números, datas e campos vazios no histórico.
    conteudo = serialize("json", [poco])
    dados = json.loads(conteudo)[0]["fields"]

    return HistoricoPoco.objects.create(
        poco=poco,
        responsavel=responsavel,
        tipo_evento=tipo_evento,
        descricao=descricao,
        dados=dados,
    )