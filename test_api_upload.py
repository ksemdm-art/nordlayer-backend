#!/usr/bin/env python3
"""
Test API upload endpoint
"""

import requests
import tempfile
import os

def test_api_upload():
    """Test file upload via API"""
    print("Testing API upload endpoint...")
    
    # Create a test image file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        tmp_file.write(b"fake image content for testing")
        tmp_file_path = tmp_file.name
    
    try:
        # Upload file via API
        with open(tmp_file_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(
                'http://localhost:8000/api/v1/files/upload',
                files=files,
                params={'folder': 'uploads/test'}
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                file_url = data['data']['url']
                storage = data['data']['storage']
                print(f"✅ Upload successful!")
                print(f"Storage: {storage}")
                print(f"URL: {file_url}")
                
                # Check if it's S3 URL
                if 's3.twcstorage.ru' in file_url:
                    print("✅ File uploaded to S3")
                else:
                    print("❌ File uploaded to local storage instead of S3")
                    
                return file_url
            else:
                print("❌ Upload failed")
                return None
        else:
            print(f"❌ API error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None
    finally:
        # Clean up temp file
        os.unlink(tmp_file_path)

if __name__ == "__main__":
    test_api_upload()