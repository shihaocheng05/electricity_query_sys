<template>
  <div class="region-analysis">
    <h1 class="region-analysis__title">片区分析</h1>

    <!-- 片区选择和周期选择 -->
    <div class="region-analysis__controls">
      <div class="control-group">
        <label>选择片区</label>
        <select v-model="selectedRegionId" @change="loadAnalysisData">
          <option v-for="region in regions" :key="region.region_id" :value="region.region_id">
            {{ region.region_name }}
          </option>
        </select>
      </div>
      <div class="control-group">
        <label>分析周期</label>
        <select v-model="analysisPeriod" @change="loadAnalysisData">
          <option value="day">日</option>
          <option value="month">月</option>
          <option value="year">年</option>
        </select>
      </div>
      <div class="control-group">
        <label>
          <input type="checkbox" v-model="comparePeriod" @change="loadAnalysisData" />
          对比同期
        </label>
      </div>
    </div>

    <!-- 统计概览卡片 -->
    <div v-if="regionSummary" class="summary-cards">
      <div class="summary-card">
        <div class="summary-card__icon">📊</div>
        <div class="summary-card__content">
          <div class="summary-card__label">总用电量</div>
          <div class="summary-card__value">{{ regionSummary.total_usage }} kWh</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-card__icon">👥</div>
        <div class="summary-card__content">
          <div class="summary-card__label">用户数量</div>
          <div class="summary-card__value">{{ regionSummary.user_count }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-card__icon">⚡</div>
        <div class="summary-card__content">
          <div class="summary-card__label">电表数量</div>
          <div class="summary-card__value">{{ regionSummary.meter_count }}</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-card__icon">⚠️</div>
        <div class="summary-card__content">
          <div class="summary-card__label">欠费用户</div>
          <div class="summary-card__value">{{ regionSummary.arrear_users }}</div>
        </div>
      </div>
    </div>

    <!-- 用电趋势图表 -->
    <div v-if="analysisData" class="chart-container">
      <h2 class="chart-title">用电趋势分析</h2>
      <div class="chart-placeholder">
        <div class="trend-list">
          <div v-for="item in analysisData.trend_data" :key="item.period" class="trend-item">
            <div class="trend-period">{{ item.period }}</div>
            <div class="trend-bar">
              <div 
                class="trend-bar-fill" 
                :style="{ width: (item.total_electricity / maxUsage * 100) + '%' }"
              ></div>
            </div>
            <div class="trend-value">{{ item.total_electricity }} kWh</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 对比数据 -->
    <div v-if="analysisData?.comparison" class="comparison-card">
      <h2 class="chart-title">同期对比</h2>
      <div class="comparison-content">
        <div class="comparison-item">
          <span class="comparison-label">当前周期总用电量：</span>
          <span class="comparison-value">{{ analysisData.comparison.current_period_total }} kWh</span>
        </div>
        <div class="comparison-item">
          <span class="comparison-label">对比周期总用电量：</span>
          <span class="comparison-value">{{ analysisData.comparison.compare_period_total }} kWh</span>
        </div>
        <div class="comparison-item">
          <span class="comparison-label">差值：</span>
          <span class="comparison-value" :class="analysisData.comparison.difference >= 0 ? 'positive' : 'negative'">
            {{ analysisData.comparison.difference }} kWh
          </span>
        </div>
        <div class="comparison-item">
          <span class="comparison-label">变化率：</span>
          <span class="comparison-value" :class="analysisData.comparison.change_rate >= 0 ? 'positive' : 'negative'">
            {{ analysisData.comparison.change_rate }}% ({{ analysisData.comparison.trend }})
          </span>
        </div>
      </div>
    </div>

    <!-- 高峰时段 -->
    <div v-if="analysisData?.peak_hours && analysisData.peak_hours.length > 0" class="peak-hours-card">
      <h2 class="chart-title">用电高峰时段</h2>
      <div class="peak-hours-list">
        <div v-for="peak in analysisData.peak_hours" :key="peak.hour" class="peak-hour-item">
          <div class="peak-hour-time">{{ peak.hour }}:00 - {{ peak.hour + 1 }}:00</div>
          <div class="peak-hour-bar">
            <div 
              class="peak-hour-bar-fill" 
              :class="{ 'is-peak': peak.is_peak }"
              :style="{ width: (peak.avg_usage / maxPeakUsage * 100) + '%' }"
            ></div>
          </div>
          <div class="peak-hour-value">{{ peak.avg_usage }} kWh</div>
        </div>
      </div>
    </div>

    <!-- 统计摘要 -->
    <div v-if="analysisData?.summary" class="summary-info">
      <h2 class="chart-title">统计摘要</h2>
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-item-label">总用电量：</span>
          <span class="summary-item-value">{{ analysisData.summary.total_electricity }} kWh</span>
        </div>
        <div class="summary-item">
          <span class="summary-item-label">平均用电量：</span>
          <span class="summary-item-value">{{ analysisData.summary.avg_electricity }} kWh</span>
        </div>
        <div class="summary-item">
          <span class="summary-item-label">最高用电量：</span>
          <span class="summary-item-value">{{ analysisData.summary.max_electricity }} kWh</span>
        </div>
        <div class="summary-item">
          <span class="summary-item-label">最低用电量：</span>
          <span class="summary-item-value">{{ analysisData.summary.min_electricity }} kWh</span>
        </div>
        <div class="summary-item">
          <span class="summary-item-label">户均用电量：</span>
          <span class="summary-item-value">{{ analysisData.summary.avg_per_meter }} kWh</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { toast } from '@/utils/toast'
import { loading as loadingUtil } from '@/utils/loading'
import { httpService } from '@/services/http'

interface Region {
  region_id: number
  region_name: string
  region_code: string
}

interface RegionSummary {
  region_name: string
  total_usage: number
  user_count: number
  meter_count: number
  arrear_users: number
}

interface AnalysisData {
  trend_data: Array<{
    period: string
    total_electricity: number
    peak_electricity: number
    valley_electricity: number
  }>
  comparison?: {
    current_period_total: number
    compare_period_total: number
    difference: number
    change_rate: number
    trend: string
  }
  peak_hours?: Array<{
    hour: number
    avg_usage: number
    is_peak: boolean
  }>
  summary: {
    total_electricity: number
    avg_electricity: number
    max_electricity: number
    min_electricity: number
    avg_per_meter: number
  }
}

const regions = ref<Region[]>([])
const selectedRegionId = ref<number | null>(null)
const analysisPeriod = ref('month')
const comparePeriod = ref(false)
const regionSummary = ref<RegionSummary | null>(null)
const analysisData = ref<AnalysisData | null>(null)
const loading = ref(false)

const maxUsage = computed(() => {
  if (!analysisData.value?.trend_data) return 1
  return Math.max(...analysisData.value.trend_data.map(d => d.total_electricity))
})

const maxPeakUsage = computed(() => {
  if (!analysisData.value?.peak_hours) return 1
  return Math.max(...analysisData.value.peak_hours.map(p => p.avg_usage))
})

// 加载片区列表
const loadRegions = async () => {
  try {
    const response = await httpService.get('/system/region/list')
    if (response.data && response.data.regions) {
      regions.value = response.data.regions
      if (regions.value.length > 0) {
        selectedRegionId.value = regions.value[0].region_id
        loadAnalysisData()
      } else {
        toast.error('暂无片区数据，请先创建片区')
      }
    }
  } catch (error: any) {
    console.error('加载片区列表失败:', error)
    toast.error('加载片区列表失败: ' + (error.message || '未知错误'))
  }
}

// 加载片区统计概览
const loadRegionSummary = async () => {
  if (!selectedRegionId.value) return
  
  try {
    const response = await httpService.get('/query/statistics/summary', {
      params: {
        scope: 'region',
        scope_id: selectedRegionId.value
      }
    })
    if (response.data) {
      regionSummary.value = response.data
    }
  } catch (error: any) {
    console.error('加载片区概览失败:', error)
  }
}

// 加载分析数据
const loadAnalysisData = async () => {
  if (!selectedRegionId.value) return
  
  loading.value = true
  try {
    await loadRegionSummary()
    
    const response = await httpService.get('/query/analyze/region', {
      params: {
        region_id: selectedRegionId.value,
        analysis_period: analysisPeriod.value,
        compare_period: comparePeriod.value
      }
    })
    
    if (response.data) {
      analysisData.value = response.data
    }
  } catch (error: any) {
    console.error('加载分析数据失败:', error)
    toast.error(error.message || '加载分析数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRegions()
})
</script>

<style scoped>
.region-analysis {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.region-analysis__title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-text);
}

.region-analysis__controls {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  padding: 20px;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.control-group select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.control-group input[type="checkbox"] {
  margin-right: 8px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.summary-card__icon {
  font-size: 36px;
}

.summary-card__content {
  flex: 1;
}

.summary-card__label {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.summary-card__value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
}

.chart-container, .comparison-card, .peak-hours-card, .summary-info {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--color-text);
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-item {
  display: grid;
  grid-template-columns: 120px 1fr 120px;
  align-items: center;
  gap: 12px;
}

.trend-period {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.trend-bar {
  height: 32px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.trend-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4f46e5, #6366f1);
  transition: width 0.3s;
}

.trend-value {
  font-size: 14px;
  font-weight: 500;
  text-align: right;
  color: var(--color-text);
}

.comparison-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comparison-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.comparison-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.comparison-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.comparison-value.positive {
  color: #ef4444;
}

.comparison-value.negative {
  color: #10b981;
}

.peak-hours-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.peak-hour-item {
  display: grid;
  grid-template-columns: 150px 1fr 100px;
  align-items: center;
  gap: 12px;
}

.peak-hour-time {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.peak-hour-bar {
  height: 28px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.peak-hour-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  transition: width 0.3s;
}

.peak-hour-bar-fill.is-peak {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.peak-hour-value {
  font-size: 14px;
  font-weight: 500;
  text-align: right;
  color: var(--color-text);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.summary-item {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
}

.summary-item-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.summary-item-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: white;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
