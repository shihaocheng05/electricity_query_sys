<template>
  <div class="dashboard">
    <h1 class="dashboard__title">仪表盘</h1>
    
    <!-- 统计卡片 -->
    <div class="dashboard__cards">
      <div class="dashboard__card">
        <div class="dashboard__card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">⚡</div>
        <div class="dashboard__card-content">
          <p class="dashboard__card-label">本月用电量</p>
          <h3 class="dashboard__card-value">{{ statistics.current_usage || 0 }} kWh</h3>
          <span class="dashboard__card-trend" :class="usageTrendClass">
            {{ usageTrendText }}
          </span>
        </div>
      </div>
      
      <div class="dashboard__card">
        <div class="dashboard__card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">💰</div>
        <div class="dashboard__card-content">
          <p class="dashboard__card-label">本月电费</p>
          <h3 class="dashboard__card-value">¥{{ statistics.current_cost || 0 }}</h3>
          <span class="dashboard__card-trend" :class="costTrendClass">
            {{ costTrendText }}
          </span>
        </div>
      </div>
      
      <div class="dashboard__card">
        <div class="dashboard__card-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">📊</div>
        <div class="dashboard__card-content">
          <p class="dashboard__card-label">累计用电量</p>
          <h3 class="dashboard__card-value">{{ statistics.total_usage || 0 }} kWh</h3>
          <span class="dashboard__card-info">全部时间</span>
        </div>
      </div>
      
      <div class="dashboard__card">
        <div class="dashboard__card-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">📋</div>
        <div class="dashboard__card-content">
          <p class="dashboard__card-label">待支付账单</p>
          <h3 class="dashboard__card-value">{{ unpaidBillsCount }}</h3>
          <span class="dashboard__card-info">共 ¥{{ unpaidBillsAmount }}</span>
        </div>
      </div>
    </div>
    
    <!-- 用电趋势图 -->
    <div class="dashboard__section">
      <div class="dashboard__section-header">
        <h2>用电趋势</h2>
        <div class="dashboard__period-selector">
          <button
            v-for="period in periods"
            :key="period.value"
            class="dashboard__period-button"
            :class="{ 'dashboard__period-button--active': selectedPeriod === period.value }"
            @click="handlePeriodChange(period.value)"
          >
            {{ period.label }}
          </button>
        </div>
      </div>
      <Chart :option="usageChartOption" height="350px" />
    </div>
    
    <!-- 最近账单 -->
    <div class="dashboard__section">
      <div class="dashboard__section-header">
        <h2>最近账单</h2>
        <router-link to="/bills" class="dashboard__link">查看全部 →</router-link>
      </div>
      <Table
        :columns="billColumns"
        :data="recentBills"
        :pagination="false"
      >
        <template #cell-status="{ value }">
          <span class="dashboard__bill-status" :class="`dashboard__bill-status--${value === 1 ? 'paid' : 'unpaid'}`">
            {{ value === 1 ? '已支付' : '未支付' }}
          </span>
        </template>
        <template #cell-actions="{ row }">
          <button
            v-if="row.status === 0"
            class="dashboard__pay-button"
            @click="handlePayBill(row.bill_id)"
          >
            支付
          </button>
          <span v-else class="dashboard__paid-text">✓ 已支付</span>
        </template>
      </Table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import queryApi from '@/services/api/query'
import billApi from '@/services/api/bill'
import Chart from '@/components/Chart.vue'
import Table from '@/components/Table.vue'
import type { EChartsOption } from 'echarts'
import type { BillInfo } from '@/services/api/bill'

interface Statistics {
  current_usage: number
  previous_usage: number
  current_cost: number
  previous_cost: number
  total_usage: number
}

interface Bill {
  bill_id: number
  bill_no: string
  billing_period: string
  amount: number
  status: number
}

const statistics = ref<Statistics>({
  current_usage: 0,
  previous_usage: 0,
  current_cost: 0,
  previous_cost: 0,
  total_usage: 0
})

const recentBills = ref<Bill[]>([])
const selectedPeriod = ref<'week' | 'month' | 'year'>('month')
const usageData = ref<{ date: string; usage: number }[]>([])

const periods = [
  { label: '本周', value: 'week' as const },
  { label: '本月', value: 'month' as const },
  { label: '本年', value: 'year' as const }
]

const billColumns = [
  { key: 'bill_no', label: '账单编号', width: '180px' },
  { key: 'billing_period', label: '账期', width: '150px' },
  { key: 'amount', label: '金额（元）', width: '120px' },
  { key: 'status', label: '状态', width: '100px' },
  { key: 'actions', label: '操作', width: '120px' }
]

const usageTrendClass = computed(() => {
  const diff = statistics.value.current_usage - statistics.value.previous_usage
  return diff > 0 ? 'dashboard__card-trend--up' : 'dashboard__card-trend--down'
})

const usageTrendText = computed(() => {
  const diff = statistics.value.current_usage - statistics.value.previous_usage
  const percent = statistics.value.previous_usage > 0
    ? Math.abs((diff / statistics.value.previous_usage) * 100).toFixed(1)
    : 0
  return diff > 0 ? `↑ ${percent}%` : `↓ ${percent}%`
})

const costTrendClass = computed(() => {
  const diff = statistics.value.current_cost - statistics.value.previous_cost
  return diff > 0 ? 'dashboard__card-trend--up' : 'dashboard__card-trend--down'
})

const costTrendText = computed(() => {
  const diff = statistics.value.current_cost - statistics.value.previous_cost
  const percent = statistics.value.previous_cost > 0
    ? Math.abs((diff / statistics.value.previous_cost) * 100).toFixed(1)
    : 0
  return diff > 0 ? `↑ ${percent}%` : `↓ ${percent}%`
})

const unpaidBillsCount = computed(() => {
  return recentBills.value.filter(b => b.status === 0).length
})

const unpaidBillsAmount = computed(() => {
  return recentBills.value
    .filter(b => b.status === 0)
    .reduce((sum, b) => sum + b.amount, 0)
    .toFixed(2)
})

const usageChartOption = computed<EChartsOption>(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: usageData.value.map(d => d.date),
    axisLine: {
      lineStyle: {
        color: '#e0e0e0'
      }
    },
    axisLabel: {
      color: '#666'
    }
  },
  yAxis: {
    type: 'value',
    name: '用电量 (kWh)',
    axisLine: {
      lineStyle: {
        color: '#e0e0e0'
      }
    },
    axisLabel: {
      color: '#666'
    },
    splitLine: {
      lineStyle: {
        color: '#f0f0f0'
      }
    }
  },
  series: [
    {
      name: '用电量',
      type: 'bar',
      data: usageData.value.map(d => d.usage),
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
        },
        borderRadius: [4, 4, 0, 0]
      }
    }
  ]
}))

const loadStatistics = async () => {
  try {
    const response = await queryApi.statisticsSummary({})
    if (response.data.code === 200 && response.data.data) {
      statistics.value = response.data.data
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadUsageData = async (period: 'week' | 'month' | 'year') => {
  try {
    // 将 week/month/year 映射到 day/month/year
    const periodMap = {
      'week': 'day',
      'month': 'month',
      'year': 'year'
    }
    
    const response = await queryApi.analyzeUser({
      analysis_period: periodMap[period],
      compare_period: false
    })
    if (response.data.code === 200 && response.data.data) {
      usageData.value = response.data.data.trend_data || []
    }
  } catch (error) {
    console.error('加载用电趋势失败:', error)
  }
}

const loadRecentBills = async () => {
  try {
    const response = await billApi.queryBills({
      page: 1,
      page_size: 5
    })
    if (response.data.code === 200 && response.data.data) {
      // 将 BillInfo 显示到 Bill 类型
      const bills = response.data.data.bills || []
      recentBills.value = bills.map((bill: BillInfo) => ({
        bill_id: bill.bill_id,
        bill_no: `BILL-${bill.bill_id}`, // 生成账单编号
        billing_period: bill.bill_month,
        amount: bill.bill_amount,
        status: bill.status === 'paid' ? 1 : 0 // 将字符串状态转换为数字
      }))
    }
  } catch (error) {
    console.error('加载账单失败:', error)
  }
}

const handlePeriodChange = (period: 'week' | 'month' | 'year') => {
  selectedPeriod.value = period
  loadUsageData(period)
}

const handlePayBill = async (billId: number) => {
  try {
    const bill = recentBills.value.find(b => b.bill_id === billId)
    if (!bill) {
      alert('账单不存在')
      return
    }
    const response = await billApi.payBill({
      bill_id: billId,
      payment_amount: bill.amount,
      payment_method: 'online'
    })
    if (response.data.code === 200) {
      alert('支付成功！')
      loadRecentBills()
      loadStatistics()
    }
  } catch (error: any) {
    alert(error.message || '支付失败')
  }
}

onMounted(() => {
  loadStatistics()
  loadUsageData('month')
  loadRecentBills()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard__title {
  margin: 0 0 24px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.dashboard__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.dashboard__card {
  display: flex;
  gap: 16px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.dashboard__card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.dashboard__card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.dashboard__card-content {
  flex: 1;
}

.dashboard__card-label {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.dashboard__card-value {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.dashboard__card-trend {
  font-size: 14px;
  font-weight: 600;
}

.dashboard__card-trend--up {
  color: #f56c6c;
}

.dashboard__card-trend--down {
  color: #67c23a;
}

.dashboard__card-info {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.dashboard__section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.dashboard__section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.dashboard__section-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.dashboard__link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  transition: opacity 0.2s;
}

.dashboard__link:hover {
  opacity: 0.8;
}

.dashboard__period-selector {
  display: flex;
  gap: 8px;
}

.dashboard__period-button {
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  background: white;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.dashboard__period-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.dashboard__period-button--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.dashboard__bill-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.dashboard__bill-status--paid {
  background: #f0f9ff;
  color: #0ea5e9;
}

.dashboard__bill-status--unpaid {
  background: #fff1f0;
  color: #f56c6c;
}

.dashboard__pay-button {
  padding: 6px 16px;
  border: none;
  background: var(--color-primary);
  color: white;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.dashboard__pay-button:hover {
  opacity: 0.9;
}

.dashboard__paid-text {
  color: #67c23a;
  font-size: 14px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .dashboard__cards {
    grid-template-columns: 1fr;
  }
  
  .dashboard__period-selector {
    flex-wrap: wrap;
  }
}
</style>
