"""
Performance tests for 3D model viewer and related endpoints.
"""
import pytest
import pytest_asyncio
import time
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import io

from app.main import app


class Test3DViewerPerformanceE2E:
    """Performance tests for 3D viewer functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest_asyncio.fixture
    async def async_client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    def test_projects_list_performance(self, client):
        """Test projects list loading performance"""
        # Test with different page sizes
        page_sizes = [10, 20, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(f"/api/v1/projects/?per_page={page_size}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # Performance thresholds based on page size
            if page_size <= 20:
                assert response_time < 1.0, f"Projects list with {page_size} items took {response_time:.2f}s"
            elif page_size <= 50:
                assert response_time < 2.0, f"Projects list with {page_size} items took {response_time:.2f}s"
            else:
                assert response_time < 3.0, f"Projects list with {page_size} items took {response_time:.2f}s"
    
    def test_project_detail_performance(self, client):
        """Test individual project loading performance"""
        # First get a list of projects
        response = client.get("/api/v1/projects/?per_page=5")
        assert response.status_code == 200
        
        projects_data = response.json()
        if projects_data.get("data"):
            projects = projects_data["data"]
            
            # Test loading individual projects
            for project in projects[:3]:  # Test first 3 projects
                project_id = project.get("id")
                if project_id:
                    start_time = time.time()
                    response = client.get(f"/api/v1/projects/{project_id}")
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    response_time = end_time - start_time
                    assert response_time < 2.0, f"Project {project_id} detail took {response_time:.2f}s"
    
    def test_stl_file_serving_performance(self, client):
        """Test STL file serving performance"""
        # Get projects with STL files
        response = client.get("/api/v1/projects/?per_page=10")
        assert response.status_code == 200
        
        projects_data = response.json()
        if projects_data.get("data"):
            projects = projects_data["data"]
            
            for project in projects[:3]:  # Test first 3 projects
                project_id = project.get("id")
                if project_id:
                    # Test STL file access
                    start_time = time.time()
                    response = client.get(f"/api/v1/projects/{project_id}/stl")
                    end_time = time.time()
                    
                    # STL file might not exist for all projects
                    if response.status_code == 200:
                        response_time = end_time - start_time
                        file_size = len(response.content)
                        
                        # Performance should be reasonable based on file size
                        if file_size < 1024 * 1024:  # < 1MB
                            assert response_time < 2.0, f"Small STL file took {response_time:.2f}s"
                        elif file_size < 10 * 1024 * 1024:  # < 10MB
                            assert response_time < 5.0, f"Medium STL file took {response_time:.2f}s"
                        else:  # > 10MB
                            assert response_time < 10.0, f"Large STL file took {response_time:.2f}s"
    
    def test_optimized_model_performance(self, client):
        """Test optimized model serving performance"""
        # Get projects
        response = client.get("/api/v1/projects/?per_page=5")
        assert response.status_code == 200
        
        projects_data = response.json()
        if projects_data.get("data"):
            projects = projects_data["data"]
            
            for project in projects[:2]:  # Test first 2 projects
                project_id = project.get("id")
                if project_id:
                    # Test optimized STL file access
                    start_time = time.time()
                    response = client.get(f"/api/v1/projects/{project_id}/stl/optimized")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = end_time - start_time
                        assert response_time < 5.0, f"Optimized STL took {response_time:.2f}s"
                        
                        # Check if it's actually compressed
                        content_encoding = response.headers.get("content-encoding")
                        content_type = response.headers.get("content-type")
                        
                        # Should be either compressed or optimized in some way
                        assert content_type in ["application/gzip", "application/octet-stream"]
    
    def test_model_info_performance(self, client):
        """Test model info retrieval performance"""
        # Get projects
        response = client.get("/api/v1/projects/?per_page=5")
        assert response.status_code == 200
        
        projects_data = response.json()
        if projects_data.get("data"):
            projects = projects_data["data"]
            
            for project in projects[:3]:  # Test first 3 projects
                project_id = project.get("id")
                if project_id:
                    start_time = time.time()
                    response = client.get(f"/api/v1/projects/{project_id}/model-info")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = end_time - start_time
                        assert response_time < 1.0, f"Model info took {response_time:.2f}s"
                        
                        # Verify response contains useful info
                        model_info = response.json()
                        assert model_info["success"] is True
                        assert "data" in model_info
    
    @pytest.mark.asyncio
    async def test_concurrent_project_access(self, async_client):
        """Test concurrent access to projects"""
        # Get list of projects first
        response = await async_client.get("/api/v1/projects/?per_page=5")
        assert response.status_code == 200
        
        projects_data = response.json()
        if projects_data.get("data"):
            projects = projects_data["data"]
            project_ids = [p.get("id") for p in projects if p.get("id")][:3]
            
            if project_ids:
                # Test concurrent access
                start_time = time.time()
                
                tasks = []
                for project_id in project_ids:
                    task = async_client.get(f"/api/v1/projects/{project_id}")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All requests should succeed
                for response in responses:
                    assert response.status_code == 200
                
                # Concurrent requests should be faster than sequential
                total_time = end_time - start_time
                assert total_time < len(project_ids) * 2.0, f"Concurrent access took {total_time:.2f}s"
    
    def test_file_upload_performance(self, client):
        """Test file upload performance for different sizes"""
        # Test with different file sizes
        file_sizes = [
            (1024, "1KB"),           # 1KB
            (10 * 1024, "10KB"),     # 10KB
            (100 * 1024, "100KB"),   # 100KB
            (1024 * 1024, "1MB"),    # 1MB
        ]
        
        for size, size_name in file_sizes:
            # Create test STL content
            stl_header = b"solid test_model\n"
            stl_footer = b"endsolid test_model\n"
            
            # Fill with dummy facets to reach desired size
            facet = b"facet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\n"
            
            remaining_size = size - len(stl_header) - len(stl_footer)
            facet_count = max(1, remaining_size // len(facet))
            
            stl_content = stl_header + (facet * facet_count) + stl_footer
            
            # Upload file
            files = {"file": (f"test_{size_name}.stl", io.BytesIO(stl_content), "application/octet-stream")}
            
            start_time = time.time()
            response = client.post("/api/v1/files/upload", files=files)
            end_time = time.time()
            
            upload_time = end_time - start_time
            
            if response.status_code == 200:
                # Performance thresholds based on file size
                if size <= 10 * 1024:  # <= 10KB
                    assert upload_time < 2.0, f"{size_name} upload took {upload_time:.2f}s"
                elif size <= 100 * 1024:  # <= 100KB
                    assert upload_time < 5.0, f"{size_name} upload took {upload_time:.2f}s"
                else:  # > 100KB
                    assert upload_time < 10.0, f"{size_name} upload took {upload_time:.2f}s"
    
    def test_cache_performance_impact(self, client):
        """Test cache performance impact"""
        # Test projects list without cache (first request)
        start_time = time.time()
        response1 = client.get("/api/v1/projects/?per_page=20")
        first_request_time = time.time() - start_time
        
        assert response1.status_code == 200
        
        # Test projects list with cache (second request)
        start_time = time.time()
        response2 = client.get("/api/v1/projects/?per_page=20")
        second_request_time = time.time() - start_time
        
        assert response2.status_code == 200
        
        # Cached request should be faster (or at least not significantly slower)
        assert second_request_time <= first_request_time * 1.5, \
            f"Cached request ({second_request_time:.2f}s) slower than first ({first_request_time:.2f}s)"
        
        # Responses should be identical
        assert response1.json() == response2.json()
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, async_client):
        """Test memory usage under load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        tasks = []
        for i in range(20):
            # Mix of different operations
            tasks.append(async_client.get("/api/v1/projects/?per_page=10"))
            tasks.append(async_client.get("/api/v1/services/"))
            tasks.append(async_client.get("/api/v1/articles/?limit=5"))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
        
        # Most requests should succeed
        successful_requests = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert successful_requests > len(tasks) * 0.8, f"Only {successful_requests}/{len(tasks)} requests succeeded"
    
    def test_database_query_performance(self, client):
        """Test database query performance"""
        # Test complex queries
        complex_queries = [
            "/api/v1/projects/?search=test&category=electronics&per_page=50",
            "/api/v1/projects/?is_featured=true&per_page=20",
            "/api/v1/articles/?category_filter=tutorial&limit=30",
            "/api/v1/services/?active_only=true&limit=50"
        ]
        
        for query in complex_queries:
            start_time = time.time()
            response = client.get(query)
            end_time = time.time()
            
            query_time = end_time - start_time
            
            # Complex queries should still be reasonably fast
            assert response.status_code == 200
            assert query_time < 3.0, f"Complex query {query} took {query_time:.2f}s"
    
    def test_static_file_serving_performance(self, client):
        """Test static file serving performance"""
        # This would test serving of uploaded files, images, etc.
        # For now, test the file listing endpoint
        
        start_time = time.time()
        response = client.get("/api/v1/files/list")
        end_time = time.time()
        
        if response.status_code == 200:
            list_time = end_time - start_time
            assert list_time < 2.0, f"File listing took {list_time:.2f}s"
            
            # Test file info retrieval if files exist
            files_data = response.json()
            if files_data.get("success") and files_data.get("data", {}).get("files"):
                files = files_data["data"]["files"][:3]  # Test first 3 files
                
                for file_info in files:
                    file_url = file_info.get("url")
                    if file_url:
                        start_time = time.time()
                        info_response = client.get(f"/api/v1/files/info?file_url={file_url}")
                        end_time = time.time()
                        
                        if info_response.status_code == 200:
                            info_time = end_time - start_time
                            assert info_time < 1.0, f"File info took {info_time:.2f}s"