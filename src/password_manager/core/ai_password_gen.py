"""AI-powered password generation using LLM."""

from src.password_manager.core.llm_client import LLMClient


class AIPasswordGenerator:
    """Generate passwords using AI/LLM with support for multiple providers."""

    def __init__(self):
        """Initialize AI password generator."""
        self.llm_client = LLMClient()

    def generate_from_keyword(
        self,
        keyword: str,
        length: int = 16,
        include_special: bool = True,
    ) -> str:
        """
        Generate password based on keyword using AI.

        Args:
            keyword: Keyword to base the password on
            length: Desired password length
            include_special: Whether to include special characters

        Returns:
            Generated password

        Raises:
            RuntimeError: If AI generation fails
        """
        prompt = f"""请基于关键词"{keyword}"生成一个安全、极具创意且易于记忆的密码。

要求：
1. 密码长度：严格限制为整个输出仅有 {length} 位。
2. 包含大写字母、小写字母、数字，并且{"包含特殊字符（如!@#$%^&*）" if include_special else "不包含特殊字符"}。
3. 【关键：避免简单拼接】绝对不要采取“关键词+一串随机数+符号”的生硬拼接套路（例如 Github123!），那与普通规则生成没有区别。
4. 【智能记忆技巧】你应该采用更高级的智能记忆变形，例如：
   - 语义转换或字符谐音替换（如将 github 变形为 G1t_Hub@Sec、将 email 变形为 E_m@1l.99 等）；
   - 首字母缩写联想法（例如根据 github 联想句子 "I love using GitHub to code 100%"，取出各部分字符变形为 Ilu_GH2c_100%）；
   - 键盘模式或创意组合（如 Git.Hub_Password_99 等）。
5. 密码必须易于人类理解记忆，但又具备极高的抗破译强度。
6. 只返回生成的密码字符串，绝对不要包含任何额外的标点、引号、解释性文字或空格。

请直接返回生成的密码："""

        try:
            response_text = self.llm_client.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个密码生成专家，擅长创建安全且易于记忆的密码。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=50,
            )

            password = ''.join(c for c in response_text if not c.isspace())
            return password

        except Exception as e:
            raise RuntimeError(f"AI password generation failed: {str(e)}") from e

    def generate_memorable_password(
        self,
        context: str = "",
        length: int = 16,
    ) -> str:
        """
        Generate a memorable password with optional context.

        Args:
            context: Optional context for password generation
            length: Desired password length

        Returns:
            Generated password

        Raises:
            RuntimeError: If AI generation fails
        """
        prompt = f"""请生成一个安全且易于记忆的密码。

{f"背景信息：{context}" if context else ""}要求：
1. 密码长度：{length}位
2. 包含大写字母、小写字母、数字和特殊字符
3. 可以使用容易记忆的模式，如：单词+数字+符号的组合
4. 密码强度要高
5. 只返回密码本身，不要其他解释

请直接返回生成的密码："""

        try:
            response_text = self.llm_client.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个密码生成专家，擅长创建安全且易于记忆的密码。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=50,
            )

            password = ''.join(c for c in response_text if not c.isspace())
            return password

        except Exception as e:
            raise RuntimeError(f"AI password generation failed: {str(e)}") from e

    def suggest_password_variations(
        self,
        base_password: str,
        count: int = 3,
    ) -> list[str]:
        """
        Generate variations of a base password.

        Args:
            base_password: Base password to create variations from
            count: Number of variations to generate

        Returns:
            List of password variations

        Raises:
            RuntimeError: If AI generation fails
        """
        prompt = f"""基于密码"{base_password}"，生成{count}个类似的密码变体。

要求：
1. 保持相似的记忆模式
2. 变换字符、数字或符号
3. 每个变体都要保持高强度
4. 每行返回一个密码，不要编号或其他解释

请直接返回{count}个密码变体："""

        try:
            response_text = self.llm_client.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个密码生成专家，擅长创建安全且易于记忆的密码。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=100,
            )

            variations = [
                ''.join(c for c in line if not c.isspace())
                for line in response_text.split('\n')
                if line.strip()
            ]

            return variations[:count]

        except Exception as e:
            raise RuntimeError(f"AI password generation failed: {str(e)}") from e

    def extract_entries_from_text(self, text: str) -> list[dict]:
        """
        Extract password entries from natural language text using LLM.

        Args:
            text: Input text containing account and password information.

        Returns:
            List of dictionaries containing entry fields.
        """
        import re
        
        # 1. 拼合空格分隔的单字母拼读，例如 "g i t h u b" -> "github"
        def merge_spaced_letters(match):
            return match.group(0).replace(" ", "").replace("\t", "")
        text = re.sub(r'\b[a-zA-Z]\b(?:\s+\b[a-zA-Z]\b)+', merge_spaced_letters, text)
        
        # 2. 拼合连字符分隔的单字母拼读，例如 "g-i-t-h-u-b" -> "github"
        def merge_hyphenated_letters(match):
            return match.group(0).replace("-", "")
        text = re.sub(r'\b[a-zA-Z]\b(?:-\b[a-zA-Z]\b)+', merge_hyphenated_letters, text)

        prompt = f"""请仔细阅读并分析以下用户文本（该文本可能是用户的直接输入，或者是图像OCR识别、语音转文字得到的转写文本）。
在其中提取出所有的账号和密码资产信息。

【要求】
1. 必须并且只能输出一个合法的 JSON 数组，数组里的每一项代表一个提取出的账号资产。
2. 绝对不能有任何 JSON 数据以外的普通解释性文本、引导词、额外符号，或者 Markdown 标记（例如禁止使用 ```json ... ``` 包裹）。
3. 严格保护用户数据，不可随意对密码、用户名等敏感信息做修改。但对于一个特例：如果发现文本中包含口述样式的中文数字（例如“一二三四五六”、“幺二三四五六”、“八八八九九九”等），这通常是语音识别将阿拉伯数字误转写为了汉字。在提取时，你应该智能地将这些汉字数字规范化转换为对应的阿拉伯数字（例如“123456”、“888999”），除非有明确的上下文指示该密码本身确实就是汉字。
4. 智能拼读容错：如果文本中包含类似于单个英文字母拼读的段落（例如“g i t h u b”或被连字符断开的“g-i-t-h-u-b”），这属于用户在口述拼读英文账号或密码，你应该自动将它们连接还原为正常的英文单词（如“github”）。

【JSON 中的字段定义】
- title: 资产标题或服务/网站名称（如 GitHub、微信、农业银行等）。此字段不可为空。如果文本中未提及明确标题，请根据上下文推断一个合适的名称（如 "未命名资产" 或者是 "X账号"）。
- username: 用户名、邮箱、手机号或登录账号。此字段不可为空。如果文本中未提及，请填充 "未知"。
- password: 密码明文。此字段不可为空。如果文本中未提及，请填充 "未提供"。
- url: 网站的链接或域名（如 github.com）。若无则提供空字符串 ""。
- category: 分类。必须为且仅为以下几项之一："工作", "个人", "社交", "金融", "购物", "其他"。如果无法归类，请默认为 "其他"。
- notes: 备注、安全提问答案或其它说明性信息。若无则提供空字符串 ""。

【提取文本如下】
{text}

直接返回 JSON 数组："""

        try:
            response_text = self.llm_client.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个高精度的密码库资产提取助手，擅长分析自然语言文本，并将其中的账号、密码、网址等信息无损、结构化地提取为标准 JSON 格式输出。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            # 清洗 markdown 标签
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()

            import json
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError("LLM returned non-list JSON.")
        except Exception as e:
            raise RuntimeError(f"AI extraction failed: {str(e)}") from e