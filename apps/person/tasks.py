import logging
import smtplib

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import BadHeaderError, EmailMultiAlternatives

# Celery config
from celery import shared_task


@shared_task
def send_securecode_email(data):
    logging.info(_("Send secure code email run"))

    to = data.get('email', None)
    passcode = data.get('passcode', None)

    if to and passcode:
        subject = _("Kode Keamanan")
        from_email = '%s <noreply@mydomain.com>' % (settings.APP_NAME)

        # Message
        text = _(
            "JANGAN BERIKAN Kode Keamanan ini kepada siapapun "
            "TERMASUK PIHAK %(app_label)s. Kode Kode Keamanan Anda: " +
            passcode
        ) % {'app_label': settings.APP_NAME}

        html = _(
            "JANGAN BERIKAN Kode Keamanan ini kepada siapapun "
            "TERMASUK PIHAK %(app_label)s.<br />"
            "Kode Kode Keamanan Anda: "
            "<strong>" + passcode + "</strong>"
            "<br /><br />"
            "Salam, <br /> <strong>%(app_label)s</strong>"
        ) % {'app_label': settings.APP_NAME}

        if subject and from_email:
            try:
                msg = EmailMultiAlternatives(subject, text, from_email, [to])
                msg.attach_alternative(html, "text/html")
                msg.send()
                logging.info(_("SecureCode email success"))
            except smtplib.SMTPConnectError as e:
                logging.error('SMTPConnectError: %s' % e)
            except smtplib.SMTPAuthenticationError as e:
                logging.error('SMTPAuthenticationError: %s' % e)
            except smtplib.SMTPSenderRefused as e:
                logging.error('SMTPSenderRefused: %s' % e)
            except smtplib.SMTPRecipientsRefused as e:
                logging.error('SMTPRecipientsRefused: %s' % e)
            except smtplib.SMTPDataError as e:
                logging.error('SMTPDataError: %s' % e)
            except smtplib.SMTPException as e:
                logging.error('SMTPException: %s' % e)
            except BadHeaderError:
                logging.warning(_("Invalid header found"))
    else:
        logging.warning(
            _("Tried to send email to non-existing SecureCode Code"))


@shared_task
def send_securecode_msisdn(data):
    logging.info(_("Send secure code msisdn run"))

    to = data.get('msisdn', None)
    passcode = data.get('passcode', None)

    if to and passcode:
        pass
    else:
        logging.warning(
            _("Tried to send email to non-existing SecureCode Code"))
