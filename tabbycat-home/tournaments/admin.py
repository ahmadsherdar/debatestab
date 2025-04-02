from django.contrib import admin
from .models import Tournament, Team, Speaker, Round, Debate, Result, SpeakerScore

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'rounds_count', 'created_by')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name', 'description')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'tournament', 'wins', 'total_speaker_score')
    list_filter = ('tournament', 'institution')
    search_fields = ('name', 'institution')

@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'total_score', 'average_score')
    list_filter = ('team__tournament', 'team')
    search_fields = ('name', 'team__name')

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'round_type', 'start_time', 'is_completed')
    list_filter = ('tournament', 'round_type', 'is_completed')
    search_fields = ('name', 'motion')

@admin.register(Debate)
class DebateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'round', 'venue', 'is_completed')
    list_filter = ('round__tournament', 'round', 'is_completed')
    search_fields = ('affirmative_team__name', 'negative_team__name', 'venue')

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'debate', 'winner', 'affirmative_score', 'negative_score')
    list_filter = ('debate__round__tournament', 'debate__round')
    search_fields = ('debate__affirmative_team__name', 'debate__negative_team__name')

@admin.register(SpeakerScore)
class SpeakerScoreAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'debate', 'score', 'position')
    list_filter = ('debate__round__tournament', 'debate__round')
    search_fields = ('speaker__name', 'debate__affirmative_team__name', 'debate__negative_team__name')
