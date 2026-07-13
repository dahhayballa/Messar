from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
import requests
import mimetypes
import logging

logger = logging.getLogger(__name__)

@deconstructible
class SupabaseStorage(Storage):
    def __init__(self, bucket_name=None, **kwargs):
        self.bucket_name = bucket_name or getattr(settings, 'SUPABASE_DEFAULT_BUCKET', 'documents')
        self.supabase_url = getattr(settings, 'SUPABASE_URL', None)
        self.supabase_key = getattr(settings, 'SUPABASE_KEY', None)
        super().__init__(**kwargs)

    def _get_headers(self):
        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY is not configured in Django settings.")
        return {
            'Authorization': f'Bearer {self.supabase_key}',
            'apikey': self.supabase_key,
        }

    def _save(self, name, content):
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is not configured in Django settings.")
            
        # Standardize path separators to forward slashes for URLs
        name = name.replace('\\', '/')
        
        # Build Supabase upload API URL:
        # POST /storage/v1/object/{bucket}/{path}
        url = f"{self.supabase_url.rstrip('/')}/storage/v1/object/{self.bucket_name}/{name}"
        
        headers = self._get_headers()
        content_type, _ = mimetypes.guess_type(name)
        if content_type:
            headers['Content-Type'] = content_type
            
        content_data = content.read()
        
        # Enable upserting files so we don't fail if the file already exists
        headers['x-upsert'] = 'true'
        
        logger.info(f"Uploading file {name} to Supabase bucket {self.bucket_name}...")
        response = requests.post(url, headers=headers, data=content_data)
        
        if response.status_code not in (200, 201):
            raise IOError(f"Could not upload file to Supabase Storage: {response.text} (Status code: {response.status_code})")
            
        return name

    def _open(self, name, mode='rb'):
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is not configured in Django settings.")
            
        name = name.replace('\\', '/')
        url = f"{self.supabase_url.rstrip('/')}/storage/v1/object/{self.bucket_name}/{name}"
        headers = self._get_headers()
        
        logger.info(f"Retrieving file {name} from Supabase bucket {self.bucket_name}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise IOError(f"Could not open file from Supabase Storage: {response.text} (Status code: {response.status_code})")
            
        return ContentFile(response.content, name=name)

    def exists(self, name):
        if not self.supabase_url:
            return False
            
        name = name.replace('\\', '/')
        # Verify object existence using a GET request
        url = f"{self.supabase_url.rstrip('/')}/storage/v1/object/{self.bucket_name}/{name}"
        try:
            headers = self._get_headers()
            response = requests.get(url, headers=headers, stream=True)
            return response.status_code == 200
        except Exception:
            return False

    def url(self, name):
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL is not configured in Django settings.")
            
        name = name.replace('\\', '/')
        # Return the public URL to access the resource
        return f"{self.supabase_url.rstrip('/')}/storage/v1/object/public/{self.bucket_name}/{name}"
