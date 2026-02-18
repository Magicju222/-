"""
LLM客户端封装模块
提供安全、可靠的大模型API调用能力
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import openai
from openai import OpenAI


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
    max_retries: int = 3
    timeout: int = 30
    rate_limit_per_minute: int = 20
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量加载配置"""
        api_key = os.getenv('LLM_API_KEY')
        if not api_key:
            raise ValueError("LLM_API_KEY environment variable not set")
        
        return cls(
            api_key=api_key,
            model=os.getenv('LLM_MODEL', 'gpt-4'),
            base_url=os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1'),
            max_retries=int(os.getenv('LLM_MAX_RETRIES', '3')),
            timeout=int(os.getenv('LLM_TIMEOUT', '30')),
            rate_limit_per_minute=int(os.getenv('LLM_RATE_LIMIT', '20'))
        )


class LLMClient:
    """
    LLM客户端
    封装OpenAI API调用，提供错误处理、重试、频率控制等功能
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        self.request_times: List[float] = []
        self.logger = self._setup_logger()
    
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
            response_format: 响应格式（如 {"type": "json_object"}）
        
        Returns:
            API响应结果
        """
        self._check_rate_limit()
        
        request_id = f"req_{int(time.time() * 1000)}"
        
        # 记录请求
        self.logger.info(f"[{request_id}] Request: {json.dumps(messages, ensure_ascii=False)[:200]}...")
        
        for attempt in range(self.config.max_retries):
            try:
                kwargs = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if response_format:
                    kwargs["response_format"] = response_format
                
                response = self.client.chat.completions.create(**kwargs)
                
                # 记录响应
                self.logger.info(f"[{request_id}] Response received, tokens: {response.usage.total_tokens if response.usage else 'N/A'}")
                
                return {
                    'content': response.choices[0].message.content,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                        'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                        'total_tokens': response.usage.total_tokens if response.usage else 0
                    },
                    'model': response.model
                }
                
            except openai.RateLimitError as e:
                self.logger.error(f"[{request_id}] Rate limit error: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    sleep_time = 2 ** attempt  # 指数退避
                    self.logger.info(f"[{request_id}] Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise LLMRateLimitError(f"Rate limit exceeded after {self.config.max_retries} retries")
                    
            except openai.AuthenticationError as e:
                self.logger.error(f"[{request_id}] Authentication error: {str(e)}")
                raise LLMAuthenticationError("Invalid API key")
                
            except openai.APITimeoutError as e:
                self.logger.error(f"[{request_id}] Timeout error: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise LLMTimeoutError(f"Request timeout after {self.config.max_retries} retries")
                    
            except Exception as e:
                self.logger.error(f"[{request_id}] Unexpected error: {str(e)}")
                if attempt < self.config.max_retries - 1:
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
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response['content'])
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
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
