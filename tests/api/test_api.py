#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 测试示例用例
"""

import pytest
import requests
import time


class TestAPI:
    """API 测试类"""
    
    BASE_URL = "https://httpbin.org"  # 测试用 API
    
    def test_get_request(self):
        """测试 GET 请求"""
        response = requests.get(f"{self.BASE_URL}/get", timeout=10)
        assert response.status_code == 200
        assert 'origin' in response.json()
    
    def test_post_request(self):
        """测试 POST 请求"""
        data = {"key": "value", "test": "api"}
        response = requests.post(f"{self.BASE_URL}/post", json=data, timeout=10)
        assert response.status_code == 200
        assert response.json()['json'] == data
    
    def test_response_time(self):
        """测试响应时间"""
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/get", timeout=10)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"响应时间过长：{elapsed:.2f}秒"
    
    def test_status_codes(self):
        """测试不同状态码"""
        test_cases = [
            (200, "/status/200"),
            (201, "/status/201"),
            (404, "/status/404"),
            (500, "/status/500"),
        ]
        
        for expected_code, endpoint in test_cases:
            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
            assert response.status_code == expected_code
    
    @pytest.mark.skip(reason="需要认证")
    def test_authenticated_endpoint(self):
        """测试需要认证的接口（示例）"""
        headers = {"Authorization": "Bearer YOUR_TOKEN"}
        response = requests.get(
            f"{self.BASE_URL}/headers",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
    
    def test_invalid_url(self):
        """测试无效 URL 处理"""
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get("http://invalid-url-that-does-not-exist.com", timeout=2)
    
    @pytest.mark.parametrize("endpoint,expected_status", [
        ("/get", 200),
        ("/headers", 200),
        ("/ip", 200),
        ("/user-agent", 200),
    ])
    def test_multiple_endpoints(self, endpoint, expected_status):
        """参数化测试多个端点"""
        response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
        assert response.status_code == expected_status
