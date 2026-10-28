from django.db import transaction
from pocos.models import Sistema


sistemas = [
    ("Alcântara", "302"),
    ("Peri Mirim", "301"),
    ("Guimarães", "303"),
    ("São Bento", "306"),
    ("São Vicente Ferrer", "307"),
    ("Matinha", "309"),
    ("São João Batista", "315"),
    ("Mirinzal", "319"),
    ("Bacuri", "324"),
    ("Cajapió", "331"),
    ("Palmeirândia", "339"),
    ("Porto Rico", "362"),
    ("Pinheiro", "363"),
    ("Penalva", "368"),
    ("Carutapera", "370"),
    ("Cândido Mendes", "371"),
    ("Godofredo Viana", "372"),
    ("Luís Domingues", "373"),
    ("Maranhãozinho", "646"),
]

with transaction.atomic():
    for cidade, codigo in sistemas:
        Sistema.objects.update_or_create(
            codigo=codigo,
            defaults={"cidade": cidade},
        )

print("Cadastro dos 19 sistemas concluído.")