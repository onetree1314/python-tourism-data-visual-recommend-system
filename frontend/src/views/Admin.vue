<template>
  <div class="admin-dashboard">
    <!-- 顶部标题栏 -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="title">
          <span class="icon">📊</span>
          旅游景点管理系统 - 数据大屏
        </h1>
        <div class="datetime">{{ currentTime }}</div>
      </div>
    </div>

    <!-- 核心数据卡片 -->
    <div class="stats-cards">
      <div class="stat-card" v-for="(stat, index) in coreStats" :key="index">
        <div class="card-glass">
          <div class="stat-icon" :style="{ background: stat.gradient }">
            {{ stat.icon }}
          </div>
          <div class="stat-content">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-trend" :class="stat.trendClass">
              {{ stat.trend }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 左侧列 -->
      <div class="chart-column">
        <!-- 评分分布 -->
        <div class="chart-card">
          <div class="card-glass">
            <div class="card-header">
              <h3>评分分布统计</h3>
              <span class="badge">实时</span>
            </div>
            <div class="chart-container">
              <v-chart v-if="scoreDistributionOption" :option="scoreDistributionOption" autoresize style="width: 100%; height: 100%;" />
              <div v-else class="chart-loading">加载中...</div>
            </div>
          </div>
        </div>

        <!-- 城市排行 -->
        <div class="chart-card">
          <div class="card-glass">
            <div class="card-header">
              <h3>城市景点排行 TOP10</h3>
            </div>
            <div class="chart-container">
              <v-chart v-if="cityRankOption" :option="cityRankOption" autoresize style="width: 100%; height: 100%;" />
              <div v-else class="chart-loading">加载中...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间列 - 中国地图 -->
      <div class="chart-column">
        <div class="chart-card large map-card">
          <div class="card-glass">
            <div class="card-header">
              <h3>中国景点分布地图</h3>
              <span class="badge">实时</span>
            </div>
            <div class="chart-container map-container" v-if="mapLoaded">
              <v-chart :option="chinaMapOption" autoresize style="width: 100%; height: 100%;" />
            </div>
            <div v-else class="map-loading">正在加载地图数据...</div>
          </div>
        </div>
      </div>

      <!-- 右侧列 -->
      <div class="chart-column">
        <!-- 价格分布 -->
        <div class="chart-card">
          <div class="card-glass">
            <div class="card-header">
              <h3>价格区间分布</h3>
            </div>
            <div class="chart-container">
              <v-chart v-if="priceDistributionOption" :option="priceDistributionOption" autoresize style="width: 100%; height: 100%;" />
              <div v-else class="chart-loading">加载中...</div>
            </div>
          </div>
        </div>

        <!-- 用户增长趋势 -->
        <div class="chart-card">
          <div class="card-glass">
            <div class="card-header">
              <h3>用户登录趋势</h3>
            </div>
            <div class="chart-container">
              <v-chart v-if="loginTrendOption" :option="loginTrendOption" autoresize style="width: 100%; height: 100%;" />
              <div v-else class="chart-loading">加载中...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { use, registerMap } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart, MapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  GeoComponent,
  VisualMapComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { analyticsAPI, adminAPI } from '../api'
import { ElMessage } from 'element-plus'

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  MapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  GeoComponent,
  VisualMapComponent
])

const currentTime = ref('')
const coreStats = ref([
  { icon: '🎯', label: '景点总数', value: '0', trend: '今日新增 0', trendClass: 'up', gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' },
  { icon: '👥', label: '用户总数', value: '0', trend: '活跃用户 0', trendClass: 'up', gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' },
  { icon: '⭐', label: '平均评分', value: '0', trend: '高分景点占比 0%', trendClass: 'stable', gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' },
  { icon: '💬', label: '评论总数', value: '0', trend: '用户参与度高', trendClass: 'up', gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' }
])

const scoreDistributionOption = ref(null)
const cityRankOption = ref(null)
const hotAttractionsOption = ref(null)
const priceDistributionOption = ref(null)
const loginTrendOption = ref(null)
const chinaMapOption = ref(null)
const mapLoaded = ref(false)

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

let timeInterval = null

onMounted(async () => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  await loadData()
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
})

const loadData = async () => {
  try {
    // 加载概览数据
    try {
      const overviewRes = await analyticsAPI.getOverview()
      console.log('概览数据:', overviewRes)
      if (overviewRes.code === 200) {
        const data = overviewRes.data
        coreStats.value[0].value = data.total_attractions.toLocaleString()
        coreStats.value[2].value = data.avg_score.toFixed(1)
        coreStats.value[3].value = data.total_comments.toLocaleString()
      }
    } catch (error) {
      console.error('加载概览数据失败:', error)
    }

    // 加载管理员统计
    try {
      const statsRes = await adminAPI.getStatistics()
      console.log('管理员统计数据:', statsRes)
      if (statsRes.code === 200) {
        const data = statsRes.data
        coreStats.value[1].value = data.total_users.toLocaleString()
        coreStats.value[1].trend = `活跃用户 ${data.active_users}`
        coreStats.value[0].trend = `今日新增 ${data.today_attractions}`
        
      // 登录趋势
      if (data.login_trend && data.login_trend.length > 0) {
        await setupLoginTrend(data.login_trend)
      } else {
        console.warn('登录趋势数据为空')
      }
      }
    } catch (error) {
      console.error('加载管理员统计数据失败:', error)
    }

    // 加载评分分布
    try {
      const scoreRes = await analyticsAPI.getScoreDistribution()
      console.log('评分分布数据:', scoreRes)
      if (scoreRes.code === 200 && scoreRes.data) {
        await setupScoreDistribution(scoreRes.data)
      } else {
        console.warn('评分分布数据格式错误:', scoreRes)
      }
    } catch (error) {
      console.error('加载评分分布失败:', error)
    }

    // 加载城市分析
    try {
      const cityRes = await analyticsAPI.getCityAnalysis()
      console.log('城市分析数据:', cityRes)
      if (cityRes.code === 200 && cityRes.data) {
        await setupCityRank(cityRes.data)
      } else {
        console.warn('城市分析数据格式错误:', cityRes)
      }
    } catch (error) {
      console.error('加载城市分析失败:', error)
    }

    // 加载价格销量分析
    try {
      const priceRes = await analyticsAPI.getPriceSalesAnalysis()
      console.log('价格销量分析数据:', priceRes)
      if (priceRes.code === 200 && priceRes.data) {
        await setupPriceDistribution(priceRes.data)
        await setupHotAttractions(priceRes.data)
      } else {
        console.warn('价格销量分析数据格式错误:', priceRes)
      }
    } catch (error) {
      console.error('加载价格销量分析失败:', error)
    }

    // 加载省份统计数据（地图）
    try {
      const provinceRes = await adminAPI.getProvinceStatistics()
      console.log('省份统计数据:', provinceRes)
      if (provinceRes.code === 200 && provinceRes.data) {
        console.log('省份数据详情:', provinceRes.data)
        await setupChinaMap(provinceRes.data)
      } else {
        console.warn('省份数据格式错误:', provinceRes)
      }
    } catch (error) {
      console.error('加载省份统计数据失败:', error)
      ElMessage.warning('地图数据加载失败，请检查权限')
    }
    
    ElMessage.success('数据加载成功')
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('数据加载失败，请检查权限')
  }
}

// 评分分布图表
const setupScoreDistribution = async (data) => {
  if (!data || !data.distribution || data.distribution.length === 0) {
    console.warn('评分分布数据为空:', data)
    return
  }
  
  await nextTick()
  
  scoreDistributionOption.value = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 20, 40, 0.9)',
      borderColor: '#4facfe',
      borderWidth: 1,
      textStyle: { color: '#fff' }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: 'rgba(0, 20, 40, 0.5)',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        color: '#fff'
      },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' }
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

// 城市排行图表
const setupCityRank = async (data) => {
  if (!data || !data.city_data || data.city_data.length === 0) {
    console.warn('城市排行数据为空:', data)
    return
  }
  
  const top10 = data.city_data.slice(0, 10)
  console.log('设置城市排行图表，前10个城市:', top10)
  
  await nextTick()
  
  cityRankOption.value = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0, 20, 40, 0.9)',
      borderColor: '#4facfe',
      borderWidth: 1,
      textStyle: { color: '#fff' }
    },
    grid: { left: '15%', right: '10%', top: '10%', bottom: '10%' },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#4facfe' } },
      splitLine: { lineStyle: { color: 'rgba(79, 172, 254, 0.1)' } },
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'category',
      data: top10.map(item => item.city),
      axisLine: { lineStyle: { color: '#4facfe' } },
      axisLabel: { color: '#fff' }
    },
    series: [{
      type: 'bar',
      data: top10.map(item => item.count),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#4facfe' },
            { offset: 1, color: '#00f2fe' }
          ]
        },
        borderRadius: [0, 10, 10, 0]
      },
      barWidth: '60%'
    }]
  }
}

// 热门景点图表
const setupHotAttractions = async (data) => {
  if (!data || !data.hot_attractions || data.hot_attractions.length === 0) {
    console.warn('热门景点数据为空:', data)
    return
  }
  
  const attractions = data.hot_attractions.slice(0, 20)
  
  await nextTick()
  
  hotAttractionsOption.value = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0, 20, 40, 0.9)',
      borderColor: '#43e97b',
      borderWidth: 1,
      textStyle: { color: '#fff' },
      formatter: (params) => {
        const item = params[0]
        return `${item.name}<br/>评论数: ${item.value.toLocaleString()}`
      }
    },
    grid: { left: '5%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: attractions.map(item => item.poi_name),
      axisLine: { lineStyle: { color: '#43e97b' } },
      axisLabel: {
        color: '#fff',
        rotate: 45,
        interval: 0,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#43e97b' } },
      splitLine: { lineStyle: { color: 'rgba(67, 233, 123, 0.1)' } },
      axisLabel: { color: '#fff' }
    },
    series: [{
      type: 'bar',
      data: attractions.map(item => item.comment_count),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 1, x2: 0, y2: 0,
          colorStops: [
            { offset: 0, color: '#43e97b' },
            { offset: 1, color: '#38f9d7' }
          ]
        },
        borderRadius: [10, 10, 0, 0]
      },
      barWidth: '50%'
    }]
  }
}

// 价格分布图表
const setupPriceDistribution = async (data) => {
  if (!data || !data.free_vs_paid || !data.price_distribution) {
    console.warn('价格分布数据为空或不完整:', data)
    return
  }
  
  console.log('设置价格分布图表，数据:', data)
  
  await nextTick()
  
  priceDistributionOption.value = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 20, 40, 0.9)',
      borderColor: '#667eea',
      borderWidth: 1,
      textStyle: { color: '#fff' }
    },
    series: [{
      type: 'pie',
      radius: '70%',
      center: ['50%', '50%'],
      data: [
        { value: data.free_vs_paid.free, name: '免费景点' },
        { value: data.free_vs_paid.paid, name: '收费景点' }
      ].concat(data.price_distribution.map(item => ({
        value: item.count,
        name: item.range
      }))),
      itemStyle: {
        borderRadius: 8,
        borderColor: 'rgba(0, 20, 40, 0.5)',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        color: '#fff'
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

// 登录趋势图表
const setupLoginTrend = async (data) => {
  if (!data || data.length === 0) {
    console.warn('登录趋势数据为空')
    return
  }
  
  await nextTick()
  
  loginTrendOption.value = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 20, 40, 0.9)',
      borderColor: '#f093fb',
      borderWidth: 1,
      textStyle: { color: '#fff' }
    },
    grid: { left: '10%', right: '10%', top: '15%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date.slice(5)),
      axisLine: { lineStyle: { color: '#f093fb' } },
      axisLabel: { color: '#fff' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#f093fb' } },
      splitLine: { lineStyle: { color: 'rgba(240, 147, 251, 0.1)' } },
      axisLabel: { color: '#fff' }
    },
    series: [{
      type: 'line',
      data: data.map(item => item.count),
      smooth: true,
      lineStyle: {
        width: 3,
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#f093fb' },
            { offset: 1, color: '#f5576c' }
          ]
        }
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(240, 147, 251, 0.3)' },
            { offset: 1, color: 'rgba(245, 87, 108, 0.1)' }
          ]
        }
      },
      itemStyle: { color: '#f093fb' }
    }]
  }
}

// 中国地图图表
const setupChinaMap = async (data) => {
  if (!data || data.length === 0) {
    console.warn('没有省份数据', data)
    return
  }
  
  console.log('设置地图数据，共', data.length, '个省份')
  console.log('前5个省份数据:', data.slice(0, 5))
  
  // 计算最大值和最小值
  const values = data.map(item => item.value || 0)
  const maxValue = Math.max(...values, 1)
  const minValue = Math.min(...values, 0)
  
  console.log('数据范围:', minValue, '-', maxValue)
  
  // 加载并注册中国地图数据
  try {
    const response = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const mapData = await response.json()
    registerMap('china', mapData)
    mapLoaded.value = true
  } catch (error) {
    console.warn('无法加载地图数据:', error)
    // 即使地图数据加载失败，也显示图表（使用默认地图）
    mapLoaded.value = true
  }
  
  // 等待DOM更新
  await new Promise(resolve => setTimeout(resolve, 100))
  
  chinaMapOption.value = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 20, 40, 0.95)',
      borderColor: '#4facfe',
      borderWidth: 2,
      textStyle: { color: '#fff', fontSize: 14 },
      formatter: (params) => {
        // 查找匹配的省份数据
        const matchedData = data.find(item => {
          // 尝试多种匹配方式
          return item.name === params.name || 
                 item.name === params.name + '省' ||
                 item.name === params.name + '市' ||
                 item.name === params.name + '自治区' ||
                 params.name === item.name ||
                 params.name === item.name + '省' ||
                 params.name === item.name + '市' ||
                 params.name === item.name + '自治区'
        })
        
        if (matchedData && matchedData.value !== undefined && matchedData.value > 0) {
          return `${params.name}<br/>景点数量: ${matchedData.value.toLocaleString()}`
        }
        // 如果params.data存在，也尝试使用
        if (params.data && params.data.value !== undefined && params.data.value > 0) {
          return `${params.name}<br/>景点数量: ${params.data.value.toLocaleString()}`
        }
        return `${params.name}<br/>暂无数据`
      }
    },
    visualMap: {
      min: minValue,
      max: maxValue,
      left: 'left',
      top: 'bottom',
      text: ['高', '低'],
      textStyle: { color: '#fff' },
      inRange: {
        color: [
          '#313695', '#4575b4', '#74add1', '#abd9e9',
          '#e0f3f8', '#ffffcc', '#fee090', '#fdae61',
          '#f46d43', '#d73027', '#a50026'
        ]
      },
      calculable: true,
      show: true
    },
    series: [{
      name: '景点数量',
      type: 'map',
      map: 'china',
      roam: true,
      zoom: 1.2,
      data: data,
      label: {
        show: true,
        formatter: (params) => {
          // 尝试多种匹配方式
          const item = data.find(d => {
            return d.name === params.name || 
                   d.name === params.name + '省' ||
                   d.name === params.name + '市' ||
                   d.name === params.name + '自治区' ||
                   params.name === d.name ||
                   params.name === d.name + '省' ||
                   params.name === d.name + '市' ||
                   params.name === d.name + '自治区'
          })
          if (item && item.value > 0) {
            return item.value.toLocaleString()
          }
          return ''
        },
        color: '#fff',
        fontSize: 11
      },
      itemStyle: {
        areaColor: 'rgba(79, 172, 254, 0.1)',
        borderColor: '#4facfe',
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          areaColor: 'rgba(67, 233, 123, 0.6)',
          borderColor: '#43e97b',
          borderWidth: 2
        },
        label: {
          color: '#fff',
          fontSize: 14,
          fontWeight: 'bold'
        }
      }
    }]
  }
}
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a1628 0%, #1a2332 50%, #0f1b2d 100%);
  padding: 20px;
  overflow-x: hidden;
}

.dashboard-header {
  margin-bottom: 30px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 15px;
  text-shadow: 0 2px 10px rgba(79, 172, 254, 0.5);
}

.icon {
  font-size: 36px;
}

.datetime {
  font-size: 18px;
  color: #4facfe;
  font-weight: 500;
  letter-spacing: 1px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  position: relative;
}

.card-glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.card-glass:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.3);
  border-color: rgba(79, 172, 254, 0.3);
}

.stat-icon {
  width: 70px;
  height: 70px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 5px;
}

.stat-trend {
  font-size: 12px;
  color: #43e97b;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.chart-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-card {
  position: relative;
}

.chart-card.large {
  height: 100%;
}

.chart-card .card-glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.chart-card .card-glass:hover {
  border-color: rgba(79, 172, 254, 0.3);
  box-shadow: 0 12px 40px rgba(79, 172, 254, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.badge {
  padding: 4px 12px;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 20px;
  font-size: 12px;
  color: #fff;
  font-weight: 500;
}

.chart-container {
  flex: 1;
  min-height: 300px;
  width: 100%;
  position: relative;
}

.chart-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.map-container {
  min-height: 600px;
  height: 100%;
  width: 100%;
  position: relative;
}

.map-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
}

.map-card {
  grid-column: span 1;
}

@media (max-width: 1600px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .title {
    font-size: 24px;
  }
  
  .datetime {
    font-size: 14px;
  }
}
</style>
