<template>
  <Layout>
    <div class="analytics-page">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1>📈 数据分析中心</h1>
        <el-button type="primary" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>

    <!-- 数据概览卡片 -->
    <div class="overview-cards">
      <div class="overview-card" v-for="(item, index) in overviewData" :key="index">
        <div class="card-inner">
          <div class="card-icon" :style="{ background: item.color }">
            {{ item.icon }}
          </div>
          <div class="card-info">
            <div class="card-label">{{ item.label }}</div>
            <div class="card-value">{{ item.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 评分分析 -->
      <div class="chart-box">
        <div class="box-header">
          <h3>🌟 评分分布分析</h3>
        </div>
        <div class="box-content">
          <v-chart :option="scoreChartOption" autoresize style="height: 350px;" />
        </div>
      </div>

      <!-- 城市分析 -->
      <div class="chart-box">
        <div class="box-header">
          <h3>🏙️ 城市景点分析</h3>
        </div>
        <div class="box-content">
          <v-chart :option="cityChartOption" autoresize style="height: 350px;" />
        </div>
      </div>

      <!-- 价格分析 -->
      <div class="chart-box full-width">
        <div class="box-header">
          <h3>💰 价格与评分关系分析</h3>
        </div>
        <div class="box-content">
          <v-chart :option="priceScoreOption" autoresize style="height: 400px;" />
        </div>
      </div>

      <!-- 标签词云 -->
      <div class="chart-box full-width">
        <div class="box-header">
          <h3>🏷️ 热门标签词云</h3>
        </div>
        <div class="box-content">
          <div class="tag-cloud">
            <span
              v-for="(tag, index) in tagCloudData"
              :key="index"
              class="tag-item"
              :style="{
                fontSize: `${12 + tag.value / 10}px`,
                color: getTagColor(index)
              }"
            >
              {{ tag.name }}
            </span>
          </div>
        </div>
      </div>

      <!-- 景点等级分布 -->
      <div class="chart-box">
        <div class="box-header">
          <h3>🎯 景点等级分布</h3>
        </div>
        <div class="box-content">
          <v-chart :option="levelChartOption" autoresize style="height: 350px;" />
        </div>
      </div>

      <!-- TOP景点列表 -->
      <div class="chart-box top-list-box">
        <div class="box-header">
          <h3>🏆 评分TOP10景点</h3>
        </div>
        <div class="box-content">
          <div class="top-list">
            <div
              v-for="(item, index) in topAttractions"
              :key="index"
              class="top-item"
              :class="`rank-${index + 1}-item`"
            >
              <div class="rank-wrapper">
                <div class="rank" :class="`rank-${index + 1}`">
                  <span class="rank-number">{{ index + 1 }}</span>
                  <div class="rank-crown" v-if="index < 3">
                    <span v-if="index === 0">👑</span>
                    <span v-else-if="index === 1">🥈</span>
                    <span v-else>🥉</span>
                  </div>
                </div>
              </div>
              <div class="attraction-info">
                <div class="name">{{ item.poi_name }}</div>
                <div class="city-info">
                  <el-icon><Location /></el-icon>
                  <span class="city">{{ item.city }}</span>
                </div>
              </div>
              <div class="score-wrapper">
                <div class="score">{{ item.comment_score }}</div>
                <div class="score-label">评分</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import Layout from '../components/Layout.vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart, RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { analyticsAPI } from '../api'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const loading = ref(false)
const overviewData = ref([
  { icon: '🎯', label: '景点总数', value: '0', color: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' },
  { icon: '🏙️', label: '城市数量', value: '0', color: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' },
  { icon: '⭐', label: '平均评分', value: '0', color: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' },
  { icon: '💬', label: '评论总数', value: '0', color: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }
])

const scoreChartOption = ref({})
const cityChartOption = ref({})
const priceScoreOption = ref({})
const levelChartOption = ref({})
const tagCloudData = ref([])
const topAttractions = ref([])

onMounted(() => {
  loadAllData()
})

const refreshData = () => {
  loadAllData()
}

const loadAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadScoreDistribution(),
      loadCityAnalysis(),
      loadPriceSalesAnalysis(),
      loadTagAnalysis()
    ])
    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

// 加载概览数据
const loadOverview = async () => {
  const res = await analyticsAPI.getOverview()
  if (res.code === 200) {
    const data = res.data
    overviewData.value[0].value = data.total_attractions.toLocaleString()
    overviewData.value[1].value = data.total_cities.toLocaleString()
    overviewData.value[2].value = data.avg_score.toFixed(1)
    overviewData.value[3].value = data.total_comments.toLocaleString()
  }
}

// 加载评分分布
const loadScoreDistribution = async () => {
  const res = await analyticsAPI.getScoreDistribution()
  if (res.code === 200) {
    const data = res.data
    topAttractions.value = data.top_attractions.slice(0, 10)
    
    scoreChartOption.value = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#4facfe',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      legend: {
        orient: 'vertical',
        right: '10%',
        top: 'center',
        textStyle: { color: '#333' }
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}个',
          color: '#333'
        },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' }
        },
        data: data.distribution.map((item, index) => ({
          value: item.count,
          name: item.range,
          itemStyle: {
            color: ['#3b82f6', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6'][index]
          }
        }))
      }]
    }
  }
}

// 加载城市分析
const loadCityAnalysis = async () => {
  const res = await analyticsAPI.getCityAnalysis()
  if (res.code === 200) {
    const data = res.data
    const top15 = data.city_data.slice(0, 15)
    
    cityChartOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#4facfe',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      grid: { left: '12%', right: '8%', top: '10%', bottom: '10%' },
      xAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#4facfe' } },
        splitLine: { lineStyle: { color: '#e8e8e8' } },
        axisLabel: { color: '#666' }
      },
      yAxis: {
        type: 'category',
        data: top15.map(item => item.city),
        axisLine: { lineStyle: { color: '#4facfe' } },
        axisLabel: { color: '#333' }
      },
      series: [{
        type: 'bar',
        data: top15.map(item => item.count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#4facfe' },
              { offset: 1, color: '#00f2fe' }
            ]
          },
          borderRadius: [0, 8, 8, 0]
        },
        barWidth: '60%',
        label: {
          show: true,
          position: 'right',
          color: '#333'
        }
      }]
    }
    
    // 景点等级分布
    levelChartOption.value = {
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#43e97b',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      series: [{
        type: 'pie',
        radius: '65%',
        center: ['50%', '50%'],
        data: data.level_stats.map((item, index) => ({
          value: item.count,
          name: item.level,
          itemStyle: {
            color: ['#10b981', '#3b82f6', '#f59e0b', '#06b6d4'][index]
          }
        })),
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}个\n({d}%)',
          color: '#333'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
  }
}

// 加载价格销量分析
const loadPriceSalesAnalysis = async () => {
  const res = await analyticsAPI.getPriceSalesAnalysis()
  if (res.code === 200) {
    const data = res.data
    
    priceScoreOption.value = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#667eea',
        borderWidth: 1,
        textStyle: { color: '#333' }
      },
      legend: {
        data: ['平均评分', '景点数量'],
        top: '5%',
        textStyle: { color: '#333' }
      },
      grid: { left: '10%', right: '10%', top: '15%', bottom: '15%' },
      xAxis: {
        type: 'category',
        data: data.price_score_relation.map(item => item.price_range),
        axisLine: { lineStyle: { color: '#667eea' } },
        axisLabel: { color: '#333', rotate: 30 }
      },
      yAxis: [
        {
          type: 'value',
          name: '平均评分',
          min: 0,
          max: 5,
          axisLine: { lineStyle: { color: '#43e97b' } },
          splitLine: { lineStyle: { color: '#e8e8e8' } },
          axisLabel: { color: '#666' }
        },
        {
          type: 'value',
          name: '景点数量',
          axisLine: { lineStyle: { color: '#4facfe' } },
          splitLine: { show: false },
          axisLabel: { color: '#666' }
        }
      ],
      series: [
        {
          name: '平均评分',
          type: 'line',
          data: data.price_score_relation.map(item => item.avg_score),
          smooth: true,
          lineStyle: {
            width: 3,
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: '#43e97b' },
                { offset: 1, color: '#38f9d7' }
              ]
            }
          },
          itemStyle: { color: '#43e97b' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(67, 233, 123, 0.3)' },
                { offset: 1, color: 'rgba(67, 233, 123, 0.05)' }
              ]
            }
          }
        },
        {
          name: '景点数量',
          type: 'bar',
          yAxisIndex: 1,
          data: data.price_score_relation.map(item => item.count),
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 1, x2: 0, y2: 0,
              colorStops: [
                { offset: 0, color: '#4facfe' },
                { offset: 1, color: '#00f2fe' }
              ]
            },
            borderRadius: [8, 8, 0, 0]
          },
          barWidth: '40%'
        }
      ]
    }
  }
}

// 加载标签分析
const loadTagAnalysis = async () => {
  const res = await analyticsAPI.getTagAnalysis()
  if (res.code === 200) {
    const data = res.data
    tagCloudData.value = data.wordcloud_data.slice(0, 50)
  }
}

// 获取标签颜色
const getTagColor = (index) => {
  const colors = [
    '#3b82f6', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
  ]
  return colors[index % colors.length]
}
</script>

<style scoped>
.analytics-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 0 20px rgba(79, 172, 254, 0.5);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.overview-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  padding: 25px;
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.4);
  border-color: rgba(79, 172, 254, 0.4);
}

.card-inner {
  display: flex;
  align-items: center;
  gap: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

.card-info {
  flex: 1;
}

.card-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.card-value {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-box {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 15px;
  padding: 20px;
  border: 1px solid rgba(79, 172, 254, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.chart-box:hover {
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.3);
  border-color: rgba(79, 172, 254, 0.4);
}

.chart-box.full-width {
  grid-column: 1 / -1;
}

.box-header {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(79, 172, 254, 0.3);
}

.box-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
}

.box-content {
  padding: 10px 0;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  padding: 20px;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.tag-item {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  font-weight: 500;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tag-item:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
}

.top-list-box {
  grid-column: 1 / -1;
}

.top-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-height: 600px;
  overflow-y: auto;
  padding: 10px;
}

.top-list::-webkit-scrollbar {
  width: 8px;
}

.top-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}

.top-list::-webkit-scrollbar-thumb {
  background: rgba(79, 172, 254, 0.5);
  border-radius: 10px;
}

.top-list::-webkit-scrollbar-thumb:hover {
  background: rgba(79, 172, 254, 0.7);
}

.top-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(79, 172, 254, 0.2);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.top-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(79, 172, 254, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.top-item:hover {
  background: rgba(79, 172, 254, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(79, 172, 254, 0.3);
  border-color: rgba(79, 172, 254, 0.5);
}

.top-item:hover::before {
  opacity: 1;
}

.rank-1-item {
  border-color: rgba(245, 158, 11, 0.4);
  background: rgba(245, 158, 11, 0.1);
}

.rank-1-item:hover {
  background: rgba(245, 158, 11, 0.2);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.4);
}

.rank-2-item {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(59, 130, 246, 0.1);
}

.rank-2-item:hover {
  background: rgba(59, 130, 246, 0.2);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.rank-3-item {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.1);
}

.rank-3-item:hover {
  background: rgba(16, 185, 129, 0.2);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
}

.rank-wrapper {
  position: relative;
}

.rank {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  color: #fff;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
  position: relative;
  transition: all 0.3s ease;
}

.top-item:hover .rank {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
}

.rank-number {
  line-height: 1;
}

.rank-crown {
  font-size: 12px;
  margin-top: 2px;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.rank-1 {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.5);
}

.rank-1:hover {
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.7);
}

.rank-2 {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.5);
}

.rank-2:hover {
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.7);
}

.rank-3 {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.5);
}

.rank-3:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.7);
}

.attraction-info {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-shadow: 0 0 10px rgba(79, 172, 254, 0.3);
}

.city-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.city-info .el-icon {
  font-size: 14px;
}

.score-wrapper {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.score {
  font-size: 24px;
  font-weight: 700;
  color: #43e97b;
  text-shadow: 0 0 15px rgba(67, 233, 123, 0.6);
  line-height: 1;
  margin-bottom: 4px;
}

.score-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

@media (max-width: 1400px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
  }
}
</style>
