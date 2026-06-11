import pytest
import json
from unittest.mock import MagicMock, patch
from src.password_manager.core.ai_password_gen import AIPasswordGenerator
from src.password_manager.core.multimodal_extractor import MultimodalExtractor


class TestAIEntriesExtraction:
    """Test LLM-based password assets extraction."""

    @patch("src.password_manager.core.ai_password_gen.LLMClient")
    def test_extract_entries_success(self, mock_llm_client_class):
        # 1. 模拟大模型返回合法的 JSON 数组
        mock_client = MagicMock()
        mock_client.create_chat_completion.return_value = json.dumps([
            {
                "title": "测试GitHub",
                "username": "test_user",
                "password": "Secure123Password!",
                "url": "github.com",
                "category": "工作",
                "notes": "工作用"
            }
        ])
        mock_llm_client_class.return_value = mock_client

        generator = AIPasswordGenerator()
        results = generator.extract_entries_from_text("我有个GitHub账号，用户名test_user，密码Secure123Password!")
        
        assert len(results) == 1
        assert results[0]["title"] == "测试GitHub"
        assert results[0]["username"] == "test_user"
        assert results[0]["password"] == "Secure123Password!"
        assert results[0]["category"] == "工作"

    @patch("src.password_manager.core.ai_password_gen.LLMClient")
    def test_extract_entries_with_markdown_blocks(self, mock_llm_client_class):
        # 2. 模拟大模型返回带有 markdown ```json ``` 标记的文本
        mock_client = MagicMock()
        mock_client.create_chat_completion.return_value = """
```json
[
  {
    "title": "WeChat",
    "username": "13800000000",
    "password": "WechatPassword999",
    "url": "",
    "category": "社交",
    "notes": ""
  }
]
```
"""
        mock_llm_client_class.return_value = mock_client

        generator = AIPasswordGenerator()
        results = generator.extract_entries_from_text("微信账号 13800000000 密码 WechatPassword999")
        
        assert len(results) == 1
        assert results[0]["title"] == "WeChat"
        assert results[0]["password"] == "WechatPassword999"
        assert results[0]["category"] == "社交"

    @patch("src.password_manager.core.ai_password_gen.LLMClient")
    def test_extract_entries_invalid_json(self, mock_llm_client_class):
        # 3. 模拟大模型返回了脏数据导致 JSON 解析失败
        mock_client = MagicMock()
        mock_client.create_chat_completion.return_value = "这不是一个JSON数组"
        mock_llm_client_class.return_value = mock_client

        generator = AIPasswordGenerator()
        with pytest.raises(RuntimeError) as excinfo:
            generator.extract_entries_from_text("一些无关紧要的文字")
        assert "AI extraction failed" in str(excinfo.value)


class TestMultimodalExtractorFallback:
    """Test multimodal OCR/ASR fallbacks and error handling."""

    def test_extract_text_file_not_found(self):
        # 测试图片或音频不存在时的异常处理
        with pytest.raises(FileNotFoundError):
            MultimodalExtractor.extract_text_from_image("/path/to/nonexistent/image.png")
            
        with pytest.raises(FileNotFoundError):
            MultimodalExtractor.extract_text_from_audio("/path/to/nonexistent/audio.wav")

    @patch("src.password_manager.core.multimodal_extractor.platform.system")
    @patch("src.password_manager.core.multimodal_extractor.shutil.which")
    def test_extract_image_native_mac_fallback(self, mock_which, mock_system):
        # 模拟 Darwin 且 swift 命令存在
        mock_system.return_value = "Darwin"
        mock_which.return_value = "/usr/bin/swift"

        # 模拟 subprocess.run 返回成功，模拟 OCR 文本
        with patch("src.password_manager.core.multimodal_extractor.subprocess.run") as mock_run, \
             patch("src.password_manager.core.multimodal_extractor.os.path.exists") as mock_exists:
            
            mock_exists.return_value = True
            mock_res = MagicMock()
            mock_res.stdout = "Extracted Text From Swift Vision OCR\n"
            mock_run.return_value = mock_res

            # 调用
            text = MultimodalExtractor.extract_text_from_image("dummy_path.png")
            assert text == "Extracted Text From Swift Vision OCR"
            mock_run.assert_called_once()
