<template>
  <Layout>
    <div class="home-container">
          <div class="overview-cards">
            <div class="card-fresh" v-for="item in overviewData" :key="item.title">
              <div class="card-icon" :style="{ background: item.color }">
                <el-icon :size="32"><component :is="item.icon" /></el-icon>
              </div>
              <div class="card-content">
                <div class="card-value">{{ item.value }}</div>
                <div class="card-title">{{ item.title }}</div>
              </div>
            </div>
          </div>
          
          <div class="hot-attractions">
            <h2>热门景点推荐</h2>
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="attraction in hotAttractions" :key="attraction.poi_id">
                <div class="attraction-card card-fresh" @click="goToDetail(attraction.poi_id)">
                  <img :src="attraction.cover_image_url || '/placeholder.jpg'" :alt="attraction.poi_name" />
                  <div class="attraction-info">
                    <h3>{{ attraction.poi_name }}</h3>
                    <div class="attraction-meta">
                      <el-rate v-model="attraction.comment_score" disabled show-score text-color="#ff9900" />
                      <span class="city">{{ attraction.city }}</span>
                    </div>
                    <div class="attraction-price">{{ attraction.price }}</div>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '../components/Layout.vue'
import { useUserStore } from '../stores/user'
import { analyticsAPI, recommendationAPI } from '../api'

const router = useRouter()
const userStore = useUserStore()
const overviewData = ref([])
const hotAttractions = ref([])

const loadOverview = async () => {
  try {
    const res = await analyticsAPI.getOverview()
    if (res.code === 200) {
      overviewData.value = [
        { title: '景点总数', value: res.data.total_attractions, icon: 'MapLocation', color: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' },
        { title: '城市数量', value: res.data.total_cities, icon: 'Location', color: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' },
        { title: '平均评分', value: res.data.avg_score, icon: 'Star', color: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' },
        { title: '总评论数', value: res.data.total_comments, icon: 'ChatDotRound', color: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }
      ]
    }
  } catch (error) {
    console.error(error)
  }
}

const loadHotAttractions = async () => {
  try {
    const res = await recommendationAPI.getHot({ limit: 8 })
    if (res.code === 200) {
      hotAttractions.value = res.data.map(item => ({
        ...item,
        comment_score: item.comment_score / 1
      }))
    }
  } catch (error) {
    console.error(error)
  }
}


const goToDetail = (id) => {
  router.push(`/attraction/${id}`)
}

onMounted(() => {
  loadOverview()
  loadHotAttractions()
})
</script>

<style scoped>
.home-container {
  padding: 0;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card-fresh {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-value {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.card-title {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
}

.hot-attractions h2 {
  margin-bottom: 20px;
  color: #fff;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.attraction-card {
  cursor: pointer;
  overflow: hidden;
  margin-bottom: 20px;
}

.attraction-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 12px;
}

.attraction-info {
  padding: 16px 0;
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
  color: rgba(255, 255, 255, 0.6);
}

.attraction-price {
  color: #3b82f6;
  font-weight: bold;
}
</style>
