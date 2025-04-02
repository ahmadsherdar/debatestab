from django.core.management.base import BaseCommand
from tournaments.models import Debate

class Command(BaseCommand):
    help = 'Check debate details'

    def add_arguments(self, parser):
        parser.add_argument('debate_id', type=int)

    def handle(self, *args, **options):
        debate_id = options['debate_id']
        try:
            debate = Debate.objects.get(id=debate_id)
            self.stdout.write(f"Debate {debate_id}:")
            self.stdout.write(f"Round: {debate.round.name}")
            self.stdout.write(f"Tournament: {debate.round.tournament.name}")
            
            self.stdout.write("\nAffirmative Team:")
            self.stdout.write(f"- Name: {debate.affirmative_team.name}")
            aff_speakers = debate.affirmative_team.speakers.all()
            if aff_speakers:
                self.stdout.write("- Speakers:")
                for speaker in aff_speakers:
                    self.stdout.write(f"  * {speaker.name}")
            else:
                self.stdout.write("- No speakers assigned")
            
            self.stdout.write("\nNegative Team:")
            self.stdout.write(f"- Name: {debate.negative_team.name}")
            neg_speakers = debate.negative_team.speakers.all()
            if neg_speakers:
                self.stdout.write("- Speakers:")
                for speaker in neg_speakers:
                    self.stdout.write(f"  * {speaker.name}")
            else:
                self.stdout.write("- No speakers assigned")
            
        except Debate.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Debate {debate_id} not found")) 