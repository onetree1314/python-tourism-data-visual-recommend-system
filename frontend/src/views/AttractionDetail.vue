<template>
  <Layout>
    <div class="detail-container">
        <div v-if="loading" class="loading-wrapper">
          <el-skeleton :rows="10" animated />
        </div>
        
        <div v-else-if="attraction" class="detail-content">
          <!-- 基本信息 -->
          <div class="card-fresh detail-header">
            <div class="header-image">
              <img :src="attraction.cover_image_url || '/placeholder.jpg'" :alt="attraction.poi_name" />
            </div>
            <div class="header-info">
              <h1>{{ attraction.poi_name }}</h1>
              
              <div class="detail-meta">
                <div class="meta-item">
                  <el-rate v-model="attraction.comment_score" disabled show-score text-color="#ff9900" />
                  <span class="score-text">{{ attraction.comment_score }}/5.0</span>
                </div>
              </div>
              
              <div class="detail-tags" v-if="attraction.city || attraction.price || (attraction.comment_count > 0)">
                <el-tag v-if="attraction.city" type="info" size="large">
                  <el-icon><Location /></el-icon>
                  {{ attraction.city }}
                </el-tag>
                <el-tag v-if="attraction.price" type="success" size="large">
                  <el-icon><Money /></el-icon>
                  {{ attraction.price }}
                </el-tag>
                <el-tag v-if="attraction.comment_count > 0" type="warning" size="large">
                  <el-icon><ChatDotRound /></el-icon>
                  {{ attraction.comment_count }} 条评论
                </el-tag>
              </div>
              
              <div v-if="attraction.district_name || attraction.zone_name" class="detail-address">
                <el-icon><MapLocation /></el-icon>
                <span>{{ attraction.district_name || attraction.zone_name }}</span>
              </div>
              
              <div class="detail-actions">
                <el-button 
                  v-if="userStore.isLoggedIn" 
                  type="primary" 
                  size="large"
                  @click="toggleFavorite"
                  :loading="favoriteLoading">
                  <el-icon><Star /></el-icon>
                  {{ isFavorite ? '取消收藏' : '收藏' }}
                </el-button>
                <el-button size="large" @click="router.push('/attractions')">
                  <el-icon><ArrowLeft /></el-icon>
                  返回列表
                </el-button>
              </div>
            </div>
          </div>

          <!-- 详细信息 -->
          <el-row :gutter="24" class="detail-sections">
            <el-col :xs="24" :lg="16">
              <!-- 标签信息 -->
              <div v-if="tagList.length > 0" class="card-fresh section-card">
                <h2>🏷️ 标签</h2>
                <div class="section-content tags-container">
                  <el-tag 
                    v-for="tag in tagList" 
                    :key="tag" 
                    size="large"
                    effect="dark"
                    style="margin-right: 12px; margin-bottom: 12px; padding: 10px 18px; font-size: 14px;">
                    {{ tag }}
                  </el-tag>
                </div>
              </div>
            </el-col>

            <el-col :xs="24" :lg="8">
              <!-- 相似推荐 -->
              <div v-if="similarAttractions.length > 0" class="card-fresh section-card">
                <h2>相似景点</h2>
                <div class="similar-list">
                  <div 
                    v-for="item in similarAttractions" 
                    :key="item.poi_id" 
                    class="similar-item"
                    @click="goToDetail(item.poi_id)">
                    <img :src="item.cover_image_url || '/placeholder.jpg'" :alt="item.poi_name" />
                    <div class="similar-info">
                      <h4>{{ item.poi_name }}</h4>
                      <div class="similar-meta">
                        <el-rate v-model="item.comment_score" disabled size="small" />
                        <span class="similar-city">{{ item.city }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 错误状态 -->
        <el-empty v-else description="景点不存在或已删除" />
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import Layout from '../components/Layout.vue'
import { attractionAPI, recommendationAPI } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const favoriteLoading = ref(false)
const attraction = ref(null)
const similarAttractions = ref([])
const favorites = ref([])

const isFavorite = computed(() => {
  if (!attraction.value) return false
  return favorites.value.some(fav => fav.poi_id === attraction.value.poi_id)
})

const tagList = computed(() => {
  if (!attraction.value) return []
  // 后端返回的是tag_list字段
  const tags = attraction.value.tag_list || attraction.value.tags
  if (!tags) return []
  if (typeof tags === 'string') {
    // 处理可能是逗号分隔或JSON格式的标签
    try {
      // 尝试解析JSON格式
      const parsed = JSON.parse(tags)
      if (Array.isArray(parsed)) {
        return parsed.filter(t => t && t.trim())
      }
    } catch (e) {
      // 不是JSON，按逗号分隔处理
      return tags.split(',').map(t => t.trim()).filter(t => t)
    }
  }
  return []
})

const loadDetail = async () => {
  loading.value = true
  try {
    const id = route.params.id
    if (!id) {
      ElMessage.error('景点ID不能为空')
      return
    }
    
    const res = await attractionAPI.getDetail(id)
    if (res.code === 200) {
      attraction.value = res.data
      // 加载相似景点
      loadSimilarAttractions(id)
      // 如果已登录，检查收藏状态
      if (userStore.isLoggedIn) {
        checkFavoriteStatus()
      }
    } else {
      ElMessage.error(res.message || '加载景点详情失败')
    }
  } catch (error) {
    console.error('加载景点详情失败:', error)
    
    // 如果是422错误且可以重试（token问题），清除token后重试
    if (error.response?.status === 422 && error.retryWithoutToken) {
      console.log('Token无效，清除后重试（无需登录即可访问）')
      // 清除token并重试
      try {
        const res = await attractionAPI.getDetail(id)
        if (res.code === 200) {
          attraction.value = res.data
          loadSimilarAttractions(id)
          // 不再检查收藏状态，因为token已清除
          return
        }
      } catch (retryError) {
        console.error('重试失败:', retryError)
      }
    }
    
    const errorMessage = error.response?.data?.message || error.message || '加载景点详情失败，请稍后重试'
    
    // 如果是404，显示友好提示
    if (error.response?.status === 404) {
      ElMessage.warning('景点不存在或已删除')
      setTimeout(() => {
        router.push('/attractions')
      }, 2000)
    } else {
      ElMessage.error(errorMessage)
    }
  } finally {
    loading.value = false
  }
}

const loadSimilarAttractions = async (id) => {
  try {
    const res = await recommendationAPI.getSimilar(id)
    if (res.code === 200) {
      similarAttractions.value = res.data?.slice(0, 5) || []
    }
  } catch (error) {
    console.error('加载相似景点失败:', error)
  }
}

const checkFavoriteStatus = async () => {
  try {
    const res = await attractionAPI.getFavorites()
    if (res.code === 200) {
      favorites.value = res.data?.items || []
    }
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

const toggleFavorite = async () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  favoriteLoading.value = true
  try {
    if (isFavorite.value) {
      // 取消收藏 - 使用poi_id
      const res = await attractionAPI.removeFavorite(attraction.value.poi_id)
      if (res.code === 200) {
        ElMessage.success('已取消收藏')
        favorites.value = favorites.value.filter(fav => fav.poi_id !== attraction.value.poi_id)
      } else {
        ElMessage.error(res.message || '取消收藏失败')
      }
    } else {
      // 添加收藏
      const res = await attractionAPI.addFavorite({ poi_id: attraction.value.poi_id })
      if (res.code === 200) {
        ElMessage.success('收藏成功')
        favorites.value.push({ poi_id: attraction.value.poi_id, ...attraction.value })
      } else {
        ElMessage.error(res.message || '收藏失败')
      }
    }
  } catch (error) {
    console.error('操作收藏失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    favoriteLoading.value = false
  }
}

const goToDetail = (id) => {
  router.push(`/attraction/${id}`)
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.detail-container {
  padding: 0;
}

.detail-content {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  gap: 40px;
  margin-bottom: 40px;
  padding: 30px;
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.header-image {
  flex: 0 0 450px;
  height: 350px;
  border-radius: 16px;
  overflow: hidden;
}

.header-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.header-image:hover img {
  transform: scale(1.05);
}

.header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px 0;
}

.header-info h1 {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 24px;
  line-height: 1.3;
  text-shadow: 0 0 15px rgba(79, 172, 254, 0.6);
}

.detail-meta {
  margin-bottom: 24px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-text {
  color: #ff9900;
  font-size: 18px;
  font-weight: 600;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.detail-tags .el-tag {
  padding: 10px 20px;
  font-size: 14px;
  border-radius: 8px;
}

.detail-address {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 30px;
  font-size: 15px;
  padding: 12px 0;
}

.detail-address .el-icon {
  font-size: 18px;
  color: rgba(79, 172, 254, 0.8);
}

.detail-actions {
  display: flex;
  gap: 16px;
  margin-top: auto;
}

.detail-sections {
  margin-top: 30px;
}

.section-card {
  margin-bottom: 24px;
  padding: 30px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.section-card:hover {
  border-color: rgba(79, 172, 254, 0.4);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.2);
}

.section-card h2 {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(79, 172, 254, 0.3);
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.section-content {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.8;
  font-size: 15px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.similar-item {
  display: flex;
  gap: 16px;
  cursor: pointer;
  padding: 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(79, 172, 254, 0.1);
  margin-bottom: 12px;
}

.similar-item:last-child {
  margin-bottom: 0;
}

.similar-item:hover {
  background: rgba(79, 172, 254, 0.15);
  border-color: rgba(79, 172, 254, 0.3);
  transform: translateX(5px);
}

.similar-item img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
}

.similar-info {
  flex: 1;
  min-width: 0;
}

.similar-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.similar-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.similar-city {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.loading-wrapper {
  padding: 20px;
}

@media (max-width: 1200px) {
  .header-image {
    flex: 0 0 350px;
    height: 300px;
  }
}

@media (max-width: 768px) {
  .detail-content {
    padding: 20px;
  }

  .detail-header {
    flex-direction: column;
    gap: 24px;
    padding: 24px;
  }

  .header-image {
    flex: none;
    width: 100%;
    height: 250px;
  }

  .header-info h1 {
    font-size: 24px;
  }

  .detail-actions {
    flex-direction: column;
  }

  .detail-actions .el-button {
    width: 100%;
  }
}
</style>
