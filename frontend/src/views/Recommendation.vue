<template>
  <Layout>
    <div class="recommendation-container">
        <div class="recommendation-content">
          <!-- 推荐表单 -->
          <div class="card-fresh form-section">
            <h2>个性化推荐设置</h2>
            <el-form :model="form" label-width="120px" class="recommendation-form">
              <el-form-item>
                <template #label>
                  <span>偏好城市</span>
                </template>
                <el-select v-model="form.city" placeholder="请选择城市" clearable filterable style="width: 100%">
                  <el-option 
                    v-for="cityItem in cities" 
                    :key="getCityValue(cityItem)" 
                    :label="getCityLabel(cityItem)" 
                    :value="getCityValue(cityItem)" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <template #label>
                  <span>价格范围</span>
                </template>
                <el-slider v-model="priceRange" range :min="0" :max="1000" :step="10" show-stops />
                <div class="price-display">
                  <span>¥{{ priceRange[0] }}</span>
                  <span>¥{{ priceRange[1] }}</span>
                </div>
              </el-form-item>
              <el-form-item>
                <template #label>
                  <span>最低评分</span>
                </template>
                <el-rate v-model="form.minScore" :max="5" show-score text-color="#ff9900" />
              </el-form-item>
              <el-form-item>
                <template #label>
                  <span>推荐数量</span>
                </template>
                <el-input-number v-model="form.limit" :min="5" :max="50" :step="5" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="large" @click="getRecommendations" :loading="loading">
                  <el-icon><Search /></el-icon>
                  开始推荐
                </el-button>
                <el-button size="large" @click="resetForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 推荐结果 -->
          <div v-if="recommendations.length > 0" class="results-section">
            <h2>为您推荐 <span class="result-count">({{ recommendations.length }} 个景点)</span></h2>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in recommendations" :key="item.poi_id">
                <div class="attraction-card card-fresh" @click="goToDetail(item.poi_id)">
                  <img :src="item.cover_image_url || '/placeholder.jpg'" :alt="item.poi_name" />
                  <div class="attraction-info">
                    <h3>{{ item.poi_name }}</h3>
                    <div class="attraction-meta">
                      <el-rate v-model="item.comment_score" disabled show-score text-color="#ff9900" />
                      <span class="city">{{ item.city }}</span>
                    </div>
                    <div v-if="item.price" class="attraction-price">{{ item.price }}</div>
                    <!-- AI推荐理由 -->
                    <div v-if="item.recommend_reason" class="recommend-reason">
                      <el-icon><ChatDotRound /></el-icon>
                      <span>{{ item.recommend_reason }}</span>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 空状态 -->
          <el-empty v-else-if="!loading" description="请设置推荐条件并点击开始推荐" />
        </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import Layout from '../components/Layout.vue'
import { recommendationAPI, attractionAPI } from '../api'

const router = useRouter()
const loading = ref(false)
const cities = ref([])
const recommendations = ref([])
const priceRange = ref([0, 1000])

const form = ref({
  city: '',
  minScore: 0,
  limit: 10
})

const loadCities = async () => {
  try {
    const res = await attractionAPI.getCities()
    if (res.code === 200) {
      const data = res.data || []
      // 后端返回的是 [{city: '上海市', count: 149}, ...] 格式
      // 保留原始数据以便显示数量
      cities.value = data
    }
  } catch (error) {
    console.error('加载城市列表失败:', error)
  }
}

// 辅助函数：获取城市标签（用于显示）
const getCityLabel = (cityItem) => {
  if (typeof cityItem === 'string') {
    return cityItem
  } else if (cityItem && cityItem.city) {
    return `${cityItem.city} (${cityItem.count || 0})`
  }
  return String(cityItem)
}

// 辅助函数：获取城市值（用于提交）
const getCityValue = (cityItem) => {
  if (typeof cityItem === 'string') {
    return cityItem
  } else if (cityItem && cityItem.city) {
    return cityItem.city
  }
  return String(cityItem)
}

const getRecommendations = async () => {
  loading.value = true
  try {
    // 构建preferences对象
    const preferences = {}
    if (form.value.city) {
      preferences.city = form.value.city
    }
    if (priceRange.value[0] > 0 || priceRange.value[1] < 1000) {
      preferences.min_price = priceRange.value[0]
      preferences.max_price = priceRange.value[1]
    }
    if (form.value.minScore > 0) {
      preferences.min_score = form.value.minScore
    }
    
    const params = {
      preferences: preferences,
      limit: form.value.limit
    }
    
    const res = await recommendationAPI.getIntelligent(params)
    if (res.code === 200) {
      // 后端返回的数据结构是 { recommendations: [...], ai_analysis: '...' }
      const data = res.data
      if (data && Array.isArray(data.recommendations)) {
        recommendations.value = data.recommendations
      } else if (Array.isArray(data)) {
        recommendations.value = data
      } else if (data && Array.isArray(data.items)) {
        recommendations.value = data.items
      } else {
        recommendations.value = []
      }
      
      const count = recommendations.value.length
      if (count > 0) {
        ElMessage.success(`为您找到 ${count} 个推荐景点`)
      } else {
        ElMessage.warning('未找到符合条件的推荐景点，请调整筛选条件')
      }
    } else {
      ElMessage.error(res.message || '推荐失败')
    }
  } catch (error) {
    console.error('获取推荐失败:', error)
    ElMessage.error('获取推荐失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    city: '',
    minScore: 0,
    limit: 10
  }
  priceRange.value = [0, 1000]
  recommendations.value = []
}

const goToDetail = (id) => {
  router.push(`/attraction/${id}`)
}

onMounted(() => {
  loadCities()
})
</script>

<style scoped>
.recommendation-container {
  padding: 0;
}

.recommendation-content {
  padding: 20px;
}

.form-section {
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.form-section h2 {
  margin-bottom: 24px;
  color: #fff;
  font-size: 20px;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.recommendation-form :deep(.el-form-item) {
  margin-bottom: 28px;
}

.recommendation-form :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.price-display {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 500;
}

.results-section {
  margin-top: 30px;
}

.results-section h2 {
  margin-bottom: 24px;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.result-count {
  font-size: 16px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7);
  margin-left: 8px;
}

.attraction-card {
  cursor: pointer;
  overflow: hidden;
  margin-bottom: 20px;
  padding: 0;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.attraction-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 12px 12px 0 0;
}

.attraction-info {
  padding: 16px;
}

.attraction-info h3 {
  font-size: 16px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #fff;
}

.attraction-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.city {
  font-size: 12px;
  color: #999;
}

.attraction-price {
  color: #3b82f6;
  font-weight: bold;
  margin-bottom: 8px;
}

.recommend-reason {
  margin-top: 12px;
  padding: 10px;
  background: rgba(79, 172, 254, 0.15);
  border-left: 3px solid rgba(79, 172, 254, 0.6);
  border-radius: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: flex-start;
  gap: 6px;
  line-height: 1.5;
  backdrop-filter: blur(10px);
}

.recommend-reason .el-icon {
  margin-top: 2px;
  color: rgba(79, 172, 254, 0.8);
  flex-shrink: 0;
}

.recommend-reason span {
  flex: 1;
}
</style>
