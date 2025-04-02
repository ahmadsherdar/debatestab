from django import forms
from django.utils import timezone
from .models import Tournament, Team, Speaker, Round, Debate, Result, SpeakerScore
from django.contrib.auth.models import User

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'description', 'start_date', 'end_date', 'team_size', 'rounds_count', 'break_count']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date cannot be before start date.")
        
        return cleaned_data

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'institution']

class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ['name', 'team']
    
    def __init__(self, *args, tournament_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tournament_id:
            self.fields['team'].queryset = Team.objects.filter(tournament_id=tournament_id)

class RoundForm(forms.ModelForm):
    class Meta:
        model = Round
        fields = ['name', 'round_type', 'motion1', 'motion2', 'motion3']
        widgets = {
            'motion1': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter first motion option', 'class': 'form-control'}),
            'motion2': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter second motion option', 'class': 'form-control'}),
            'motion3': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter third motion option', 'class': 'form-control'}),
        }
        labels = {
            'motion1': 'Motion Option 1',
            'motion2': 'Motion Option 2',
            'motion3': 'Motion Option 3',
        }
    
    def __init__(self, *args, tournament_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required attribute to motion fields
        self.fields['motion1'].required = True
        self.fields['motion2'].required = True
        self.fields['motion3'].required = True

class DebateForm(forms.ModelForm):
    class Meta:
        model = Debate
        fields = ['round', 'affirmative_team', 'negative_team', 'venue']
    
    def __init__(self, *args, round_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if round_id:
            round_obj = Round.objects.get(id=round_id)
            tournament = round_obj.tournament
            self.fields['round'].initial = round_obj
            self.fields['round'].widget = forms.HiddenInput()
            self.fields['affirmative_team'].queryset = Team.objects.filter(tournament=tournament)
            self.fields['negative_team'].queryset = Team.objects.filter(tournament=tournament)
    
    def clean(self):
        cleaned_data = super().clean()
        affirmative_team = cleaned_data.get('affirmative_team')
        negative_team = cleaned_data.get('negative_team')
        
        if affirmative_team and negative_team and affirmative_team == negative_team:
            raise forms.ValidationError("A team cannot debate against itself.")
        
        return cleaned_data

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['winner', 'margin', 'selected_motion', 'affirmative_score', 'negative_score', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'margin': forms.NumberInput(attrs={
                'min': 1,
                'max': 12,
                'class': 'form-control',
                'placeholder': 'Enter margin (1-12)',
                'required': 'required'
            })
        }
        help_texts = {
            'margin': 'Enter the margin of victory (1-12) for the winning team.',
            'winner': 'Select the winning team',
            'selected_motion': 'Select which motion was debated'
        }
    
    def __init__(self, *args, debate_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if debate_id:
            self.debate = Debate.objects.get(id=debate_id)
            tournament = self.debate.round.tournament
            
            # Hide the total score fields as we'll calculate them
            self.fields['affirmative_score'].widget = forms.HiddenInput()
            self.fields['negative_score'].widget = forms.HiddenInput()
            
            # Update winner choices with team names
            self.fields['winner'].choices = [
                ('', 'Select Winner'),
                ('A', f'{self.debate.affirmative_team.name}'),
                ('N', f'{self.debate.negative_team.name}')
            ]
            
            # Update motion choices with actual motions from the round
            round_obj = self.debate.round
            print(f"DEBUG: Round {round_obj.number} motions:")
            print(f"motion1: '{round_obj.motion1}'")
            print(f"motion2: '{round_obj.motion2}'")
            print(f"motion3: '{round_obj.motion3}'")
            
            motion_choices = []
            if round_obj.motion1:
                motion_choices.append(('1', f"Motion 1: {round_obj.motion1[:100]}"))
            if round_obj.motion2:
                motion_choices.append(('2', f"Motion 2: {round_obj.motion2[:100]}"))
            if round_obj.motion3:
                motion_choices.append(('3', f"Motion 3: {round_obj.motion3[:100]}"))
            
            print(f"DEBUG: Found {len(motion_choices)} motion choices")
            
            if motion_choices:
                # Add blank choice
                motion_choices.insert(0, ('', 'Select Motion'))
                self.fields['selected_motion'].choices = motion_choices
                self.fields['selected_motion'].widget.attrs['class'] = 'form-control'
                self.fields['selected_motion'].required = True
                print("DEBUG: Motion field should be visible with choices")
            else:
                # If no motions were specified, hide this field
                self.fields['selected_motion'].widget = forms.HiddenInput()
                print("DEBUG: No motions found, hiding the field")
            
            # Add speaker score fields for affirmative team
            for i, speaker in enumerate(self.debate.affirmative_team.speakers.all()):
                field_name = f'aff_speaker_{speaker.id}'
                self.fields[field_name] = forms.FloatField(
                    label=f"{speaker.name}",
                    min_value=tournament.min_speaker_score,
                    max_value=tournament.max_speaker_score,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control aff-speaker-score',
                        'step': '0.5',
                        'required': 'required'
                    })
                )
            
            # Add speaker score fields for negative team
            for i, speaker in enumerate(self.debate.negative_team.speakers.all()):
                field_name = f'neg_speaker_{speaker.id}'
                self.fields[field_name] = forms.FloatField(
                    label=f"{speaker.name}",
                    min_value=tournament.min_speaker_score,
                    max_value=tournament.max_speaker_score,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control neg-speaker-score',
                        'step': '0.5',
                        'required': 'required'
                    })
                )
            
            # Make required fields
            self.fields['winner'].required = True
            self.fields['margin'].required = True
            
            # Add custom classes for JavaScript handling
            self.fields['winner'].widget.attrs['class'] = 'form-control winner-select'
            self.fields['margin'].widget.attrs['class'] = 'form-control margin-input'
            
            # Add data attributes for team names
            self.fields['winner'].widget.attrs['data-aff-team'] = self.debate.affirmative_team.name
            self.fields['winner'].widget.attrs['data-neg-team'] = self.debate.negative_team.name
    
    def clean(self):
        cleaned_data = super().clean()
        winner = cleaned_data.get('winner')
        margin = cleaned_data.get('margin')
        selected_motion = cleaned_data.get('selected_motion')
        
        if not winner:
            raise forms.ValidationError("You must select a winner.")
            
        if margin is None:
            raise forms.ValidationError("You must enter a margin of victory.")
            
        if margin and (margin < 1 or margin > 12):
            raise forms.ValidationError("Margin must be between 1 and 12")
        
        # Validate motion is selected if motions were provided for the round
        round_obj = self.debate.round
        has_motions = any([round_obj.motion1, round_obj.motion2, round_obj.motion3])
        if has_motions and not selected_motion:
            raise forms.ValidationError("You must select which motion was debated.")
        
        # Calculate total speaker scores
        aff_total = 0
        neg_total = 0
        
        # Sum affirmative speaker scores
        for field_name, value in cleaned_data.items():
            if field_name.startswith('aff_speaker_'):
                if value is not None:
                    aff_total += value
        
        # Sum negative speaker scores
        for field_name, value in cleaned_data.items():
            if field_name.startswith('neg_speaker_'):
                if value is not None:
                    neg_total += value
        
        # Store the totals in the cleaned data
        cleaned_data['affirmative_score'] = aff_total
        cleaned_data['negative_score'] = neg_total
        
        # Validate that winning team has higher speaker points
        if winner == 'A' and neg_total >= aff_total:
            raise forms.ValidationError(
                f"The winning team ({self.debate.affirmative_team.name}) must have higher total speaker points than the losing team. "
                f"Current totals - {self.debate.affirmative_team.name}: {aff_total}, {self.debate.negative_team.name}: {neg_total}"
            )
        elif winner == 'N' and aff_total >= neg_total:
            raise forms.ValidationError(
                f"The winning team ({self.debate.negative_team.name}) must have higher total speaker points than the losing team. "
                f"Current totals - {self.debate.affirmative_team.name}: {aff_total}, {self.debate.negative_team.name}: {neg_total}"
            )
            
        return cleaned_data

class SpeakerScoreForm(forms.ModelForm):
    class Meta:
        model = SpeakerScore
        fields = ['speaker', 'score', 'position']
    
    def __init__(self, *args, debate_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if debate_id:
            debate = Debate.objects.get(id=debate_id)
            # Limit speaker choices to those from teams in this debate
            self.fields['speaker'].queryset = Speaker.objects.filter(
                team__in=[debate.affirmative_team, debate.negative_team]
            ) 

class BulkSpeakerScoreForm(forms.Form):
    def __init__(self, *args, debate=None, **kwargs):
        super().__init__(*args, **kwargs)
        if debate:
            tournament = debate.round.tournament
            min_score = tournament.min_speaker_score
            max_score = tournament.max_speaker_score
            
            # Add fields for affirmative team speakers
            for i, speaker in enumerate(debate.affirmative_team.speakers.all()):
                field_name = f'aff_speaker_{speaker.id}'
                self.fields[field_name] = forms.FloatField(
                    label=f"{speaker.name}",
                    min_value=min_score,
                    max_value=max_score,
                    widget=forms.NumberInput(attrs={'step': '0.5', 'class': 'form-control'}),
                    help_text=f"Position: {i+1}"
                )
            
            # Add fields for negative team speakers
            for i, speaker in enumerate(debate.negative_team.speakers.all()):
                field_name = f'neg_speaker_{speaker.id}'
                self.fields[field_name] = forms.FloatField(
                    label=f"{speaker.name}",
                    min_value=min_score,
                    max_value=max_score,
                    widget=forms.NumberInput(attrs={'step': '0.5', 'class': 'form-control'}),
                    help_text=f"Position: {i+1}"
                ) 

class UserRegistrationForm(forms.Form):
    username = forms.CharField(
        label='Username',
        min_length=4,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2 