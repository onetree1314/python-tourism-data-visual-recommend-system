<template>
  <Layout>
    <div class="attractions-container">
        <div class="attractions-content">
          <!-- 搜索和筛选 -->
          <div class="card-fresh filter-section">
            <el-form :model="searchForm" inline class="filter-form">
              <el-form-item label="关键词">
                <el-input 
                  v-model="searchForm.keyword" 
                  placeholder="请输入景点名称" 
                  clearable
                  style="width: 200px"
                  @keyup.enter="handleSearch">
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
              <el-form-item label="城市">
                <el-select 
                  v-model="searchForm.city" 
                  placeholder="请选择城市" 
                  clearable 
                  filterable 
                  style="width: 180px">
                  <el-option 
                    v-for="cityItem in cities" 
                    :key="cityItem.city || cityItem" 
                    :label="getCityLabel(cityItem)" 
                    :value="getCityValue(cityItem)" />
                </el-select>
              </el-form-item>
              <el-form-item label="价格范围">
                <el-select v-model="searchForm.priceRange" placeholder="价格范围" clearable style="width: 150px">
                  <el-option label="免费" value="free" />
                  <el-option label="0-50元" value="0-50" />
                  <el-option label="50-100元" value="50-100" />
                  <el-option label="100-200元" value="100-200" />
                  <el-option label="200元以上" value="200+" />
                </el-select>
              </el-form-item>
              <el-form-item label="排序">
                <el-select v-model="searchForm.sort" placeholder="排序方式" style="width: 150px">
                  <el-option label="默认" value="default" />
                  <el-option label="评分最高" value="score_desc" />
                  <el-option label="评分最低" value="score_asc" />
                  <el-option label="价格最低" value="price_asc" />
                  <el-option label="价格最高" value="price_desc" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSearch">
                  <el-icon><Search /></el-icon>
                  搜索
                </el-button>
                <el-button @click="resetSearch">重置</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 景点列表 -->
          <div v-if="attractions.length > 0" class="attractions-list">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="attraction in attractions" :key="attraction.poi_id">
                <div class="attraction-card card-fresh" @click="goToDetail(attraction.poi_id)">
                  <img :src="attraction.cover_image_url || '/placeholder.jpg'" :alt="attraction.poi_name" />
                  <div class="attraction-info">
                    <h3>{{ attraction.poi_name }}</h3>
                    <div class="attraction-meta">
                      <el-rate v-model="attraction.comment_score" disabled show-score text-color="#ff9900" />
                      <span class="city">{{ attraction.city }}</span>
                    </div>
                    <div class="attraction-price">{{ attraction.price }}</div>
                    <div v-if="attraction.address" class="attraction-address">
                      <el-icon><Location /></el-icon>
                      <span>{{ attraction.address }}</span>
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
          <el-empty v-else description="暂无景点数据" />
        </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import Layout from '../components/Layout.vue'
import { attractionAPI } from '../api'

const router = useRouter()
const loading = ref(false)
const cities = ref([])
const attractions = ref([])

const searchForm = ref({
  keyword: '',
  city: '',
  priceRange: '',
  sort: 'default'
})

const pagination = ref({
  page: 1,
  pageSize: 12,
  total: 0
})

const loadCities = async () => {
  try {
    const res = await attractionAPI.getCities()
    if (res.code === 200) {
      const data = res.data || []
      // 后端返回的是 [{city: '上海市', count: 149}, ...] 格式
      // 需要提取city字段
      cities.value = data.map(item => {
        if (typeof item === 'string') {
          return item
        } else if (item && item.city) {
          return item.city
        }
        return item
      }).filter(Boolean)
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

const loadAttractions = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }

    // 关键词搜索
    if (searchForm.value.keyword && searchForm.value.keyword.trim()) {
      params.keyword = searchForm.value.keyword.trim()
    }

    // 城市筛选
    if (searchForm.value.city) {
      params.city = searchForm.value.city
    }

    // 价格范围处理（后端使用is_free参数）
    if (searchForm.value.priceRange === 'free') {
      params.is_free = 'true'
    }

    // 排序方式（后端使用sort_by参数）
    if (searchForm.value.sort && searchForm.value.sort !== 'default') {
      const sortMap = {
        'score_desc': 'comment_score',
        'score_asc': 'comment_score', // 后端只支持降序，升序需要前端处理
        'price_asc': 'heat_score', // 价格排序暂不支持，使用默认排序
        'price_desc': 'heat_score'
      }
      params.sort_by = sortMap[searchForm.value.sort] || 'heat_score'
    }

    const res = await attractionAPI.getList(params)
    if (res.code === 200) {
      attractions.value = res.data?.items || []
      pagination.value.total = res.data?.total || 0
    } else {
      ElMessage.error(res.message || '加载景点列表失败')
    }
  } catch (error) {
    console.error('加载景点列表失败:', error)
    ElMessage.error('加载景点列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadAttractions()
}

const resetSearch = () => {
  searchForm.value = {
    keyword: '',
    city: '',
    priceRange: '',
    sort: 'default'
  }
  pagination.value.page = 1
  loadAttractions()
}

const handleSizeChange = () => {
  pagination.value.page = 1
  loadAttractions()
}

const handlePageChange = () => {
  loadAttractions()
}

const goToDetail = (id) => {
  router.push(`/attraction/${id}`)
}

onMounted(() => {
  loadCities()
  loadAttractions()
})

watch(() => searchForm.value.sort, () => {
  handleSearch()
})
</script>

<style scoped>
.attractions-container {
  padding: 0;
}

.attractions-content {
  padding: 20px;
}

.filter-section {
  margin-bottom: 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.attractions-list {
  margin-top: 20px;
}

.attraction-card {
  cursor: pointer;
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
  margin-bottom: 8px;
}

.attraction-address {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
