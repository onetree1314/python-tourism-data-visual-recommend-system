<template>
  <div class="layout-container">
    <el-container class="root-layout">
      <el-header class="glass-effect main-header">
        <div class="header-content">
          <div class="header-left">
            <h1>🏔️ 旅游数据分析系统</h1>
            <span class="header-subtitle">Tourism Data Analysis Platform</span>
          </div>
          <div class="header-actions">
            <template v-if="!userStore.isLoggedIn">
              <el-button type="primary" @click="router.push('/login')"
                >登录</el-button
              >
              <el-button @click="router.push('/register')">注册</el-button>
            </template>
            <template v-else>
              <el-tag
                v-if="userStore.isAdmin"
                type="danger"
                effect="dark"
                size="large"
              >
                <el-icon><UserFilled /></el-icon>
                管理员
              </el-tag>
              <el-tag v-else type="success" effect="dark" size="large">
                <el-icon><User /></el-icon>
                普通用户
              </el-tag>
              <span class="username">{{ userStore.userInfo?.username }}</span>
              <el-button type="danger" @click="handleLogout"
                >退出登录</el-button
              >
            </template>
          </div>
        </div>
      </el-header>

      <el-container class="content-container">
        <el-aside width="220px" class="glass-effect sidebar">
          <el-menu :default-active="activeMenu" router class="sidebar-menu">
            <el-menu-item index="/home">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/attractions">
              <el-icon><MapLocation /></el-icon>
              <span>景点列表</span>
            </el-menu-item>
            <el-menu-item index="/analytics">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据分析</span>
            </el-menu-item>

            <!-- 登录用户功能 -->
            <template v-if="userStore.isLoggedIn">
              <el-menu-item index="/recommendation">
                <el-icon><Star /></el-icon>
                <span>智能推荐</span>
              </el-menu-item>
              <el-menu-item index="/favorites">
                <el-icon><Collection /></el-icon>
                <span>我的收藏</span>
              </el-menu-item>
              <el-menu-item index="/chat">
                <el-icon><ChatDotRound /></el-icon>
                <span>AI助手</span>
              </el-menu-item>
            </template>

            <!-- 管理员专属功能 -->
            <template v-if="userStore.isAdmin">
              <el-divider style="margin: 12px 0" />
              <div class="menu-group-title">管理功能</div>
              <el-menu-item index="/admin">
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </el-menu-item>
            </template>

            <!-- 未登录提示 -->
            <template v-if="!userStore.isLoggedIn">
              <el-divider style="margin: 12px 0" />
              <div class="login-tip">
                <el-icon><InfoFilled /></el-icon>
                <p>登录后可使用更多功能</p>
                <el-button
                  type="primary"
                  size="small"
                  @click="router.push('/login')"
                >
                  立即登录
                </el-button>
              </div>
            </template>
          </el-menu>
        </el-aside>

        <el-main>
          <slot />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "../stores/user";

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const activeMenu = computed(() => route.path);

const handleLogout = async () => {
  await userStore.logout();
  router.push("/login");
};
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  background: linear-gradient(
    135deg,
    #0a0e27 0%,
    #1a1f3a 25%,
    #2d1b4e 50%,
    #1a1f3a 75%,
    #0a0e27 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
  position: relative;
  overflow: hidden;
}

.layout-container::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(
      circle at 20% 50%,
      rgba(79, 172, 254, 0.15) 0%,
      transparent 50%
    ),
    radial-gradient(
      circle at 80% 80%,
      rgba(240, 147, 251, 0.15) 0%,
      transparent 50%
    ),
    radial-gradient(
      circle at 40% 20%,
      rgba(67, 233, 123, 0.1) 0%,
      transparent 50%
    );
  pointer-events: none;
  z-index: 0;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.el-header {
  padding: 0;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.main-header {
  padding: 0 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(79, 172, 254, 0.2);
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 8px 0;
}

.header-content h1 {
  color: #fff;
  font-size: 26px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #43e97b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
  filter: drop-shadow(0 0 8px rgba(79, 172, 254, 0.6));
}

.header-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-left: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: #fff;
  font-weight: 600;
  font-size: 15px;
}

.sidebar {
  margin: 20px;
  padding: 16px 0;
  /* 由容器高度驱动，不再强行设置最小高度，避免溢出 */
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.sidebar-menu {
  border: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.8);
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(79, 172, 254, 0.2);
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(
    135deg,
    rgba(79, 172, 254, 0.3) 0%,
    rgba(67, 233, 123, 0.3) 100%
  );
  color: #fff;
  box-shadow: 0 0 20px rgba(79, 172, 254, 0.4);
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  color: inherit;
}

.menu-group-title {
  padding: 8px 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.login-tip {
  padding: 16px 20px;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
}

.login-tip p {
  margin: 8px 0 12px 0;
  font-size: 13px;
}

.el-main {
  position: relative;
  z-index: 1;
  padding: 20px;
  overflow: visible;
}

/* 仅限定内部内容容器为左右布局，避免影响包含 header 的根容器 */
.content-container {
  display: flex;
  flex-direction: row;
}

/* 根布局占满视口高度，内部内容自适应填充 */
.root-layout {
  min-height: 100vh;
}

:deep(.el-aside) {
  flex-shrink: 0 !important;
  width: 220px !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

:deep(.el-main) {
  background: transparent;
  flex: 1 !important;
  min-width: 0 !important;
  margin-left: 0 !important;
}
</style>
