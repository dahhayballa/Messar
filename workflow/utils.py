import logging

logger = logging.getLogger(__name__)

def send_sms_notification(phone_number: str, message: str) -> None:
    """
    Simule l'envoi d'un SMS au format officiel mauritanien.
    Affiche le contenu dans la console de debug de Django.
    """
    sms_output = (
        f"\n==================== [SMS SENDING] ====================\n"
        f"Recipient : {phone_number}\n"
        f"Message   : {message}\n"
        f"=======================================================\n"
    )
    print(sms_output)
    logger.info(f"SMS Sent to {phone_number}: {message}")
