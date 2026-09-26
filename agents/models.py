from django.conf import settings
from django.db import models


class AgentProfile(models.Model):
    """
    Created once, the moment a user chooses to become an Agent (see
    agents.views.join). This is deliberately independent of is_seller —
    an Agent doesn't need to sell anything themselves; per the original
    brief, agents earn Loyalty Coin by sharing and referring OTHER
    people's products too, not just their own listings.

    Creating this row is what flips CustomUser.is_agent to True — "you
    must create a profile to become an Agent" is enforced by the join
    view, not just implied.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_profile'
    )
    display_name = models.CharField(
        max_length=100,
        help_text="How you're introduced on your Agent Page, e.g. your name or a brand you go by."
    )
    bio = models.TextField(
        blank=True, max_length=500,
        help_text="Optional — a short line about yourself or what you promote."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name
