<template>
  <div class="usage-analysis">
    <h1 class="usage-analysis__title">用电分析</h1>
    
    <!-- 筛选器 -->
    <div class="usage-analysis__filters">
      <div class="usage-analysis__filter-group">
        <label>时间范围:</label>
        <input
          v-model="filters.startDate"
          type="date"
          class="usage-analysis__input"
        />
        <span>至</span>
        <input
          v-model="filters.endDate"
          type="date"
          class="usage-analysis__input"
        />
      </div>
      
      <div class="usage-analysis__filter-group">
        <label>周期:</label>
        <select v-model="filters.period" class="usage-analysis__select">
          <option value="day">按天</option>
          <option value="week">按周</option>
          <option value="month">按月</option>
        </select>
      </div>
      
      <div class="usage-analysis__filter-group">
        <label>分析类型:</label>
        <select v-model="filters.analysisType" class="usage-analysis__select">
          <option value="usage_trend">用电趋势</option>
          <option value="peak_valley">峰谷分时</option>
          <option value="comparison">同比环比</option>
        </select>
      </div>
      
      <button class="usage-analysis__search-button" @click="loadAnalysisData">
        🔍 查询
      </button>
    </div>
    
    <!-- 统计摘要 -->
    <div class="usage-analysis__summary">
      <div class="usage-analysis__summary-item">
        <span class="usage-analysis__summary-label">总用电量</span>
        <span class="usage-analysis__summary-value">{{ summary.total_usage }} kWh</span>
      </div>
      <div class="usage-analysis__summary-item">
        <span class="usage-analysis__summary-label">平均日用电</span>
        <span class="usage-analysis__summary-value">{{ summary.avg_daily }} kWh</span>
      </div>
      <div class="usage-analysis__summary-item">
        <span class="usage-analysis__summary-label">峰时用电</span>
        <span class="usage-analysis__summary-value">{{ summary.peak_usage }} kWh</span>
      </div>
      <div class="usage-analysis__summary-item">
        <span class="usage-analysis__summary-label">谷时用电</span>
        <span class="usage-analysis__summary-value">{{ summary.valley_usage }} kWh</span>
      </div>
    </div>
    
    <!-- 主图表 -->
    <div class="usage-analysis__chart-section">
      <Chart :option="mainChartOption" height="450px" />
    </div>
    
    <!-- 详细数据表格 -->
    <div class="usage-analysis__table-section">
      <div class="usage-analysis__table-header">
        <h2>详细数据</h2>
        <button class="usage-analysis__export-button" @click="handleExport">
          📥 导出数据
        </button>
      </div>
      <Table
        :columns="tableColumns"
        :data="tableData"
        :pagination="true"
        :page-size="10"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import queryApi from '@/services/api/query'
import usageApi from '@/services/api/usage'
import Chart from '@/components/Chart.vue'
import Table from '@/components/Table.vue'
import { toast } from '@/utils/toast'
import { loading } from '@/utils/loading'
import type { EChartsOption } from 'echarts'

interface Filters {
  startDate: string
  endDate: string
  period: 'day' | 'week' | 'month'
  analysisType: 'usage_trend' | 'peak_valley' | 'comparison'
}

interface Summary {
  total_usage: number
  avg_daily: number
  peak_usage: number
  valley_usage: number
}

interface UsageDataPoint {
  date?: string
  period?: string
  usage?: number
  total_electricity?: number
  peak_usage?: number
  peak_electricity?: number
  valley_usage?: number
  valley_electricity?: number
  cost?: number
}

const filters = ref<Filters>({
  startDate: getDefaultStartDate(),
  endDate: getDefaultEndDate(),
  period: 'day',
  analysisType: 'usage_trend'
})

const summary = ref<Summary>({
  total_usage: 0,
  avg_daily: 0,
  peak_usage: 0,
  valley_usage: 0
})

const chartData = ref<UsageDataPoint[]>([])
const tableData = ref<any[]>([])

const tableColumns = computed(() => {
  const baseColumns = [
    { key: 'date', label: '日期', width: '150px' },
    { key: 'usage', label: '用电量 (kWh)', width: '150px', sortable: true }
  ]
  
  if (filters.value.analysisType === 'peak_valley') {
    return [
      ...baseColumns,
      { key: 'peak_usage', label: '峰时用电 (kWh)', width: '150px', sortable: true },
      { key: 'valley_usage', label: '谷时用电 (kWh)', width: '150px', sortable: true },
      { key: 'cost', label: '电费 (元)', width: '120px', sortable: true }
    ]
  }
  
  return [
    ...baseColumns,
    { key: 'cost', label: '电费 (元)', width: '120px', sortable: true }
  ]
})

const mainChartOption = computed<EChartsOption>(() => {
  if (filters.value.analysisType === 'peak_valley') {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['峰时用电', '谷时用电']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: chartData.value.map(d => d.date)
      },
      yAxis: {
        type: 'value',
        name: '用电量 (kWh)'
      },
      series: [
        {
          name: '峰时用电',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.peak_usage || 0),
          itemStyle: {
            color: '#f56c6c'
          }
        },
        {
          name: '谷时用电',
          type: 'bar',
          stack: 'total',
          data: chartData.value.map(d => d.valley_usage || 0),
          itemStyle: {
            color: '#67c23a'
          }
        }
      ]
    }
  }
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['用电量', '电费']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.map(d => d.period || d.date || ''),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '用电量 (kWh)',
        position: 'left',
        axisLine: {
          lineStyle: {
            color: '#5470c6'
          }
        }
      },
      {
        type: 'value',
        name: '电费 (元)',
        position: 'right',
        axisLine: {
          lineStyle: {
            color: '#91cc75'
          }
        }
      }
    ],
    series: [
      {
        name: '用电量',
        type: 'bar',
        yAxisIndex: 0,
        data: chartData.value.map(d => d.total_electricity || d.usage || 0),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' }
            ]
          }
        }
      },
      {
        name: '电费',
        type: 'line',
        yAxisIndex: 1,
        data: chartData.value.map(d => d.cost || 0),
        itemStyle: {
          color: '#91cc75'
        },
        smooth: true
      }
    ]
  }
})

function getDefaultStartDate(): string {
  const date = new Date()
  date.setDate(date.getDate() - 30)
  return date.toISOString().split('T')[0] as string
}

function getDefaultEndDate(): string {
  return new Date().toISOString().split('T')[0] as string
}

const loadAnalysisData = async () => {
  try {
    loading.show('加载分析数据...')
    
    // 将period映射到analysis_period
    const periodMap: Record<string, string> = {
      'day': 'day',
      'week': 'month',  // 周期使用月来近似
      'month': 'month'
    }
    
    const response = await queryApi.analyzeUser({
      analysis_period: periodMap[filters.value.period] || 'month',
      compare_period: filters.value.analysisType === 'comparison'
    })
    
    if (response.data.code === 200 && response.data.data) {
      chartData.value = response.data.data.trend_data || []
      tableData.value = chartData.value.map((d, index) => ({
        id: index,
        ...d
      }))
      
      // 计算摘要
      const totalUsage = chartData.value.reduce((sum, d) => sum + (d.total_electricity || d.usage || 0), 0)
      const days = chartData.value.length || 1
      
      summary.value = {
        total_usage: Number(totalUsage.toFixed(2)),
        avg_daily: Number((totalUsage / days).toFixed(2)),
        peak_usage: Number(chartData.value.reduce((sum, d) => sum + (d.peak_electricity || d.peak_usage || 0), 0).toFixed(2)),
        valley_usage: Number(chartData.value.reduce((sum, d) => sum + (d.valley_electricity || d.valley_usage || 0), 0).toFixed(2))
      }
      
      toast.success('数据加载成功')
    }
  } catch (error: any) {
    console.error('加载分析数据失败:', error)
    toast.error(error.message || '加载分析数据失败，请重试')
  } finally {
    loading.hide()
  }
}

const handleExport = async () => {
  try {
    loading.show('导出数据中...')
    const response = await queryApi.exportData({
      start_date: filters.value.startDate,
      end_date: filters.value.endDate,
      export_type: 'usage_analysis',
      format: 'excel'
    })
    
    if (response.data.code === 200 && response.data.data) {
      // 获取下载链接和文件名
      const downloadUrl: string = (response.data.data.download_url ?? response.data.data.file_name ?? '') as string
      const fileName: string = (response.data.data.filename ?? response.data.data.file_name ?? 'export.xlsx') as string

      // 验证下载链接
      if (!downloadUrl || downloadUrl.trim() === '') {
        toast.error('导出失败：未获取到下载链接')
        return
      }

      // 创建下载链接
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = fileName
      link.click()
      toast.success('导出成功！')
    }
  } catch (error) {
    console.error('导出失败:', error)
    toast.error('导出失败，请重试')
  } finally {
    loading.hide()
  }
}

onMounted(() => {
  loadAnalysisData()
})
</script>

<style scoped>
.usage-analysis {
  max-width: 1400px;
  margin: 0 auto;
}

.usage-analysis__title {
  margin: 0 0 24px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.usage-analysis__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.usage-analysis__filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.usage-analysis__filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.usage-analysis__input,
.usage-analysis__select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.usage-analysis__input:focus,
.usage-analysis__select:focus {
  border-color: var(--color-primary);
}

.usage-analysis__search-button {
  padding: 8px 20px;
  border: none;
  background: var(--color-primary);
  color: white;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.usage-analysis__search-button:hover {
  opacity: 0.9;
}

.usage-analysis__summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.usage-analysis__summary-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.usage-analysis__summary-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.usage-analysis__summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
}

.usage-analysis__chart-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.usage-analysis__table-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.usage-analysis__table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.usage-analysis__table-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.usage-analysis__export-button {
  padding: 8px 16px;
  border: 1px solid var(--color-primary);
  background: white;
  color: var(--color-primary);
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.usage-analysis__export-button:hover {
  background: var(--color-primary);
  color: white;
}

@media (max-width: 768px) {
  .usage-analysis__filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .usage-analysis__filter-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .usage-analysis__summary {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
