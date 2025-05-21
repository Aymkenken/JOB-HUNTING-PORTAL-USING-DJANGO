import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

def send_application_status_notification(application):
    """
    Send notification when an application status is updated
    """
    try:
        channel_layer = get_channel_layer()
        room_name = f"notifications_{application.applicant.id}"
        
        logger.info(f"Sending application status notification to user {application.applicant.username}")
        logger.info(f"Room name: {room_name}")
        
        notification_data = {
            "type": "notification_message",
            "message": {
                "type": "application_status",
                "job_title": application.job.title,
                "status": application.status,
                "application_id": application.id,
                "job_id": application.job.id,
                "employer_name": f"{application.job.employer.first_name} {application.job.employer.last_name}"
            }
        }
        
        logger.info(f"Notification data: {notification_data}")
        
        async_to_sync(channel_layer.group_send)(
            room_name,
            notification_data
        )
        logger.info("Application status notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending application status notification: {str(e)}")

def send_new_application_notification(job, applicant):
    """
    Send notification when a new application is received
    """
    try:
        channel_layer = get_channel_layer()
        room_name = f"notifications_{job.employer.id}"
        
        logger.info(f"Sending new application notification to employer {job.employer.username}")
        logger.info(f"Room name: {room_name}")
        
        notification_data = {
            "type": "notification_message",
            "message": {
                "type": "new_application",
                "job_title": job.title,
                "applicant_name": f"{applicant.first_name} {applicant.last_name}",
                "job_id": job.id
            }
        }
        
        logger.info(f"Notification data: {notification_data}")
        
        async_to_sync(channel_layer.group_send)(
            room_name,
            notification_data
        )
        logger.info("New application notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending new application notification: {str(e)}") 