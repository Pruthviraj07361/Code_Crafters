from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_activitylog'),
        ('assignments', '0002_problemstatement_test_cases'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='slot',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_published', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements', to='accounts.adminprofile')),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
    ]
