"""Integra o usuário ao auth do Django sem renomear a coluna nem perder senhas."""
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('restaurante','0002_projecao_e_cache')]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[],
        state_operations=[
            migrations.RenameField(model_name='usuario', old_name='senha_hash', new_name='password'),
            migrations.AlterField(model_name='usuario',name='password',field=models.CharField(max_length=255,db_column='senha_hash')),
        ],
    )]
