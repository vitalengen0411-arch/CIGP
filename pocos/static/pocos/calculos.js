document.addEventListener("DOMContentLoaded", function () {
    function lerNumero(nome) {
        const campo = document.getElementById("id_" + nome);

        if (!campo || campo.value.trim() === "") {
            return null;
        }

        const valor = Number(campo.value.replace(",", "."));
        return Number.isFinite(valor) ? valor : null;
    }

    function diasDoMesSelecionado() {
        const campo = document.getElementById("id_mes_referencia");

        if (!campo || campo.value.trim() === "") {
            return null;
        }

        const texto = campo.value.trim();
        let ano;
        let mes;
        let dia = 1;
        let partes;

        // Formatos: AAAA-MM ou AAAA-MM-DD.
        partes = texto.match(/^(\d{4})-(\d{2})(?:-(\d{2}))?$/);

        if (partes) {
            ano = Number(partes[1]);
            mes = Number(partes[2]);
            dia = partes[3] ? Number(partes[3]) : 1;
        } else {
            // Formato brasileiro: DD/MM/AAAA.
            partes = texto.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);

            if (partes) {
                dia = Number(partes[1]);
                mes = Number(partes[2]);
                ano = Number(partes[3]);
            } else {
                // Formato brasileiro: MM/AAAA.
                partes = texto.match(/^(\d{2})\/(\d{4})$/);

                if (!partes) {
                    return null;
                }

                mes = Number(partes[1]);
                ano = Number(partes[2]);
            }
        }

        if (ano < 1 || mes < 1 || mes > 12) {
            return null;
        }

        const bissexto = (
            ano % 400 === 0 ||
            (ano % 4 === 0 && ano % 100 !== 0)
        );

        const diasPorMes = [
            31,
            bissexto ? 29 : 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31
        ];

        const quantidadeDias = diasPorMes[mes - 1];

        if (dia < 1 || dia > quantidadeDias) {
            return null;
        }

        return quantidadeDias;
    }

    function mostrar(nome, valor, unidade) {
        const destino = document.querySelector(
            ".field-" + nome + " .readonly"
        );

        if (!destino) {
            return;
        }

        destino.textContent = valor === null
            ? "Não informado"
            : valor.toLocaleString("pt-BR", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }) + " " + unidade;
    }

    function atualizar() {
        const horas = lerNumero("horas_trabalhadas");
        const vazao = lerNumero("vazao");
        const estatico = lerNumero("nivel_estatico");
        const dinamico = lerNumero("nivel_dinamico");
        const diasDoMes = diasDoMesSelecionado();

        mostrar(
            "dias_operacao",
            horas === null || diasDoMes === null
                ? null
                : horas / diasDoMes,
            "h/dia"
        );

        mostrar(
            "aduzido_mes",
            horas === null || vazao === null
                ? null
                : horas * vazao,
            "m³"
        );

        mostrar(
            "rebaixamento_calculado",
            estatico === null || dinamico === null
                ? null
                : dinamico - estatico,
            "m"
        );
    }

    [
        "horas_trabalhadas",
        "mes_referencia",
        "vazao",
        "nivel_estatico",
        "nivel_dinamico"
    ].forEach(function (nome) {
        const campo = document.getElementById("id_" + nome);

        if (campo) {
            campo.addEventListener("input", atualizar);
            campo.addEventListener("change", atualizar);
        }
    });

    // Atualiza também após escolher uma data no calendário do Django.
    document.addEventListener("click", function (evento) {
        if (evento.target.closest(".calendarbox, .datetimeshortcuts")) {
            window.setTimeout(atualizar, 0);
        }
    });

    atualizar();
});