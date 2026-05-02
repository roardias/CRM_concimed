from django.db import migrations


def create_default_stages(apps, schema_editor):
    KanbanStage = apps.get_model("leads", "KanbanStage")
    defaults = [
        ("Novo lead", 1),
        ("Contato inicial", 2),
        ("Qualificacao", 3),
        ("Proposta", 4),
        ("Fechamento", 5),
    ]
    for name, order in defaults:
        KanbanStage.objects.get_or_create(name=name, defaults={"order": order})


def remove_default_stages(apps, schema_editor):
    KanbanStage = apps.get_model("leads", "KanbanStage")
    KanbanStage.objects.filter(
        name__in=["Novo lead", "Contato inicial", "Qualificacao", "Proposta", "Fechamento"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_stages, remove_default_stages),
    ]
