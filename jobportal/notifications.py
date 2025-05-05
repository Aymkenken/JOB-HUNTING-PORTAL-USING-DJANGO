from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_application_status_notification(application):
    """
    Send notification when an application status is updated
    """
    channel_layer = get_channel_layer()
    room_name = f"notifications_{application.applicant.id}"
    
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "notification_message",
            "message": {
                "type": "application_status",
                "job_title": application.job.title,
                "status": application.status,
                "application_id": application.id
            }
        }
    )

def send_new_application_notification(job, applicant):
    """
    Send notification when a new application is received
    """
    channel_layer = get_channel_layer()
    room_name = f"notifications_{job.employer.id}"
    
    async_to_sync(channel_layer.group_send)(
        room_name,
        {
            "type": "notification_message",
            "message": {
                "type": "new_application",
                "job_title": job.title,
                "applicant_name": f"{applicant.first_name} {applicant.last_name}",
                "job_id": job.id
            }
        }
    ) 