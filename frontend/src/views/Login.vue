<template>
  <div class="login-container">
    <div class="login-card glass-effect">
      <div class="logo-section">
        <div class="logo-icon">🏔️</div>
        <h1 class="system-title">旅游数据分析系统</h1>
        <p class="system-subtitle">Tourism Data Analysis Platform</p>
      </div>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="0" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入用户名" 
            size="large" 
            prefix-icon="User"
            class="custom-input" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码" 
            size="large" 
            prefix-icon="Lock" 
            class="custom-input"
            @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button 
            class="btn-gradient login-btn" 
            type="primary" 
            size="large" 
            @click="handleLogin" 
            :loading="loading">
            立即登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="footer-links">
        <router-link to="/register" class="register-link">
          <span>还没有账号？</span>
          <span class="link-text">立即注册</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = ref({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await userStore.login(form.value)
        if (success) {
          ElMessage.success('登录成功')
          router.push('/home')
        } else {
          ElMessage.error('登录失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '登录失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 520px;
  padding: 60px 50px;
  border-radius: 32px;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo-section {
  text-align: center;
  margin-bottom: 48px;
}

.logo-icon {
  font-size: 72px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.system-title {
  font-size: 36px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px 0;
  letter-spacing: 1px;
}

.system-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.login-form {
  margin-bottom: 32px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 16px 20px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.15);
}

.login-form :deep(.el-input__inner) {
  font-size: 15px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  height: 52px;
  font-size: 17px;
  font-weight: 600;
  border-radius: 16px;
  letter-spacing: 1px;
  margin-top: 8px;
}

.footer-links {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.register-link {
  color: #6b7280;
  text-decoration: none;
  font-size: 15px;
  transition: all 0.3s ease;
  display: inline-block;
}

.register-link .link-text {
  color: #3b82f6;
  font-weight: 600;
  margin-left: 6px;
}

.register-link:hover .link-text {
  color: #2563eb;
  text-decoration: underline;
}
</style>
