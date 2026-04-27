"""Utility functions for SMTP configuration app."""
from cryptography.fernet import Fernet
from django.conf import settings


def get_encryption_key():
    """
    Get the encryption key from settings.
    
    Returns:
        bytes: The encryption key
    
    Raises:
        ValueError: If ENCRYPTION_KEY is not configured
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY not configured. Generate one with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    # Convert string to bytes if necessary
    if isinstance(key, str):
        key = key.encode()
    
    return key


def encrypt_password(password):
    """
    Encrypt SMTP password using Fernet symmetric encryption.
    
    Args:
        password (str): The plaintext password to encrypt
    
    Returns:
        bytes: The encrypted password
    """
    if not password:
        return b''
    
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Convert password to bytes and encrypt
    password_bytes = password.encode('utf-8')
    encrypted = fernet.encrypt(password_bytes)
    
    return encrypted


def decrypt_password(encrypted_password):
    """
    Decrypt SMTP password using Fernet symmetric encryption.
    
    Args:
        encrypted_password (bytes): The encrypted password
    
    Returns:
        str: The decrypted plaintext password
    """
    if not encrypted_password:
        return ''
    
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Decrypt and convert back to string
    decrypted_bytes = fernet.decrypt(encrypted_password)
    password = decrypted_bytes.decode('utf-8')
    
    return password



def test_smtp_connection(smtp_config):
    """
    Test SMTP connection by sending a test email.
    
    Args:
        smtp_config (SMTPConfig): The SMTP configuration to test
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Decrypt password
        password = decrypt_password(smtp_config.encrypted_password)
        
        # Connect to SMTP server
        # Port 587 uses STARTTLS (use_tls=True)
        # Port 465 uses SSL from start (use_tls=False)
        if smtp_config.port == 587 or smtp_config.use_tls:
            server = smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=10)
            server.ehlo()
            if smtp_config.use_tls:
                server.starttls()
                server.ehlo()  # required after STARTTLS
        else:
            # Port 465 or explicit SSL
            server = smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, timeout=10)
            server.ehlo()
        
        # Authenticate
        server.login(smtp_config.username, password)
        
        # Send test email to user
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'SMTP Configuration Test - Bulk Email Sender'
        msg['From'] = smtp_config.username
        msg['To'] = smtp_config.user.email
        
        text_content = """
        SMTP Configuration Test Successful
        
        Your SMTP configuration has been validated successfully.
        You can now use this configuration to send email campaigns.
        
        Configuration Details:
        - Provider: {}
        - Host: {}
        - Port: {}
        - Username: {}
        
        Best regards,
        Bulk Email Sender Team
        """.format(
            smtp_config.get_provider_display(),
            smtp_config.host,
            smtp_config.port,
            smtp_config.username
        )
        
        html_content = """
        <html>
            <body>
                <h2>SMTP Configuration Test Successful</h2>
                <p>Your SMTP configuration has been validated successfully.</p>
                <p>You can now use this configuration to send email campaigns.</p>
                <h3>Configuration Details:</h3>
                <ul>
                    <li><strong>Provider:</strong> {}</li>
                    <li><strong>Host:</strong> {}</li>
                    <li><strong>Port:</strong> {}</li>
                    <li><strong>Username:</strong> {}</li>
                </ul>
                <p>Best regards,<br>Bulk Email Sender Team</p>
            </body>
        </html>
        """.format(
            smtp_config.get_provider_display(),
            smtp_config.host,
            smtp_config.port,
            smtp_config.username
        )
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email
        server.sendmail(smtp_config.username, [smtp_config.user.email], msg.as_string())
        server.quit()
        
        return True, "SMTP configuration validated successfully. Test email sent."
    
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Authentication failed: {str(e)}"
    
    except smtplib.SMTPConnectError as e:
        return False, f"Connection failed: Could not connect to {smtp_config.host}:{smtp_config.port}"
    
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
