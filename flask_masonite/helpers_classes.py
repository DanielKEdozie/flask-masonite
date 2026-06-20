"""
Helper classes for Flask-Sonite framework.
Includes Task, Email, and Security helper classes.
"""

import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union
import hashlib
import secrets
import bcrypt
from concurrent.futures import ThreadPoolExecutor
import threading
import time


class Task:
    """
    Task helper class for managing background tasks and scheduling.
    """
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.tasks = {}
        self.task_counter = 0
    
    def run_async(self, func, *args, **kwargs):
        """
        Run a function asynchronously in a thread pool.
        
        Args:
            func: The function to run asynchronously
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Future object for the asynchronous task
        """
        return self.executor.submit(func, *args, **kwargs)
    
    def schedule(self, func, delay_seconds: int, *args, **kwargs):
        """
        Schedule a function to run after a delay.
        
        Args:
            func: The function to schedule
            delay_seconds: Number of seconds to wait before running
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Task ID for the scheduled task
        """
        def delayed_task():
            time.sleep(delay_seconds)
            return func(*args, **kwargs)
        
        future = self.executor.submit(delayed_task)
        task_id = f"scheduled_{self.task_counter}"
        self.tasks[task_id] = future
        self.task_counter += 1
        return task_id
    
    def run_periodic(self, func, interval_seconds: int, max_runs: Optional[int] = None, *args, **kwargs):
        """
        Run a function periodically at specified intervals.
        
        Args:
            func: The function to run periodically
            interval_seconds: Interval in seconds between runs
            max_runs: Maximum number of times to run (None for infinite)
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        def periodic_task():
            count = 0
            while max_runs is None or count < max_runs:
                func(*args, **kwargs)
                count += 1
                if max_runs is None or count < max_runs:
                    time.sleep(interval_seconds)
        
        return self.executor.submit(periodic_task)
    
    def get_result(self, task_id: str):
        """
        Get the result of a scheduled task.
        
        Args:
            task_id: The ID of the task to get result for
            
        Returns:
            Result of the task or None if not completed
        """
        if task_id in self.tasks:
            future = self.tasks[task_id]
            if future.done():
                return future.result()
        return None
    
    def shutdown(self):
        """
        Shutdown the task executor and clean up resources.
        """
        self.executor.shutdown(wait=True)


class Email:
    """
    Email helper class for sending emails.
    """
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587, 
                 username: str = None, password: str = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send(self, to_emails: Union[str, List[str]], subject: str, body: str, 
             from_email: str = None, html_body: str = None):
        """
        Send an email.
        
        Args:
            to_emails: Recipient email address(es)
            subject: Email subject
            body: Plain text body of the email
            from_email: Sender email address (uses username if not provided)
            html_body: HTML body of the email (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if isinstance(to_emails, str):
            to_emails = [to_emails]
        
        if not from_email:
            from_email = self.username
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Add plain text body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add HTML body if provided
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_bulk(self, recipients: List[dict], subject: str, body: str, 
                  from_email: str = None, html_body: str = None):
        """
        Send bulk emails to multiple recipients with personalized content.
        
        Args:
            recipients: List of dictionaries with 'email' and optional personalization data
            subject: Email subject
            body: Plain text body of the email
            from_email: Sender email address
            html_body: HTML body of the email (optional)
            
        Returns:
            Number of emails sent successfully
        """
        success_count = 0
        for recipient in recipients:
            email_addr = recipient.get('email')
            personalized_body = body.format(**recipient)
            personalized_subject = subject.format(**recipient)
            personalized_html = html_body.format(**recipient) if html_body else None
            
            if self.send([email_addr], personalized_subject, personalized_body, 
                         from_email, personalized_html):
                success_count += 1
        
        return success_count


class Security:
    """
    Security helper class for hashing and password management.
    """
    
    @staticmethod
    def hash_password(password: str, method: str = 'bcrypt') -> str:
        """
        Hash a password using the specified method.
        
        Args:
            password: The password to hash
            method: Hashing method ('bcrypt', 'sha256', 'pbkdf2')
            
        Returns:
            Hashed password string
        """
        if method == 'bcrypt':
            # Using bcrypt for password hashing
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        elif method == 'sha256':
            # Simple SHA-256 with salt
            salt = secrets.token_hex(32)
            pwdhash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
            return f"{pwdhash}:{salt}"
        else:
            raise ValueError(f"Unsupported hashing method: {method}")
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, method: str = 'bcrypt') -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: The password to verify
            hashed_password: The stored hashed password
            method: Hashing method used ('bcrypt', 'sha256')
            
        Returns:
            True if password matches the hash, False otherwise
        """
        if method == 'bcrypt':
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        elif method == 'sha256':
            # Extract salt from stored hash
            pwdhash, salt = hashed_password.split(':')
            # Hash the provided password with the same salt
            new_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
            return new_hash == pwdhash
        else:
            raise ValueError(f"Unsupported verification method: {method}")
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: Length of the token in bytes (default 32)
            
        Returns:
            Random token string
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def encrypt_data(data: str, key: str = None) -> str:
        """
        Encrypt data using a simple XOR cipher with a random key.
        NOTE: This is not suitable for production use. Use proper encryption libraries like cryptography.
        
        Args:
            data: Data to encrypt
            key: Encryption key (generated if not provided)
            
        Returns:
            Encrypted data as hex string
        """
        if key is None:
            key = secrets.token_bytes(32)
        elif isinstance(key, str):
            key = key.encode('utf-8')
        
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()
        
        for i in range(len(data_bytes)):
            encrypted.append(data_bytes[i] ^ key[i % len(key)])
        
        return encrypted.hex()
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> str:
        """
        Decrypt data using XOR cipher.
        NOTE: This is not suitable for production use. Use proper encryption libraries like cryptography.
        
        Args:
            encrypted_data: Encrypted data as hex string
            key: Decryption key
            
        Returns:
            Decrypted data string
        """
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        encrypted_bytes = bytes.fromhex(encrypted_data)
        decrypted = bytearray()
        
        for i in range(len(encrypted_bytes)):
            decrypted.append(encrypted_bytes[i] ^ key[i % len(key)])
        
        return decrypted.decode('utf-8')
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """
        Generate a random salt for password hashing.
        
        Args:
            length: Length of the salt in bytes (default 32)
            
        Returns:
            Random salt string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_with_salt(password: str, salt: str = None) -> tuple:
        """
        Hash a password with a salt.
        
        Args:
            password: The password to hash
            salt: Salt to use (generated if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = Security.generate_salt()
        
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)  # 100,000 iterations
        return pwdhash.hex(), salt
    
    @staticmethod
    def verify_with_salt(password: str, pwdhash: str, salt: str) -> bool:
        """
        Verify a password against its hash with salt.
        
        Args:
            password: The password to verify
            pwdhash: The stored hashed password
            salt: The salt used for hashing
            
        Returns:
            True if password matches the hash, False otherwise
        """
        new_hash, _ = Security.hash_with_salt(password, salt)
        return new_hash == pwdhash