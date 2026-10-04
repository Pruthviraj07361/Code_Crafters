from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from accounts.models import AdminProfile
from .models import Submission


class SubmissionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.submission_id = self.scope['url_route']['kwargs']['submission_id']
        submission_state = await self.get_authorized_submission_state()
        if submission_state is None:
            await self.close(code=4403)
            return

        self.group_name = f'submission_{self.submission_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        submission_state = await self.get_authorized_submission_state()
        if submission_state is None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.close(code=4403)
            return
        await self.accept()
        await self.send_status(submission_state['status'], submission_state['judge0_output'])

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def submission_status(self, event):
        await self.send_status(event['status'], event['judge0_output'])

    async def send_status(self, status, judge0_output):
        await self.send_json({
            'status': status,
            'judge0_output': judge0_output,
        })

    @database_sync_to_async
    def get_authorized_submission_state(self):
        user = self.scope['user']
        if not user.is_authenticated or not user.is_active:
            return None

        try:
            submission = Submission.objects.select_related('student').get(
                pk=self.submission_id,
            )
        except Submission.DoesNotExist:
            return None

        is_owner = submission.student.user_id == user.pk
        is_staff = user.is_superuser or AdminProfile.objects.filter(
            user_id=user.pk,
            is_approved=True,
            staff_type__in=[
                AdminProfile.STAFF_FACULTY,
                AdminProfile.STAFF_SUPERVISOR,
                AdminProfile.STAFF_SUPERUSER,
            ],
        ).exists()
        if not (is_owner or is_staff):
            return None

        return {
            'status': submission.status,
            'judge0_output': submission.judge0_output,
        }