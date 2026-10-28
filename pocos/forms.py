from decimal import Decimal

from django import forms

from .models import CondicaoExploracao, Poco


class EntradaVazao(forms.NumberInput):
    def format_value(self, value):
        if isinstance(value, Decimal):
            texto = format(value, "f")

            if "." in texto:
                texto = texto.rstrip("0").rstrip(".")

            value = texto

        return super().format_value(value)


class SeletorMultiplasFotos(forms.ClearableFileInput):
    allow_multiple_selected = True


class CampoMultiplasFotos(forms.ImageField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            SeletorMultiplasFotos(
                attrs={"accept": "image/*"},
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []

        arquivos = (
            list(data)
            if isinstance(data, (list, tuple))
            else [data]
        )

        if len(arquivos) > 15:
            raise forms.ValidationError(
                "Você pode adicionar no máximo 15 fotos por evento."
            )

        validar_imagem = super().clean

        return [
            validar_imagem(arquivo, initial)
            for arquivo in arquivos
        ]


class PocoForm(forms.ModelForm):
    tipo_evento = forms.ChoiceField(
        label="Evento para o histórico",
        choices=[
            ("", "Selecione um evento"),
            ("instalacao_novo_cmb", "Instalação de novo CMB"),
            ("quadro_comando", "Quadro de Comando - QC"),
            ("cabo_partido", "Cabo partido"),
            ("tubo_furado", "Tubo furado"),
            ("cmb_antigo", "CMB antigo"),
            ("outros", "Outros"),
        ],
        required=False,
        help_text=(
            "Selecione quando quiser registrar um evento. "
            "Alterações comuns do cadastro continuam sendo "
            "registradas automaticamente."
        ),
    )

    descricao_evento = forms.CharField(
        label="Descrição do evento",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3},
        ),
        help_text=(
            "Descreva o serviço realizado ou a ocorrência "
            "que deseja registrar no histórico."
        ),
    )

    fotos_evento = CampoMultiplasFotos(
        label="Fotos do evento",
        required=False,
        help_text=(
            "Envio opcional de até 15 fotos por evento. "
            "Selecione várias fotos segurando Ctrl. "
            "As fotos enviadas serão vinculadas ao novo evento."
        ),
    )

    class Meta:
        model = Poco
        fields = "__all__"

        widgets = {
            "vazao": EntradaVazao(
                attrs={"step": "0.001", "min": "0"},
            ),
            "exploracao_vazao": EntradaVazao(
                attrs={"step": "0.001", "min": "0"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["sistema"].required = True
        self.fields["sistema"].queryset = (
            self.fields["sistema"].queryset
            .exclude(codigo__in=["302", "363"])
            .order_by("cidade")
        )

        for nome in ("cidade", "codigo_sistema"):
            self.fields[nome].required = False
            self.fields[nome].disabled = True
            self.fields[nome].help_text = (
                "Preenchido automaticamente ao salvar "
                "o sistema selecionado."
            )

    def clean(self):
        dados = super().clean()
        sistema = dados.get("sistema")

        if sistema is not None:
            dados["cidade"] = sistema.cidade
            dados["codigo_sistema"] = sistema.codigo

        return dados


class CondicaoExploracaoForm(forms.ModelForm):
    class Meta:
        model = CondicaoExploracao
        fields = "__all__"

        widgets = {
            "vazao": EntradaVazao(
                attrs={"step": "0.001", "min": "0"},
            ),
        }