from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    # Bots fill in every field they find; humans never see this one. A filled
    # value means the submission is discarded.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
        label="Website",
    )

    class Meta:
        model = Comment
        fields = ["user_name", "user_email", "text"]
        labels = {
            "user_name": "Your Name",
            "user_email": "Your Email",
            "text": "Your Comment",
        }
        help_texts = {
            "user_email": "Not published — it's only so I can reply.",
        }
        widgets = {
            "user_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "user_email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "text": forms.Textarea(attrs={"rows": 5}),
        }
        error_messages = {
            "text": {"required": "Please write something before posting."},
        }

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if len(text) < 3:
            raise forms.ValidationError("That comment is too short.")
        return text

    @property
    def is_spam(self):
        """True when the honeypot was filled in."""
        return bool(self.data.get("website", "").strip())
