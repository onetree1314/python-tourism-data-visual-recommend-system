<template>
  <Layout>
    <div class="favorites-container">
        <div class="favorites-content">
          <!-- 收藏列表 -->
          <div v-if="favorites.length > 0" class="favorites-list">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in favorites" :key="item.poi_id">
                <div class="attraction-card card-fresh">
                  <img :src="item.cover_image_url || '/placeholder.jpg'" :alt="item.poi_name" />
                  <div class="attraction-info">
                    <h3>{{ item.poi_name }}</h3>
                    <div class="attraction-meta">
                      <el-rate v-model="item.comment_score" disabled show-score text-color="#ff9900" />
                      <span class="city">{{ item.city }}</span>
                    </div>
                    <div class="attraction-price">{{ item.price }}</div>
                    <div class="card-actions">
                      <el-button type="primary" size="small" @click="goToDetail(item.poi_id)">
                        <el-icon><View /></el-icon>
                        查看详情
                      </el-button>
                      <el-button type="danger" size="small" @click="removeFavorite(item)">
                        <el-icon><Delete /></el-icon>
                        取消收藏
                      </el-button>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>

            <!-- 分页 -->
            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="pagination.page"
                v-model:page-size="pagination.pageSize"
                :page-sizes="[12, 24, 48, 96]"
                :total="pagination.total"
                layout="total, sizes, prev, pager, next, jumper"
                @size-change="handleSizeChange"
                @current-change="handlePageChange" />
            </div>
          </div>

          <!-- 加载中 -->
          <div v-else-if="loading" class="loading-wrapper">
            <el-skeleton :rows="8" animated />
          </div>

          <!-- 空状态 -->
          <el-empty v-else description="暂无收藏的景点">
            <el-button type="primary" @click="router.push('/attractions')">
              去浏览景点
            </el-button>
          </el-empty>
        </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import Layout from '../components/Layout.vue'
import { attractionAPI } from '../api'

const router = useRouter()
const loading = ref(false)
const favorites = ref([])

const pagination = ref({
  page: 1,
  pageSize: 12,
  total: 0
})

const loadFavorites = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }
    
    const res = await attractionAPI.getFavorites(params)
    if (res.code === 200) {
      favorites.value = res.data?.items || []
      pagination.value.total = res.data?.total || 0
    } else {
      ElMessage.error(res.message || '加载收藏列表失败')
    }
  } catch (error) {
    console.error('加载收藏列表失败:', error)
    ElMessage.error('加载收藏列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const removeFavorite = async (item) => {
  try {
    await ElMessageBox.confirm('确定要取消收藏这个景点吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    // 后端路由期望的是poi_id，不是收藏记录的id
    const poiId = item.poi_id
    if (!poiId) {
      ElMessage.error('景点ID不存在')
      return
    }
    
    const res = await attractionAPI.removeFavorite(poiId)
    if (res.code === 200) {
      ElMessage.success('已取消收藏')
      loadFavorites()
    } else {
      ElMessage.error(res.message || '取消收藏失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消收藏失败:', error)
      ElMessage.error('取消收藏失败，请稍后重试')
    }
  }
}

const goToDetail = (id) => {
  router.push(`/attraction/${id}`)
}

const handleSizeChange = () => {
  pagination.value.page = 1
  loadFavorites()
}

const handlePageChange = () => {
  loadFavorites()
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-container {
  padding: 0;
}

.favorites-content {
  padding: 20px;
}

.favorites-list {
  margin-top: 20px;
}

.attraction-card {
  overflow: hidden;
  margin-bottom: 20px;
  padding: 0;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.attraction-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.4);
  border-color: rgba(79, 172, 254, 0.4);
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
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

.loading-wrapper {
  padding: 20px;
}
</style>
