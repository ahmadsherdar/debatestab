from django.urls import path
from . import views

urlpatterns = [
    # Home and Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # Tournament URLs
    path('tournaments/', views.TournamentListView.as_view(), name='tournament_list'),
    path('tournaments/new/', views.TournamentCreateView.as_view(), name='tournament_create'),
    path('tournaments/<int:pk>/', views.TournamentDetailView.as_view(), name='tournament_detail'),
    path('tournaments/<int:pk>/edit/', views.TournamentUpdateView.as_view(), name='tournament_update'),
    path('tournaments/<int:pk>/delete/', views.TournamentDeleteView.as_view(), name='tournament_delete'),
    
    # Team URLs
    path('tournaments/<int:tournament_id>/teams/', views.TeamListView.as_view(), name='team_list'),
    path('tournaments/<int:tournament_id>/teams/new/', views.TeamCreateView.as_view(), name='team_create'),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    
    # Speaker URLs
    path('teams/<int:team_id>/speakers/new/', views.SpeakerCreateView.as_view(), name='speaker_create'),
    
    # Round URLs
    path('tournaments/<int:tournament_id>/rounds/new/', views.RoundCreateView.as_view(), name='round_create'),
    path('rounds/<int:pk>/', views.RoundDetailView.as_view(), name='round_detail'),
    path('rounds/<int:pk>/motions/', views.RoundMotionsView.as_view(), name='round_motions'),
    path('rounds/<int:round_id>/generate-debates/', views.GenerateDebatesView.as_view(), name='generate_debates'),
    
    # Debate URLs
    path('debates/<int:pk>/', views.DebateDetailView.as_view(), name='debate_detail'),
    
    # Result URLs
    path('debates/<int:debate_id>/result/new/', views.ResultCreateView.as_view(), name='result_create'),
    
    # Speaker Score URLs
    path('debates/<int:debate_id>/speaker-scores/new/', views.SpeakerScoreCreateView.as_view(), name='speaker_score_create'),
    path('debates/<int:debate_id>/speaker-scores/bulk/', views.BulkSpeakerScoresView.as_view(), name='bulk_speaker_scores'),
    
    # Speaker Rankings
    path('tournaments/<int:tournament_id>/speaker-rankings/', views.SpeakerRankingsView.as_view(), name='speaker_rankings'),
] 