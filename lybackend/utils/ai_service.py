import requests
from config import Config

class AIService:
    """AI服务封装"""
    
    def __init__(self):
        # DeepSeek配置（用于推荐分析）
        self.deepseek_api_key = Config.DEEPSEEK_API_KEY
        self.deepseek_base_url = Config.DEEPSEEK_BASE_URL
        
        # BigModel配置（用于旅游规划）
        self.bigmodel_api_key = Config.BIGMODEL_API_KEY
        self.bigmodel_base_url = Config.BIGMODEL_BASE_URL
    
    def get_deepseek_recommendation(self, user_data, attractions_data, limit=10):
        """使用DeepSeek进行景点推荐分析"""
        try:
            # 获取用户偏好
            preferences = user_data.get('preferences', {})
            preference_text = ""
            if preferences.get('city'):
                preference_text += f"偏好城市：{preferences.get('city')}\n"
            if preferences.get('min_price') is not None or preferences.get('max_price') is not None:
                min_price = preferences.get('min_price', 0)
                max_price = preferences.get('max_price', 1000)
                preference_text += f"价格范围：¥{min_price} - ¥{max_price}\n"
            if preferences.get('min_score'):
                preference_text += f"最低评分：{preferences.get('min_score')}分\n"
            
            prompt = f"""
作为旅游推荐专家，请根据以下信息进行景点推荐分析：

用户浏览历史：{user_data.get('browse_history', [])}
用户收藏：{user_data.get('favorites', [])}
用户偏好设置：
{preference_text if preference_text else '无特殊偏好'}

候选景点数据：
{attractions_data}

请分析用户偏好，从候选景点中推荐最合适的{limit}个景点，并说明推荐理由。
返回JSON格式：
{{
    "recommendations": [
        {{"poi_id": "景点ID", "reason": "推荐理由", "score": 评分}}
    ]
}}

注意：必须返回恰好{limit}个推荐景点，不要多也不要少。
"""
            
            url = f"{self.deepseek_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个专业的旅游推荐助手，擅长分析用户偏好并提供个性化推荐。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"DeepSeek API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return None
    
    def get_bigmodel_travel_plan(self, destination, days, preferences):
        """使用BigModel生成旅游规划"""
        try:
            url = f"{self.bigmodel_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.bigmodel_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
请为我制定一个{destination}的{days}天旅游计划。

用户偏好：{preferences}

请提供详细的行程安排，包括：
1. 每天的景点安排
2. 推荐的游玩时间
3. 交通建议
4. 美食推荐
5. 注意事项

返回JSON格式的行程计划。
"""
            
            data = {
                "model": "glm-4",
                "messages": [
                    {"role": "system", "content": "你是一个专业的旅游规划师，擅长制定详细的旅游行程。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"BigModel API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"BigModel API error: {e}")
            return None
    
    def chat_with_bigmodel(self, messages, context_data=None):
        """使用BigModel进行对话（AI助手）"""
        try:
            url = f"{self.bigmodel_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.bigmodel_api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建系统提示词
            system_content = "你是一个专业的旅游数据分析助手，可以帮助用户分析旅游数据、推荐景点、制定旅游计划等。"
            
            if context_data:
                system_content += f"\n\n当前数据库信息：\n{context_data}\n\n请基于这些数据回答用户的问题。"
            
            # 构建消息列表
            formatted_messages = [
                {"role": "system", "content": system_content}
            ]
            
            # 添加历史消息（保留最近的对话上下文）
            for msg in messages[-10:]:  # 只保留最近10条消息
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            data = {
                "model": "glm-4",
                "messages": formatted_messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"BigModel API error: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"BigModel API error: {e}")
            return None
    
    def analyze_attraction_comments(self, comments_text):
        """使用DeepSeek分析景点评论"""
        try:
            prompt = f"""
请分析以下景点评论，提取关键信息：

评论内容：
{comments_text}

请提供：
1. 情感分析（正面/负面比例）
2. 高频关键词
3. 主要优点
4. 主要缺点
5. 总体评价

返回JSON格式。
"""
            
            url = f"{self.deepseek_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个专业的文本分析师。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 1500
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"DeepSeek API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return None

# 全局AI服务实例
ai_service = AIService()
