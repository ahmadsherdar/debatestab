# Generated by Django 5.0.6 on 2025-03-09 19:30

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Debate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('venue', models.CharField(blank=True, max_length=100)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField()),
                ('name', models.CharField(blank=True, max_length=100)),
                ('round_type', models.CharField(choices=[('P', 'Preliminary'), ('Q', 'Quarterfinal'), ('S', 'Semifinal'), ('F', 'Final')], default='P', max_length=1)),
                ('motion', models.TextField(blank=True)),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('institution', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wins', models.PositiveSmallIntegerField(default=0)),
                ('total_speaker_score', models.FloatField(default=0)),
            ],
            options={
                'ordering': ['-wins', '-total_speaker_score'],
            },
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('winner', models.CharField(choices=[('A', 'Affirmative'), ('N', 'Negative')], max_length=1)),
                ('affirmative_score', models.FloatField()),
                ('negative_score', models.FloatField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('debate', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='tournaments.debate')),
                ('submitted_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submitted_results', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='debate',
            name='round',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debates', to='tournaments.round'),
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('total_score', models.FloatField(default=0)),
                ('average_score', models.FloatField(default=0)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speakers', to='tournaments.team')),
            ],
        ),
        migrations.AddField(
            model_name='debate',
            name='affirmative_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affirmative_debates', to='tournaments.team'),
        ),
        migrations.AddField(
            model_name='debate',
            name='negative_team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='negative_debates', to='tournaments.team'),
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('team_size', models.PositiveSmallIntegerField(default=3)),
                ('rounds_count', models.PositiveSmallIntegerField(default=5)),
                ('break_count', models.PositiveSmallIntegerField(default=8, help_text='Number of teams that break to elimination rounds')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tournaments', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='team',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to='tournaments.tournament'),
        ),
        migrations.AddField(
            model_name='round',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rounds', to='tournaments.tournament'),
        ),
        migrations.CreateModel(
            name='SpeakerScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('position', models.PositiveSmallIntegerField(help_text='Speaker position (1st, 2nd, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('debate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speaker_scores', to='tournaments.debate')),
                ('speaker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='tournaments.speaker')),
            ],
            options={
                'unique_together': {('debate', 'speaker', 'position')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='round',
            unique_together={('tournament', 'number')},
        ),
    ]
