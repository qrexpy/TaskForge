#!/usr/bin/env python3

import json
import requests
from typing import Dict, Optional, Any, Union

class RubisClient:
    """Client for interacting with the Rubis API."""
    
    API_BASE_URL = "https://api.rubis.app/v2"  # Correct API endpoint
    
    def __init__(self):
        """Initialize the Rubis API client."""
        self.session = requests.Session()
    
    def create_scrap(self, 
                     content: str, 
                     title: Optional[str] = None, 
                     public: bool = False,
                     access_key: Optional[str] = None,
                     owner_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new scrap on Rubis.
        
        Args:
            content: The content of the scrap
            title: Optional title for the scrap
            public: Whether the scrap should be public
            access_key: Optional access key for private scraps
            owner_key: Optional custom owner key
            
        Returns:
            Dict containing the scrap information
        """
        params = {}
        if title:
            params['title'] = title
        if public:
            params['public'] = 'true'
        if access_key and not public:
            params['accessKey'] = access_key
        if owner_key:
            params['ownerKey'] = owner_key
            
        try:
            print(f"Requesting URL: {self.API_BASE_URL}/scrap with params: {params}")
            response = self.session.post(
                f"{self.API_BASE_URL}/scrap",
                params=params,
                data=content,
                headers={"Content-Type": "text/plain"},
                timeout=10  # Add timeout to prevent hanging
            )
            
            print(f"Response status: {response.status_code}")
            
            # Attempt to print response body even if status code indicates error
            try:
                response_text = response.text
                print(f"Response body: {response_text[:200]}..." if len(response_text) > 200 else response_text)
            except Exception as e:
                print(f"Could not get response text: {e}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error connecting to Rubis API: {e}")
            # Return a default structure with error info
            return {
                "id": None,
                "url": None,
                "rawUrl": None,
                "ownerKey": owner_key or "generated_offline_key",
                "error": str(e)
            }
    
    def get_scrap_metadata(self, 
                           scrap_id: str, 
                           access_key: Optional[str] = None,
                           owner_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for a scrap.
        
        Args:
            scrap_id: The ID of the scrap
            access_key: Access key for private scraps
            owner_key: Owner key for authentication
            
        Returns:
            Dict containing the scrap metadata
        """
        params = {}
        if access_key:
            params['accessKey'] = access_key
        if owner_key:
            params['ownerKey'] = owner_key
            
        response = self.session.get(
            f"{self.API_BASE_URL}/scrap/{scrap_id}",
            params=params
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_raw_scrap_content(self, 
                              scrap_id: str, 
                              access_key: Optional[str] = None,
                              owner_key: Optional[str] = None,
                              download: bool = False) -> str:
        """
        Get the raw content of a scrap.
        
        Args:
            scrap_id: The ID of the scrap
            access_key: Access key for private scraps
            owner_key: Owner key for authentication
            download: Whether to download the scrap as a file
            
        Returns:
            The raw content of the scrap as a string
        """
        params = {}
        if access_key:
            params['accessKey'] = access_key
        if owner_key:
            params['ownerKey'] = owner_key
        if download:
            params['download'] = 'true'
            
        response = self.session.get(
            f"{self.API_BASE_URL}/scrap/{scrap_id}/raw",
            params=params
        )
        
        response.raise_for_status()
        return response.text
    
    def update_scrap_metadata(self,
                              scrap_id: str,
                              owner_key: str,
                              title: Optional[str] = None,
                              public: Optional[bool] = None,
                              access_key: Optional[str] = None,
                              new_owner_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Update metadata for a scrap.
        
        Args:
            scrap_id: The ID of the scrap
            owner_key: Owner key for authentication (required)
            title: New title for the scrap
            public: Whether the scrap should be public
            access_key: New access key for private scraps
            new_owner_key: New owner key
            
        Returns:
            Dict containing the update result
        """
        params = {'ownerKey': owner_key}
        
        payload = {}
        if title is not None:
            payload['title'] = title
        if public is not None:
            payload['public'] = public
        if access_key is not None:
            payload['accessKey'] = access_key
        if new_owner_key is not None:
            payload['ownerKey'] = new_owner_key
            
        response = self.session.patch(
            f"{self.API_BASE_URL}/scrap/{scrap_id}/metadata",
            params=params,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    def replace_scrap_content(self,
                              scrap_id: str,
                              owner_key: str,
                              content: str) -> Dict[str, Any]:
        """
        Replace the content of a scrap.
        
        Args:
            scrap_id: The ID of the scrap
            owner_key: Owner key for authentication (required)
            content: New content for the scrap
            
        Returns:
            Dict containing the update result
        """
        params = {'ownerKey': owner_key}
        
        try:
            response = self.session.put(
                f"{self.API_BASE_URL}/scrap/{scrap_id}",
                params=params,
                data=content,
                headers={"Content-Type": "text/plain"},
                timeout=10  # Add timeout to prevent hanging
            )
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating scrap on Rubis API: {e}")
            # Return a default structure with error info
            return {
                "id": scrap_id,
                "url": None,
                "rawUrl": None,
                "ownerKey": owner_key,
                "error": str(e)
            }
    
    def delete_scrap(self,
                     scrap_id: str,
                     owner_key: str) -> Dict[str, Any]:
        """
        Delete a scrap.
        
        Args:
            scrap_id: The ID of the scrap
            owner_key: Owner key for authentication (required)
            
        Returns:
            Dict containing the deletion result
        """
        params = {'ownerKey': owner_key}
        
        response = self.session.delete(
            f"{self.API_BASE_URL}/scrap/{scrap_id}",
            params=params
        )
        
        response.raise_for_status()
        return response.json()
    
    def extract_scrap_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract the scrap ID from a Rubis URL.
        
        Args:
            url: The Rubis URL to parse
            
        Returns:
            The scrap ID if found, None otherwise
        """
        import re
        # Match patterns like https://rubis.app/s/AbCdEf123456 or https://api.rubis.app/v2/scrap/AbCdEf123456
        # or just a raw ID like AbCdEf123456
        matches = re.search(r'(?:rubis\.app/s/|scrap/)?([\w-]{8,})', url)
        if matches:
            return matches.group(1)
        return None