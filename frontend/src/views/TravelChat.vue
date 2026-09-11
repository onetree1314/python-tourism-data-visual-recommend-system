<template>
  <Layout>
    <div class="chat-container">
      <div class="chat-content">
        <!-- 聊天标题 -->
        <div class="chat-header card-fresh">
          <div class="header-info">
            <el-icon class="header-icon"><ChatDotRound /></el-icon>
            <div>
              <h2>AI旅游助手</h2>
              <p v-if="userStore.isAdmin">管理员模式 - 可查询系统数据、用户统计、爬虫状态等</p>
              <p v-else>智能助手 - 可咨询景点推荐、旅游规划、数据分析等</p>
            </div>
          </div>
        </div>

        <!-- 聊天消息区域 -->
        <div class="chat-messages card-fresh" ref="messagesContainer">
          <div v-if="messages.length === 0" class="empty-state">
            <el-icon class="empty-icon"><ChatLineRound /></el-icon>
            <p>开始与AI助手对话吧！</p>
            <div class="suggestions">
              <el-tag
                v-for="(suggestion, index) in suggestions"
                :key="index"
                class="suggestion-tag"
                @click="sendMessage(suggestion)"
              >
                {{ suggestion }}
              </el-tag>
            </div>
          </div>

          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message-item', message.role]"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'"><User /></el-icon>
              <el-icon v-else><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-bubble" :class="message.role">
                <div v-if="message.role === 'assistant'" class="message-text" v-html="formatMessage(message.content)"></div>
                <div v-else class="message-text">{{ message.content }}</div>
              </div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>

          <!-- 加载中提示 -->
          <div v-if="loading" class="message-item assistant">
            <div class="message-avatar">
              <el-icon><Service /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-bubble assistant">
                <div class="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input card-fresh">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            @keydown.ctrl.enter="handleSend"
            @keydown.enter.exact.prevent="handleSend"
            :disabled="loading"
          />
          <div class="input-actions">
            <el-button
              type="primary"
              :loading="loading"
              @click="handleSend"
              :disabled="!inputMessage.trim()"
            >
              <el-icon><Promotion /></el-icon>
              发送 (Enter)
            </el-button>
            <el-button @click="clearChat" :disabled="loading || messages.length === 0">
              <el-icon><Delete /></el-icon>
              清空对话
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { recommendationAPI } from '../api'
import { ElMessage } from 'element-plus'
import { ChatDotRound, ChatLineRound, User, Service, Promotion, Delete } from '@element-plus/icons-vue'
import Layout from '../components/Layout.vue'

const userStore = useUserStore()

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

// 根据角色显示不同的建议问题
const suggestions = ref(
  userStore.isAdmin
    ? [
        '系统总共有多少用户？',
        '今天爬虫执行了多少次任务？',
        '哪个城市的景点最多？',
        '最近7天的用户登录趋势如何？',
        '系统中有多少景点数据？'
      ]
    : [
        '推荐一些高评分的景点',
        '帮我规划一个3天的北京旅游行程',
        '哪些景点是免费的？',
        '上海有哪些热门景点？',
        '根据我的浏览历史推荐景点'
      ]
)

// 发送消息
const handleSend = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 发送到后端
  loading.value = true
  try {
    const res = await recommendationAPI.chat({
      message: userMessage,
      messages: messages.value.slice(0, -1).map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    })

    if (res.code === 200) {
      messages.value.push({
        role: 'assistant',
        content: res.data.response,
        timestamp: new Date()
      })
    } else {
      ElMessage.error(res.message || 'AI回复失败')
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后重试')
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// 快速发送建议问题
const sendMessage = (text) => {
  inputMessage.value = text
  handleSend()
}

// 清空对话
const clearChat = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

// 格式化消息（支持换行）
const formatMessage = (text) => {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-container {
  padding: 0;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  position: relative;
  overflow: visible;
}

.chat-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px);
  min-height: 600px;
  box-sizing: border-box;
}

.chat-header {
  padding: 20px 30px;
  margin-bottom: 20px;
  background: rgba(20, 40, 70, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.3);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  font-size: 40px;
  color: #4facfe;
}

.header-info h2 {
  margin: 0 0 5px 0;
  color: #ffffff;
  font-size: 24px;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.header-info p {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: rgba(15, 25, 40, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  border-radius: 16px;
  margin-bottom: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ffffff;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
  max-width: 600px;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(79, 172, 254, 0.2) !important;
  color: #ffffff !important;
  border: 1px solid rgba(79, 172, 254, 0.4) !important;
}

.suggestion-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
}

.message-item {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(79, 172, 254, 0.2);
  border: 2px solid rgba(79, 172, 254, 0.3);
}

.message-item.user .message-avatar {
  background: rgba(67, 233, 123, 0.2);
  border-color: rgba(67, 233, 123, 0.3);
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message-item.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 18px;
  border-radius: 16px;
  word-wrap: break-word;
  line-height: 1.6;
}

.message-bubble.user {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: rgba(20, 40, 70, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(79, 172, 254, 0.4);
  color: #ffffff;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.message-bubble.assistant .message-text {
  color: #ffffff !important;
  font-weight: 400;
  line-height: 1.8;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 5px;
}

.message-item.user .message-time {
  text-align: right;
}

.loading-dots {
  display: flex;
  gap: 5px;
  padding: 5px 0;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(79, 172, 254, 0.6);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input {
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  border-radius: 16px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(79, 172, 254, 0.3);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(79, 172, 254, 0.5);
}
</style>
