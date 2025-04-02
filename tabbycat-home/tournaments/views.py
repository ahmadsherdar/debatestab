from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import random

from .models import Tournament, Team, Speaker, Round, Debate, Result, SpeakerScore, UserProfile
from .forms import TournamentForm, TeamForm, SpeakerForm, RoundForm, DebateForm, ResultForm, SpeakerScoreForm, BulkSpeakerScoreForm, UserRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth import login

# Custom Mixins
class TournamentCreatorRequiredMixin(UserPassesTestMixin):
    """Mixin that tests if the current user is the creator of the related tournament."""
    
    def get_tournament(self):
        """Get the tournament object related to the view."""
        if hasattr(self, 'tournament'):
            return self.tournament
        elif 'tournament_id' in self.kwargs:
            return get_object_or_404(Tournament, id=self.kwargs.get('tournament_id'))
        elif hasattr(self, 'object') and hasattr(self.object, 'tournament'):
            return self.object.tournament
        elif hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'tournament'):
                return obj.tournament
            elif isinstance(obj, Tournament):
                return obj
        return None
        
    def test_func(self):
        """Test if the current user is the creator of the tournament."""
        tournament = self.get_tournament()
        if tournament:
            return self.request.user == tournament.created_by
        return False
        
    def handle_no_permission(self):
        """Handle when the user doesn't have permission."""
        if self.request.user.is_authenticated:
            return HttpResponseForbidden("You don't have permission to perform this action.")
        return super().handle_no_permission()

# Tournament Views
class TournamentListView(ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    ordering = ['-start_date']
    paginate_by = 10

class TournamentDetailView(DetailView):
    model = Tournament
    template_name = 'tournaments/tournament_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_object()
        context['teams'] = tournament.teams.all().order_by('-wins', '-total_speaker_score')
        context['rounds'] = tournament.rounds.all().order_by('number')
        context['current_round'] = tournament.rounds.filter(is_completed=False).first()
        
        # Get speakers for ranking
        speakers = Speaker.objects.filter(team__tournament=tournament).order_by('-total_score')
        # Create a list of (rank, speaker) tuples for the template
        speakers_with_rank = [(i+1, speaker) for i, speaker in enumerate(speakers)]
        context['speakers'] = speakers
        context['speakers_with_rank'] = speakers_with_rank
        
        return context

class TournamentCreateView(LoginRequiredMixin, CreateView):
    model = Tournament
    fields = ['name', 'description', 'start_date', 'end_date', 'team_size', 'rounds_count', 'min_speaker_score', 'max_speaker_score']
    template_name = 'tournaments/tournament_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TournamentUpdateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, UpdateView):
    model = Tournament
    fields = ['name', 'description', 'start_date', 'end_date', 'team_size', 'rounds_count', 'min_speaker_score', 'max_speaker_score']
    template_name = 'tournaments/tournament_form.html'
    
class TournamentDeleteView(LoginRequiredMixin, TournamentCreatorRequiredMixin, DeleteView):
    model = Tournament
    template_name = 'tournaments/tournament_confirm_delete.html'
    success_url = '/'

# Team Views
class TeamListView(ListView):
    model = Team
    template_name = 'tournaments/team_list.html'
    context_object_name = 'teams'
    paginate_by = 20
    
    def get_queryset(self):
        tournament_id = self.kwargs.get('tournament_id')
        return Team.objects.filter(tournament_id=tournament_id).order_by('-wins', '-total_speaker_score')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = get_object_or_404(Tournament, id=self.kwargs.get('tournament_id'))
        context['tournament'] = tournament
        
        # Get all rounds for this tournament
        rounds = tournament.rounds.all().order_by('number')
        context['rounds'] = rounds
        
        # Get results for each team in each round
        teams = context['teams']
        team_results = {}
        
        for team in teams:
            team_results[team.id] = {}
            for round_obj in rounds:
                # Check if team participated in any debate in this round
                aff_debates = team.affirmative_debates.filter(round=round_obj)
                neg_debates = team.negative_debates.filter(round=round_obj)
                
                result = None
                if aff_debates.exists() and aff_debates.first().is_completed:
                    debate = aff_debates.first()
                    result = {
                        'debate': debate,
                        'won': debate.result.winner == 'A',
                        'score': debate.result.affirmative_score
                    }
                elif neg_debates.exists() and neg_debates.first().is_completed:
                    debate = neg_debates.first()
                    result = {
                        'debate': debate,
                        'won': debate.result.winner == 'N',
                        'score': debate.result.negative_score
                    }
                
                team_results[team.id][round_obj.id] = result
        
        context['team_results'] = team_results
        return context

class TeamDetailView(DetailView):
    model = Team
    template_name = 'tournaments/team_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        context['speakers'] = team.speakers.all()
        context['affirmative_debates'] = team.affirmative_debates.all()
        context['negative_debates'] = team.negative_debates.all()
        return context

class TeamCreateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, CreateView):
    model = Team
    fields = ['name', 'institution']
    template_name = 'tournaments/team_form.html'
    
    def form_valid(self, form):
        form.instance.tournament_id = self.kwargs.get('tournament_id')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = get_object_or_404(Tournament, id=self.kwargs.get('tournament_id'))
        return context

# Round Views
class RoundDetailView(DetailView):
    model = Round
    template_name = 'tournaments/round_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        round_obj = self.get_object()
        context['debates'] = round_obj.debates.all()
        context['tournament'] = round_obj.tournament
        return context

class RoundCreateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, CreateView):
    model = Round
    form_class = RoundForm
    template_name = 'tournaments/round_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament_id'] = self.kwargs.get('tournament_id')
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        tournament = Tournament.objects.get(id=self.kwargs.get('tournament_id'))
        # Set round number automatically
        existing_rounds = tournament.rounds.count()
        next_round_number = existing_rounds + 1
        # Set default name as "Round X"
        initial['name'] = f'Round {next_round_number}'
        return initial
    
    def form_valid(self, form):
        form.instance.tournament_id = self.kwargs.get('tournament_id')
        tournament = Tournament.objects.get(id=self.kwargs.get('tournament_id'))
        
        # Set round number automatically
        existing_rounds = tournament.rounds.count()
        form.instance.number = existing_rounds + 1
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = get_object_or_404(Tournament, id=self.kwargs.get('tournament_id'))
        context['tournament'] = tournament
        # Add round number to context
        context['next_round_number'] = tournament.rounds.count() + 1
        return context
    
    def get_success_url(self):
        return reverse('round_detail', kwargs={'pk': self.object.id})

class GenerateDebatesView(LoginRequiredMixin, TournamentCreatorRequiredMixin, View):
    """Generate debates for a round using a simple random pairing algorithm."""
    
    def get_tournament(self):
        round_obj = get_object_or_404(Round, id=self.kwargs.get('round_id'))
        return round_obj.tournament
    
    def post(self, request, *args, **kwargs):
        round_obj = get_object_or_404(Round, id=self.kwargs.get('round_id'))
        tournament = round_obj.tournament
        
        # Check if debates already exist for this round
        if round_obj.debates.exists():
            messages.warning(request, 'Debates already exist for this round.')
            return redirect('round_detail', pk=round_obj.id)
        
        teams = list(tournament.teams.all())
        
        # For the first round, randomly pair teams
        if round_obj.number == 1:
            random.shuffle(teams)
        else:
            # For subsequent rounds, pair teams based on their win-loss records
            teams.sort(key=lambda t: (t.wins, t.total_speaker_score), reverse=True)
        
        # Create debates
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                Debate.objects.create(
                    round=round_obj,
                    affirmative_team=teams[i],
                    negative_team=teams[i+1]
                )
        
        messages.success(request, f'Successfully generated {len(teams)//2} debates for {round_obj}.')
        return redirect('round_detail', pk=round_obj.id)

@login_required
def generate_debates(request, round_id):
    """Generate debates for a round using a simple random pairing algorithm."""
    round_obj = get_object_or_404(Round, id=round_id)
    tournament = round_obj.tournament
    
    # Check if user is the tournament creator
    if request.user != tournament.created_by:
        return HttpResponseForbidden("You don't have permission to perform this action.")
    
    # Check if debates already exist for this round
    if round_obj.debates.exists():
        messages.warning(request, 'Debates already exist for this round.')
        return redirect('round_detail', pk=round_id)
    
    teams = list(tournament.teams.all())
    
    # For the first round, randomly pair teams
    if round_obj.number == 1:
        random.shuffle(teams)
    else:
        # For subsequent rounds, pair teams based on their win-loss records
        teams.sort(key=lambda t: (t.wins, t.total_speaker_score), reverse=True)
    
    # Create debates
    for i in range(0, len(teams), 2):
        if i + 1 < len(teams):
            Debate.objects.create(
                round=round_obj,
                affirmative_team=teams[i],
                negative_team=teams[i+1]
            )
    
    messages.success(request, f'Successfully generated {len(teams)//2} debates for {round_obj}.')
    return redirect('round_detail', pk=round_id)

# Result Views
class ResultCreateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, View):
    template_name = 'tournaments/result_form.html'
    
    def get_tournament(self):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        return debate.round.tournament
    
    def get(self, request, *args, **kwargs):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        
        context = {
            'debate': debate,
            'form': ResultForm(debate_id=debate.id)
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        
        form = ResultForm(request.POST, debate_id=debate.id)
        
        if form.is_valid():
            try:
                # Get form data from cleaned_data
                winner = form.cleaned_data['winner']
                margin = form.cleaned_data['margin']  # This is the winning team's margin
                affirmative_score = form.cleaned_data['affirmative_score']
                negative_score = form.cleaned_data['negative_score']
                selected_motion = form.cleaned_data.get('selected_motion')
                
                # Create result
                result = Result.objects.create(
                    debate=debate,
                    winner=winner,
                    margin=margin,  # Store the original margin value
                    affirmative_score=affirmative_score,
                    negative_score=negative_score,
                    selected_motion=selected_motion,
                    submitted_by=request.user,
                    notes=form.cleaned_data.get('notes', '')
                )
                
                # Update the round with the selected motion if this is the first completed debate
                round_obj = debate.round
                if selected_motion:
                    motion_field = f'motion{selected_motion}'
                    selected_motion_text = getattr(round_obj, motion_field, '')
                    
                    # Only set the selected_motion if it's not already set
                    if not round_obj.selected_motion:
                        round_obj.selected_motion = selected_motion_text
                        round_obj.save()
                
                # Save individual speaker scores
                for field_name, score in form.cleaned_data.items():
                    if field_name.startswith('aff_speaker_') or field_name.startswith('neg_speaker_'):
                        # Extract speaker ID from field name
                        speaker_id = int(field_name.split('_')[-1])
                        speaker = get_object_or_404(Speaker, id=speaker_id)
                        
                        # Determine position based on field prefix and order
                        if field_name.startswith('aff_speaker_'):
                            team_speakers = list(debate.affirmative_team.speakers.all())
                        else:
                            team_speakers = list(debate.negative_team.speakers.all())
                        
                        position = team_speakers.index(speaker) + 1
                        
                        # Create speaker score
                        SpeakerScore.objects.create(
                            debate=debate,
                            speaker=speaker,
                            score=score,
                            position=position
                        )
                        
                        # Update speaker statistics
                        speaker_scores = SpeakerScore.objects.filter(speaker=speaker)
                        speaker.total_score = speaker_scores.aggregate(Sum('score'))['score__sum'] or 0
                        speaker.average_score = speaker.total_score / speaker_scores.count()
                        speaker.save()
                
                # Update team statistics
                winner_team = debate.affirmative_team if winner == 'A' else debate.negative_team
                loser_team = debate.negative_team if winner == 'A' else debate.affirmative_team
                
                # Update winner's stats with positive margin
                winner_team.wins += 1
                winner_team.total_margin += margin
                winner_team.total_speaker_score = winner_team.speakers.aggregate(
                    total=Sum('total_score'))['total'] or 0
                winner_team.save()
                
                # Update loser's stats with negative margin
                loser_team.total_margin -= margin  # Subtract the same margin value
                loser_team.total_speaker_score = loser_team.speakers.aggregate(
                    total=Sum('total_score'))['total'] or 0
                loser_team.save()
                
                # Mark debate as completed
                debate.is_completed = True
                debate.save()
                
                # Check if round is completed
                round_obj = debate.round
                if all(d.is_completed for d in round_obj.debates.all()):
                    round_obj.is_completed = True
                    round_obj.save()
                
                messages.success(request, 'Result has been recorded successfully.')
                return redirect('debate_detail', pk=debate.id)
                
            except Exception as e:
                messages.error(request, f'Error saving result: {str(e)}')
                context = {
                    'debate': debate,
                    'form': form
                }
                return render(request, self.template_name, context)
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
        
        context = {
            'debate': debate,
            'form': form
        }
        return render(request, self.template_name, context)

# Speaker Score Views
class SpeakerScoreCreateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, CreateView):
    model = SpeakerScore
    fields = ['speaker', 'score', 'position']
    template_name = 'tournaments/speaker_score_form.html'
    
    def get_tournament(self):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        return debate.round.tournament
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        # Limit speaker choices to those from teams in this debate
        form.fields['speaker'].queryset = Speaker.objects.filter(
            team__in=[debate.affirmative_team, debate.negative_team]
        )
        return form
    
    def form_valid(self, form):
        form.instance.debate_id = self.kwargs.get('debate_id')
        
        # Update speaker statistics
        speaker = form.instance.speaker
        speaker.total_score += form.instance.score
        scores_count = speaker.scores.count() + 1  # +1 for the current score being added
        speaker.average_score = speaker.total_score / scores_count
        speaker.save()
        
        # Update team's total speaker score
        team = speaker.team
        team.total_speaker_score += form.instance.score
        team.save()
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        context['debate'] = debate
        return context
    
    def get_success_url(self):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        return reverse('debate_detail', kwargs={'pk': debate.id})

# Dashboard View
@login_required
def dashboard(request):
    user_tournaments = Tournament.objects.filter(created_by=request.user).order_by('-start_date')
    upcoming_tournaments = Tournament.objects.filter(start_date__gte=timezone.now()).order_by('start_date')[:5]
    active_tournaments = Tournament.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('end_date')[:5]
    
    context = {
        'user_tournaments': user_tournaments,
        'upcoming_tournaments': upcoming_tournaments,
        'active_tournaments': active_tournaments,
    }
    
    return render(request, 'tournaments/dashboard.html', context)

# Home View
def home(request):
    active_tournaments = Tournament.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('end_date')[:5]
    
    upcoming_tournaments = Tournament.objects.filter(
        start_date__gt=timezone.now()
    ).order_by('start_date')[:5]
    
    context = {
        'active_tournaments': active_tournaments,
        'upcoming_tournaments': upcoming_tournaments,
    }
    
    return render(request, 'tournaments/home.html', context)

# Speaker Views
class SpeakerCreateView(LoginRequiredMixin, TournamentCreatorRequiredMixin, CreateView):
    model = Speaker
    fields = ['name']
    template_name = 'tournaments/speaker_form.html'
    
    def get_tournament(self):
        team = get_object_or_404(Team, id=self.kwargs.get('team_id'))
        return team.tournament
    
    def get(self, request, *args, **kwargs):
        team = get_object_or_404(Team, id=self.kwargs.get('team_id'))
        current_speakers_count = team.speakers.count()
        
        # Check if the team already has the maximum number of speakers allowed
        if current_speakers_count >= team.tournament.team_size:
            messages.error(request, f'This team already has the maximum number of speakers ({team.tournament.team_size}) allowed.')
            return redirect('team_detail', pk=team.id)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, id=self.kwargs.get('team_id'))
        context['team'] = team
        context['current_speakers_count'] = team.speakers.count()
        context['max_speakers'] = team.tournament.team_size
        return context
    
    def form_valid(self, form):
        team_id = self.kwargs.get('team_id')
        team = get_object_or_404(Team, id=team_id)
        current_speakers_count = team.speakers.count()
        
        # Double-check the limit before saving (in case of concurrent submissions)
        if current_speakers_count >= team.tournament.team_size:
            messages.error(self.request, f'This team already has the maximum number of speakers ({team.tournament.team_size}) allowed.')
            return redirect('team_detail', pk=team.id)
        
        form.instance.team_id = team_id
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('team_detail', kwargs={'pk': self.kwargs.get('team_id')})

# Debate Views
class DebateDetailView(DetailView):
    model = Debate
    template_name = 'tournaments/debate_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        debate = self.get_object()
        
        # Get teams and their speakers
        aff_speakers = debate.affirmative_team.speakers.all()
        neg_speakers = debate.negative_team.speakers.all()
        
        # Create dictionaries to store speaker scores
        aff_speaker_scores = {}
        neg_speaker_scores = {}
        
        # Get actual speaker scores from the database
        if debate.is_completed:
            # Get all speaker scores for this debate
            speaker_scores = debate.speaker_scores.all()
            
            # Map scores to speakers
            for score in speaker_scores:
                if score.speaker.team == debate.affirmative_team:
                    aff_speaker_scores[score.speaker.id] = score.score
                elif score.speaker.team == debate.negative_team:
                    neg_speaker_scores[score.speaker.id] = score.score
        
        context['affirmative_speakers'] = aff_speakers
        context['negative_speakers'] = neg_speakers
        context['aff_speaker_scores'] = aff_speaker_scores
        context['neg_speaker_scores'] = neg_speaker_scores
        
        return context

# Speaker Rankings View
class SpeakerRankingsView(LoginRequiredMixin, View):
    template_name = 'tournaments/speaker_rankings.html'
    
    def get(self, request, *args, **kwargs):
        tournament_id = self.kwargs.get('tournament_id')
        tournament = get_object_or_404(Tournament, id=tournament_id)
        
        # Get all rounds in the tournament
        rounds = tournament.rounds.all().order_by('number')
        
        # Get all speakers in the tournament
        speakers = Speaker.objects.filter(team__tournament=tournament)
        
        # Create a dictionary to store scores by round for each speaker
        speaker_round_scores = {}
        for speaker in speakers:
            speaker_round_scores[speaker.id] = {}
            speaker.total_score = 0
            
            # Initialize scores for all rounds to 0
            for round_obj in rounds:
                speaker_round_scores[speaker.id][round_obj.id] = 0
            
            # Get actual scores where they exist
            for score in speaker.scores.all():
                round_id = score.debate.round.id
                speaker_round_scores[speaker.id][round_id] = score.score
                speaker.total_score += score.score
        
        # Sort speakers by total score (descending)
        speakers = sorted(speakers, key=lambda s: s.total_score, reverse=True)
        
        context = {
            'tournament': tournament,
            'rounds': rounds,
            'speakers': speakers,
            'speaker_round_scores': speaker_round_scores
        }
        
        return render(request, self.template_name, context)

@login_required
def speaker_rankings(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Get all rounds in the tournament
    rounds = tournament.rounds.all().order_by('number')
    
    # Get all speakers in the tournament
    speakers = Speaker.objects.filter(team__tournament=tournament)
    
    # Create a dictionary to store scores by round for each speaker
    speaker_round_scores = {}
    for speaker in speakers:
        speaker_round_scores[speaker.id] = {}
        speaker.total_score = 0
        
        # Initialize scores for all rounds to 0
        for round_obj in rounds:
            speaker_round_scores[speaker.id][round_obj.id] = 0
        
        # Get actual scores where they exist
        for score in speaker.scores.all():
            round_id = score.debate.round.id
            speaker_round_scores[speaker.id][round_id] = score.score
            speaker.total_score += score.score
    
    # Sort speakers by total score (descending)
    speakers = sorted(speakers, key=lambda s: s.total_score, reverse=True)
    
    context = {
        'tournament': tournament,
        'speakers': speakers,
        'rounds': rounds,
        'speaker_round_scores': speaker_round_scores
    }
    
    return render(request, 'tournaments/speaker_rankings.html', context)

@login_required
def bulk_speaker_scores(request, debate_id):
    debate = get_object_or_404(Debate, id=debate_id)
    tournament = debate.round.tournament
    
    # Check if user is the tournament creator
    if request.user != tournament.created_by:
        return HttpResponseForbidden("You don't have permission to perform this action.")
    
    if request.method == 'POST':
        form = BulkSpeakerScoreForm(request.POST, debate=debate)
        if form.is_valid():
            # Process the form data
            for field_name, score in form.cleaned_data.items():
                if field_name.startswith('aff_speaker_') or field_name.startswith('neg_speaker_'):
                    # Extract speaker ID from field name
                    speaker_id = int(field_name.split('_')[-1])
                    speaker = get_object_or_404(Speaker, id=speaker_id)
                    
                    # Determine position based on field prefix and order
                    if field_name.startswith('aff_speaker_'):
                        team_speakers = list(debate.affirmative_team.speakers.all())
                    else:
                        team_speakers = list(debate.negative_team.speakers.all())
                    
                    position = team_speakers.index(speaker) + 1
                    
                    # Check if a score already exists for this speaker in this debate
                    existing_score = SpeakerScore.objects.filter(debate=debate, speaker=speaker).first()
                    
                    if existing_score:
                        # Update existing score
                        existing_score.score = score
                        existing_score.position = position
                        existing_score.save()
                    else:
                        # Create new score
                        SpeakerScore.objects.create(
                            debate=debate,
                            speaker=speaker,
                            score=score,
                            position=position
                        )
                    
                    # Update speaker statistics
                    speaker_scores = SpeakerScore.objects.filter(speaker=speaker)
                    speaker.total_score = speaker_scores.aggregate(Sum('score'))['score__sum'] or 0
                    speaker.average_score = speaker.total_score / speaker_scores.count()
                    speaker.save()
                    
                    # Update team's total speaker score
                    team = speaker.team
                    team.total_speaker_score = team.speakers.aggregate(Sum('total_score'))['total_score__sum'] or 0
                    team.save()
            
            messages.success(request, 'Speaker scores have been recorded successfully.')
            return redirect('debate_detail', pk=debate_id)
    else:
        form = BulkSpeakerScoreForm(debate=debate)
    
    context = {
        'form': form,
        'debate': debate,
        'tournament': tournament,
        'min_score': tournament.min_speaker_score,
        'max_score': tournament.max_speaker_score,
    }
    
    return render(request, 'tournaments/bulk_speaker_scores.html', context)

class BulkSpeakerScoresView(LoginRequiredMixin, TournamentCreatorRequiredMixin, View):
    template_name = 'tournaments/bulk_speaker_scores.html'
    
    def get_tournament(self):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        return debate.round.tournament
    
    def get(self, request, *args, **kwargs):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        form = BulkSpeakerScoreForm(debate=debate)
        context = {
            'debate': debate,
            'form': form
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        debate = get_object_or_404(Debate, id=self.kwargs.get('debate_id'))
        form = BulkSpeakerScoreForm(request.POST, debate=debate)
        
        if form.is_valid():
            # Process the form data
            for field_name, score in form.cleaned_data.items():
                if field_name.startswith('aff_speaker_') or field_name.startswith('neg_speaker_'):
                    # Extract speaker ID from field name
                    speaker_id = int(field_name.split('_')[-1])
                    speaker = get_object_or_404(Speaker, id=speaker_id)
                    
                    # Determine position based on field prefix and order
                    if field_name.startswith('aff_speaker_'):
                        team_speakers = list(debate.affirmative_team.speakers.all())
                    else:
                        team_speakers = list(debate.negative_team.speakers.all())
                    
                    position = team_speakers.index(speaker) + 1
                    
                    # Check if a score already exists for this speaker in this debate
                    existing_score = SpeakerScore.objects.filter(debate=debate, speaker=speaker).first()
                    
                    if existing_score:
                        # Update existing score
                        existing_score.score = score
                        existing_score.position = position
                        existing_score.save()
                    else:
                        # Create new score
                        SpeakerScore.objects.create(
                            debate=debate,
                            speaker=speaker,
                            score=score,
                            position=position
                        )
                    
                    # Update speaker statistics
                    speaker_scores = SpeakerScore.objects.filter(speaker=speaker)
                    speaker.total_score = speaker_scores.aggregate(Sum('score'))['score__sum'] or 0
                    speaker.average_score = speaker.total_score / speaker_scores.count()
                    speaker.save()
                    
                    # Update team's total speaker score
                    team = speaker.team
                    team.total_speaker_score = team.speakers.aggregate(Sum('total_score'))['total_score__sum'] or 0
                    team.save()
            
            # Check if debate is completed - mark completed if it is
            if hasattr(debate, 'result') and debate.result:
                debate.is_completed = True
                debate.save()
            
            messages.success(request, 'Speaker scores have been saved successfully.')
            return redirect('debate_detail', pk=debate.id)
        
        context = {
            'debate': debate,
            'form': form
        }
        return render(request, self.template_name, context)

class RoundMotionsView(DetailView):
    model = Round
    template_name = 'tournaments/round_motions.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        round_obj = self.get_object()
        context['tournament'] = round_obj.tournament
        
        # Create a list of motions
        motions = []
        if round_obj.motion1:
            motions.append(('1', round_obj.motion1))
        if round_obj.motion2:
            motions.append(('2', round_obj.motion2))
        if round_obj.motion3:
            motions.append(('3', round_obj.motion3))
        
        context['motions'] = motions
        context['selected_motion'] = round_obj.selected_motion
        
        return context

class UserRegistrationView(View):
    """View for user registration."""
    template_name = 'tournaments/register.html'
    
    def get(self, request, *args, **kwargs):
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create the user account
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            
            # Create user profile with phone number
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number']
            )
            
            # Log the user in
            login(request, user)
            
            messages.success(request, f'Account created for {user.username}! You can now create tournaments.')
            return redirect('dashboard')
        
        return render(request, self.template_name, {'form': form})
