"""
LLM客户端封装模块
提供安全、可靠的大模型API调用能力
支持 OpenAI、Gemini、Moonshot(Kimi) API
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# 尝试导入 openai
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# 尝试导入 google generative ai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMError(Exception):
    """LLM调用基础错误"""
    pass


class LLMRateLimitError(LLMError):
    """频率限制错误"""
    pass


class LLMAuthenticationError(LLMError):
    """认证错误"""
    pass


class LLMTimeoutError(LLMError):
    """超时错误"""
    pass


@dataclass
class LLMConfig:
    """LLM配置类"""
    api_key: str
    model: str = "gpt-4"
    base_url: str = "https://api.openai.com/v1"
    provider: str = "openai"  # 'openai', 'gemini', 'moonshot'
    max_retries: int = 3
    timeout: int = 30
    rate_limit_per_minute: int = 20
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量加载配置"""
        api_key = os.getenv('LLM_API_KEY')
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable not set")
        
        provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
        # 根据提供商设置默认模型和 base_url
        if provider == 'gemini':
            default_model = 'gemini-pro'
            default_base_url = ''
        elif provider == 'moonshot':
            default_model = 'moonshot-v1-8k'
            default_base_url = 'https://api.moonshot.cn/v1'
        else:
            default_model = 'gpt-4'
            default_base_url = 'https://api.openai.com/v1'
        
        # 如果设置了自定义 base_url，使用它
        custom_base_url = os.getenv('LLM_BASE_URL', '')
        if custom_base_url:
            default_base_url = custom_base_url
        
        return cls(
            api_key=api_key,
            model=os.getenv('LLM_MODEL', default_model),
            base_url=default_base_url,
            provider=provider,
            max_retries=int(os.getenv('LLM_MAX_RETRIES', '3')),
            timeout=int(os.getenv('LLM_TIMEOUT', '30')),
            rate_limit_per_minute=int(os.getenv('LLM_RATE_LIMIT', '20'))
        )


class LLMClient:
    """
    LLM客户端
    封装OpenAI/Gemini/Moonshot API调用，提供错误处理、重试、频率控制等功能
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.request_times: List[float] = []
        self.logger = self._setup_logger()
        
        # 初始化对应的客户端
        if self.config.provider == 'gemini':
            self._init_gemini()
        else:
            # OpenAI 和 Moonshot 都使用 OpenAI 客户端（兼容格式）
            self._init_openai_compatible()
    
    def _init_openai_compatible(self):
        """初始化 OpenAI 兼容客户端（支持 OpenAI 和 Moonshot）"""
        if not OPENAI_AVAILABLE:
            raise LLMError("OpenAI package not installed. Run: pip install openai")
        
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url if self.config.base_url else None
        )
        self.logger.info(f"{self.config.provider} client initialized with model: {self.config.model}")
    
    def _init_gemini(self):
        """初始化 Gemini 客户端"""
        if not GEMINI_AVAILABLE:
            raise LLMError("Google Generative AI package not installed. Run: pip install google-generativeai")
        
        genai.configure(api_key=self.config.api_key)
        self.client = genai.GenerativeModel(self.config.model)
        self.logger.info(f"Gemini client initialized with model: {self.config.model}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('llm_client')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('llm_api.log', encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _check_rate_limit(self):
        """检查并控制请求速率"""
        now = time.time()
        # 清理1分钟前的记录
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.config.rate_limit_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    def _call_openai_compatible(self, messages: List[Dict[str, str]], 
                                 temperature: float, max_tokens: int,
                                 response_format: Optional[Dict] = None) -> Dict[str, Any]:
        """调用 OpenAI 兼容 API（支持 OpenAI 和 Moonshot）"""
        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        
        return {
            'content': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            },
            'model': response.model
        }
    
    def _call_gemini(self, messages: List[Dict[str, str]], 
                     temperature: float, max_tokens: int) -> Dict[str, Any]:
        """调用 Gemini API"""
        # 转换消息格式
        system_content = ""
        user_content = ""
        
        for msg in messages:
            if msg['role'] == 'system':
                system_content = msg['content']
            elif msg['role'] == 'user':
                user_content = msg['content']
        
        # 合并 system 和 user 内容
        if system_content:
            full_prompt = f"{system_content}\n\n{user_content}"
        else:
            full_prompt = user_content
        
        # 配置生成参数
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        response = self.client.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        # 估算 token 数量
        content = response.text
        estimated_tokens = len(full_prompt) // 4 + len(content) // 4
        
        return {
            'content': content,
            'usage': {
                'prompt_tokens': len(full_prompt) // 4,
                'completion_tokens': len(content) // 4,
                'total_tokens': estimated_tokens
            },
            'model': self.config.model
        }
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       response_format: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（仅 OpenAI/Moonshot 支持）
        
        Returns:
            API响应结果
        """
        self._check_rate_limit()
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 记录请求
        self.logger.info(f"[{request_id}] Request: {json.dumps(messages, ensure_ascii=False)[:200]}...")
        
        for attempt in range(self.config.max_retries):
            try:
                if self.config.provider == 'gemini':
                    result = self._call_gemini(messages, temperature, max_tokens)
                else:
                    result = self._call_openai_compatible(messages, temperature, max_tokens, response_format)
                
                # 记录响应
                self.logger.info(f"[{request_id}] Response received")
                
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                self.logger.error(f"[{request_id}] Error: {str(e)}")
                
                # 检查是否是频率限制错误
                if 'rate limit' in error_msg or '429' in error_msg:
                    if attempt < self.config.max_retries - 1:
                        sleep_time = 2 ** attempt
                        self.logger.info(f"[{request_id}] Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        raise LLMRateLimitError(f"Rate limit exceeded after {self.config.max_retries} retries")
                
                # 检查是否是认证错误
                elif 'authentication' in error_msg or '401' in error_msg or '403' in error_msg:
                    raise LLMAuthenticationError("Invalid API key")
                
                # 检查是否是超时错误
                elif 'timeout' in error_msg:
                    if attempt < self.config.max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        raise LLMTimeoutError(f"Request timeout after {self.config.max_retries} retries")
                
                # 其他错误，重试
                elif attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise LLMError(f"Unexpected error: {str(e)}")
    
    def analyze(self, prompt: str, 
                system_message: str = "You are a professional data analyst.",
                temperature: float = 0.7,
                max_tokens: int = 2000,
                response_format: Optional[Dict] = None) -> str:
        """
        执行分析请求
        
        Args:
            prompt: 分析提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式
        
        Returns:
            分析结果文本
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
        
        return response['content']
    
    def analyze_json(self, prompt: str,
                    system_message: str = "You are a professional data analyst. Return results in JSON format.",
                    temperature: float = 0.7,
                    max_tokens: int = 2000) -> Dict[str, Any]:
        """
        执行分析请求并返回JSON格式结果
        
        Args:
            prompt: 分析提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            JSON格式的分析结果
        """
        # Gemini 不支持 response_format，需要在 prompt 中说明
        if self.config.provider == 'gemini':
            prompt = prompt + "\n\n重要：请以有效的 JSON 格式返回结果，不要包含任何其他文本。"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response_format = {"type": "json_object"} if self.config.provider not in ['gemini'] else None
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
        
        content = response['content']
        
        # 尝试提取 JSON（有时模型会包裹在代码块中）
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            self.logger.error(f"Response content: {content[:500]}...")
            
            # 尝试修复截断的 JSON
            try:
                # 尝试找到最后一个完整的对象并截断
                last_brace = content.rfind('}')
                if last_brace > 0:
                    fixed_content = content[:last_brace+1]
                    # 补全可能缺失的括号
                    open_braces = fixed_content.count('{') - fixed_content.count('}')
                    open_brackets = fixed_content.count('[') - fixed_content.count(']')
                    fixed_content += '}' * open_braces
                    fixed_content += ']' * open_brackets
                    return json.loads(fixed_content)
            except:
                pass
            
            raise LLMError(f"Invalid JSON response: {str(e)}")
    
    def generate_code(self, prompt: str,
                     system_message: str = "You are a Python expert. Generate clean, executable code.",
                     temperature: float = 0.3,
                     max_tokens: int = 1500) -> str:
        """
        生成代码
        
        Args:
            prompt: 代码生成提示词
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
        
        Returns:
            生成的代码
        """
        response = self.analyze(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取代码块
        if '```python' in response:
            code = response.split('```python')[1].split('```')[0].strip()
        elif '```' in response:
            code = response.split('```')[1].split('```')[0].strip()
        else:
            code = response.strip()
        
        return code
