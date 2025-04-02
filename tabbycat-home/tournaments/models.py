from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Tournament(models.Model):
    """Model representing a debate tournament."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournaments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tournament settings
    TEAM_SIZE_CHOICES = (
        (2, '2 speakers per team'),
        (3, '3 speakers per team'),
    )
    team_size = models.PositiveSmallIntegerField(choices=TEAM_SIZE_CHOICES, default=3)
    rounds_count = models.PositiveSmallIntegerField(default=5)
    break_count = models.PositiveSmallIntegerField(default=8, help_text="Number of teams that break to elimination rounds")
    min_speaker_score = models.FloatField(default=69.0, help_text="Minimum speaker score allowed")
    max_speaker_score = models.FloatField(default=79.0, help_text="Maximum speaker score allowed")
    
    def save(self, *args, **kwargs):
        # Set break_count based on team_size
        if self.team_size == 2:
            self.break_count = 16
        else:  # team_size == 3
            self.break_count = 8
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tournament_detail', args=[str(self.id)])

class Team(models.Model):
    """Model representing a debate team."""
    name = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Team statistics (updated after each round)
    wins = models.PositiveSmallIntegerField(default=0)
    total_speaker_score = models.FloatField(default=0)
    total_margin = models.IntegerField(default=0)  # New field for tracking total margin
    
    def __str__(self):
        return f"{self.name} ({self.institution})"
    
    def get_absolute_url(self):
        return reverse('team_detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['-wins', '-total_margin', '-total_speaker_score']  # Updated ordering to match new ranking system

class Speaker(models.Model):
    """Model representing a speaker in a debate team."""
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='speakers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Speaker statistics
    total_score = models.FloatField(default=0)
    average_score = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.name} ({self.team.name})"

class Round(models.Model):
    """Model representing a round in a tournament."""
    ROUND_TYPES = (
        ('P', 'Preliminary'),
        ('Q', 'Quarterfinal'),
        ('S', 'Semifinal'),
        ('F', 'Final'),
    )
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100, blank=True)
    round_type = models.CharField(max_length=1, choices=ROUND_TYPES, default='P')
    motion = models.TextField(blank=True, help_text="Legacy field - use motion1, motion2, motion3 instead")
    motion1 = models.TextField(blank=True, help_text="First motion option")
    motion2 = models.TextField(blank=True, help_text="Second motion option")
    motion3 = models.TextField(blank=True, help_text="Third motion option")
    selected_motion = models.TextField(blank=True, help_text="The motion that was selected for debates")
    start_time = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.name:
            return f"{self.name} (Round {self.number})"
        return f"Round {self.number}"
    
    def get_absolute_url(self):
        return reverse('round_detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['number']
        unique_together = ['tournament', 'number']

class Debate(models.Model):
    """Model representing a debate in a round."""
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='debates')
    affirmative_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='affirmative_debates')
    negative_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='negative_debates')
    venue = models.CharField(max_length=100, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.affirmative_team.name} vs {self.negative_team.name} (Round {self.round.number})"
    
    def get_absolute_url(self):
        return reverse('debate_detail', args=[str(self.id)])

class Result(models.Model):
    """Model representing the result of a debate."""
    WINNER_CHOICES = (
        ('A', 'Affirmative'),
        ('N', 'Negative'),
    )
    
    MOTION_CHOICES = (
        ('1', 'Motion 1'),
        ('2', 'Motion 2'),
        ('3', 'Motion 3'),
    )
    
    debate = models.OneToOneField(Debate, on_delete=models.CASCADE, related_name='result')
    winner = models.CharField(max_length=1, choices=WINNER_CHOICES)
    margin = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        default=1,  # Default value of 1 for existing records
        help_text="Margin of victory (1-12 points)"
    )
    selected_motion = models.CharField(max_length=1, choices=MOTION_CHOICES, blank=True, null=True, help_text="Which motion was debated")
    affirmative_score = models.FloatField()
    negative_score = models.FloatField()
    notes = models.TextField(blank=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='submitted_results')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        winner_team = self.debate.affirmative_team if self.winner == 'A' else self.debate.negative_team
        return f"{winner_team.name} won ({self.affirmative_score} - {self.negative_score})"

class SpeakerScore(models.Model):
    """Model representing a speaker's score in a debate."""
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE, related_name='speaker_scores')
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE, related_name='scores')
    score = models.FloatField()
    position = models.PositiveSmallIntegerField(help_text="Speaker position (1st, 2nd, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.speaker.name}: {self.score} (Position {self.position})"
    
    class Meta:
        unique_together = ['debate', 'speaker', 'position']

class UserProfile(models.Model):
    """Model representing additional user information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
