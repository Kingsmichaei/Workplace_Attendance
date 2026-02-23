# Generated migration for FaceData and Attendance updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaceData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facial_encodings', models.TextField()),
                ('face_registered', models.BooleanField(default=False)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='face_data', to='auth.user')),
            ],
        ),
        migrations.AddField(
            model_name='attendance',
            name='clock_in_method',
            field=models.CharField(choices=[('manual', 'Manual'), ('facial', 'Facial Recognition')], default='manual', max_length=20),
        ),
        migrations.AddField(
            model_name='attendance',
            name='clock_out_method',
            field=models.CharField(blank=True, choices=[('manual', 'Manual'), ('facial', 'Facial Recognition')], default='manual', max_length=20, null=True),
        ),
    ]
