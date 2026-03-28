import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_via_outlook(to_email, subject, body):
    """Outlook SMTP로 이메일 발송"""
    try:
        outlook_email = os.getenv('OUTLOOK_EMAIL', 'changgeun.jang@mogam.re.kr')
        outlook_password = os.getenv('OUTLOOK_PASSWORD')
        
        if not outlook_password:
            raise Exception("OUTLOOK_PASSWORD not set")
        
        msg = MIMEMultipart()
        msg['From'] = outlook_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(outlook_email, outlook_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Outlook SMTP error: {e}")
        return False
