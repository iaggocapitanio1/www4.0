from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SendEmailSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField(max_length=int(20e3), required=False)
    html_message = serializers.CharField(max_length=int(20e3), required=False)
    recipients = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    recipient_group = serializers.ChoiceField(
        choices=[(-1, _("No Role Selection")), (0, _("Administrator")), (1, _("Worker")), (2, _("Customer"))])

    def validate(self, attrs):
        recipients = attrs.get("recipients")
        recipients_group = attrs.get("recipient_group")

        if recipients_group is None and len(recipients) == 0:
            raise serializers.ValidationError(dict(recipients="You need to insert a recipients or a recipients_group"))
        return attrs

    class Meta:
        fields = "__all__"
        kwargs = dict(
            message=dict(help_text='email message to send in text')
        )
