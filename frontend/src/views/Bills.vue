<template>
  <div class="bills">
    <h1 class="bills__title">账单管理</h1>
    
    <!-- 筛选器 -->
    <div class="bills__filters">
      <div class="bills__filter-group">
        <label>账期:</label>
        <input
          v-model="filters.billingPeriod"
          type="month"
          class="bills__input"
        />
      </div>
      
      <div class="bills__filter-group">
        <label>状态:</label>
        <select v-model="filters.status" class="bills__select">
          <option :value="undefined">全部</option>
          <option :value="0">未支付</option>
          <option :value="1">已支付</option>
        </select>
      </div>
      
      <div class="bills__filter-group">
        <label>金额范围:</label>
        <input
          v-model.number="filters.minAmount"
          type="number"
          placeholder="最小金额"
          class="bills__input bills__input--number"
        />
        <span>至</span>
        <input
          v-model.number="filters.maxAmount"
          type="number"
          placeholder="最大金额"
          class="bills__input bills__input--number"
        />
      </div>
      
      <button class="bills__search-button" @click="loadBills">
        🔍 查询
      </button>
      
      <button class="bills__reset-button" @click="resetFilters">
        🔄 重置
      </button>
    </div>
    
    <!-- 统计汇总 -->
    <div class="bills__summary">
      <div class="bills__summary-item bills__summary-item--total">
        <span class="bills__summary-label">总账单数</span>
        <span class="bills__summary-value">{{ totalBills }}</span>
      </div>
      <div class="bills__summary-item bills__summary-item--unpaid">
        <span class="bills__summary-label">待支付账单</span>
        <span class="bills__summary-value">{{ unpaidCount }}</span>
      </div>
      <div class="bills__summary-item bills__summary-item--amount">
        <span class="bills__summary-label">待支付金额</span>
        <span class="bills__summary-value">¥{{ unpaidAmount }}</span>
      </div>
    </div>
    
    <!-- 账单列表 -->
    <div class="bills__table-section">
      <div class="bills__table-header">
        <h2>账单列表</h2>
        <div class="bills__table-actions">
          <button
            v-if="selectedBills.length > 0"
            class="bills__batch-button"
            @click="handleBatchPay"
          >
            批量支付 ({{ selectedBills.length }})
          </button>
        </div>
      </div>
      
      <Table
        :columns="billColumns"
        :data="bills"
        :pagination="true"
        :page-size="pageSize"
        @page-change="handlePageChange"
      >
        <template #cell-checkbox="{ row }">
          <input
            v-if="row.status === 'UNPAID'"
            type="checkbox"
            :checked="selectedBills.includes(row.bill_id)"
            @change="toggleBillSelection(row.bill_id)"
          />
        </template>
        
        <template #cell-bill_no="{ value, row }">
          <a class="bills__bill-link" @click="viewBillDetail(row.bill_id)">
            {{ value }}
          </a>
        </template>
        
        <template #cell-status="{ value }">
          <span class="bills__status-badge" :class="`bills__status-badge--${value === 'PAID' ? 'paid' : 'unpaid'}`">
            {{ value === 'PAID' ? '✓ 已支付' : '⏳ 待支付' }}
          </span>
        </template>
        
        <template #cell-actions="{ row }">
          <div class="bills__action-buttons">
            <button class="bills__action-button" @click="viewBillDetail(row.bill_id)">
              查看
            </button>
            <button
              v-if="row.status === 'UNPAID'"
              class="bills__action-button bills__action-button--primary"
              @click="handlePayBill(row.bill_id)"
            >
              支付
            </button>
            <button
              v-if="row.status === 'UNPAID'"
              class="bills__action-button"
              @click="handleSendReminder(row.bill_id)"
            >
              提醒
            </button>
          </div>
        </template>
      </Table>
    </div>
    
    <!-- 账单详情弹窗 -->
    <div v-if="showDetailModal" class="bills__modal" @click="closeDetailModal">
      <div class="bills__modal-content" @click.stop>
        <div class="bills__modal-header">
          <h3>账单详情</h3>
          <button class="bills__modal-close" @click="closeDetailModal">✕</button>
        </div>
        <div v-if="billDetail" class="bills__modal-body">
          <div class="bills__detail-row">
            <span class="bills__detail-label">账单编号:</span>
            <span class="bills__detail-value">{{ billDetail.bill_no }}</span>
          </div>
          <div class="bills__detail-row">
            <span class="bills__detail-label">账期:</span>
            <span class="bills__detail-value">{{ billDetail.bill_month }}</span>
          </div>
          <div class="bills__detail-row">
            <span class="bills__detail-label">用电量:</span>
            <span class="bills__detail-value">{{ billDetail.total_usage }} kWh</span>
          </div>
          <div class="bills__detail-row">
            <span class="bills__detail-label">账单金额:</span>
            <span class="bills__detail-value bills__detail-value--amount">¥{{ billDetail.bill_amount }}</span>
          </div>
          <div class="bills__detail-row">
            <span class="bills__detail-label">状态:</span>
            <span class="bills__detail-value">
              <span :class="`bills__status-badge bills__status-badge--${billDetail.status === 'PAID' ? 'paid' : 'unpaid'}`">
                {{ billDetail.status === 'PAID' ? '已支付' : '待支付' }}
              </span>
            </span>
          </div>
          <div v-if="billDetail.payment_time" class="bills__detail-row">
            <span class="bills__detail-label">支付时间:</span>
            <span class="bills__detail-value">{{ billDetail.payment_time }}</span>
          </div>
          <div class="bills__detail-row">
            <span class="bills__detail-label">创建时间:</span>
            <span class="bills__detail-value">{{ billDetail.generate_time }}</span>
          </div>
        </div>
        <div class="bills__modal-footer">
          <button
            v-if="billDetail && billDetail.status === 'UNPAID'"
            class="bills__modal-button bills__modal-button--primary"
            @click="handlePayBill(billDetail.bill_id)"
          >
            立即支付
          </button>
          <button class="bills__modal-button" @click="closeDetailModal">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import billApi, { type BillInfo } from '@/services/api/bill'
import Table from '@/components/Table.vue'

interface BillFilters {
  billingPeriod?: string
  status?: number
  minAmount?: number
  maxAmount?: number
}

// 使用 BillInfo 类型
const filters = ref<BillFilters>({})
const bills = ref<BillInfo[]>([])
const selectedBills = ref<number[]>([])
const showDetailModal = ref(false)
const billDetail = ref<BillInfo | null>(null)
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

const billColumns = [
  { key: 'checkbox', label: '', width: '50px' },
  { key: 'bill_no', label: '账单编号', width: '180px' },
  { key: 'bill_month', label: '账期', width: '120px', sortable: true },
  { key: 'total_usage', label: '用电量 (kWh)', width: '120px', sortable: true },
  { key: 'bill_amount', label: '金额 (元)', width: '120px', sortable: true },
  { key: 'status', label: '状态', width: '120px' },
  { key: 'generate_time', label: '创建时间', width: '180px', sortable: true },
  { key: 'actions', label: '操作', width: '200px' }
]

const totalBills = computed(() => bills.value.length)
const unpaidCount = computed(() => bills.value.filter(b => b.status === 'UNPAID').length)
const unpaidAmount = computed(() => {
  return bills.value
    .filter(b => b.status === 'UNPAID')
    .reduce((sum, b) => sum + b.bill_amount, 0)
    .toFixed(2)
})

const loadBills = async () => {
  try {
    const params: any = {
      page: currentPage.value,
      per_page: pageSize.value,
    }
    
    // 如果有账期筛选，转换为 start_month 和 end_month
    if (filters.value.billingPeriod) {
      params.start_month = filters.value.billingPeriod
      params.end_month = filters.value.billingPeriod
    }
    
    if (filters.value.status !== undefined) {
      // 后端期望的是 UNPAID/PAID 字符串，需要转换
      params.status = filters.value.status === 0 ? 'UNPAID' : 'PAID'
    }
    
    const response = await billApi.queryBills(params)
    
    if (response.success && response.data) {
      // 映射后端返回的字段到前端期望的字段
      const backendBills = response.data.bills || []
      bills.value = backendBills.map((bill: any) => ({
        bill_id: bill.id,
        bill_no: bill.meter_code, // 暂时用 meter_code
        bill_month: bill.bill_month,
        total_usage: bill.total_electricity,
        bill_amount: bill.total_amount,
        status: typeof bill.status === 'string' ? bill.status : (bill.status === 0 ? 'UNPAID' : 'PAID'),
        generate_time: bill.create_time,
        due_date: bill.due_date,
        payment_time: bill.payment_time
      }))
      totalCount.value = response.data.pagination?.total || 0
    }
  } catch (error) {
    console.error('加载账单失败:', error)
  }
}

const resetFilters = () => {
  filters.value = {}
  currentPage.value = 1
  loadBills()
}

const handlePageChange = (page: number, size: number) => {
  currentPage.value = page
  pageSize.value = size
  loadBills()
}

const toggleBillSelection = (billId: number) => {
  const index = selectedBills.value.indexOf(billId)
  if (index > -1) {
    selectedBills.value.splice(index, 1)
  } else {
    selectedBills.value.push(billId)
  }
}

const handlePayBill = async (billId: number) => {
  if (!confirm('确认支付该账单吗？')) return
  
  // 找到对应账单获取金额
  const bill = bills.value.find(b => b.bill_id === billId) || billDetail.value
  if (!bill) {
    alert('账单不存在')
    return
  }
  
  try {
    const response = await billApi.payBill({
      bill_id: billId,
      payment_amount: bill.bill_amount,
      payment_method: 'ONLINE'
    })
    
    if (response.success) {
      alert('支付成功！')
      closeDetailModal()
      loadBills()
    }
  } catch (error: any) {
    alert(error.message || '支付失败')
  }
}

const handleBatchPay = async () => {
  if (!confirm(`确认支付选中的 ${selectedBills.value.length} 个账单吗？`)) return
  
  try {
    // 逐个支付（实际应该有批量支付接口）
    for (const billId of selectedBills.value) {
      const bill = bills.value.find(b => b.bill_id === billId)
      if (bill) {
        await billApi.payBill({
          bill_id: billId,
          payment_amount: bill.bill_amount,
          payment_method: 'ONLINE'
        })
      }
    }
    
    alert('批量支付成功！')
    selectedBills.value = []
    loadBills()
  } catch (error: any) {
    alert(error.message || '批量支付失败')
  }
}

const handleSendReminder = async (billId: number) => {
  try {
    const response = await billApi.sendBillReminder(billId)
    
    if (response.success) {
      alert('提醒已发送！')
    }
  } catch (error: any) {
    alert(error.message || '发送提醒失败')
  }
}

const viewBillDetail = async (billId: number) => {
  try {
    const response = await billApi.getBillDetail(billId)
    
    if (response.success && response.data) {
      billDetail.value = response.data
      showDetailModal.value = true
    }
  } catch (error) {
    console.error('加载账单详情失败:', error)
    alert('加载账单详情失败')
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  billDetail.value = null
}

onMounted(() => {
  loadBills()
})
</script>

<style scoped>
.bills {
  max-width: 1400px;
  margin: 0 auto;
}

.bills__title {
  margin: 0 0 24px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.bills__filters {
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

.bills__filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bills__filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.bills__input,
.bills__select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.bills__input--number {
  width: 120px;
}

.bills__input:focus,
.bills__select:focus {
  border-color: var(--color-primary);
}

.bills__search-button,
.bills__reset-button {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.bills__search-button {
  background: var(--color-primary);
  color: white;
}

.bills__reset-button {
  background: #f5f5f5;
  color: var(--color-text-secondary);
}

.bills__search-button:hover,
.bills__reset-button:hover {
  opacity: 0.9;
}

.bills__summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.bills__summary-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border-left: 4px solid;
}

.bills__summary-item--total {
  border-color: #409eff;
}

.bills__summary-item--unpaid {
  border-color: #f56c6c;
}

.bills__summary-item--amount {
  border-color: #e6a23c;
}

.bills__summary-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.bills__summary-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.bills__table-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.bills__table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.bills__table-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.bills__batch-button {
  padding: 8px 16px;
  border: none;
  background: var(--color-primary);
  color: white;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.bills__batch-button:hover {
  opacity: 0.9;
}

.bills__bill-link {
  color: var(--color-primary);
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

.bills__bill-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.bills__status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.bills__status-badge--paid {
  background: #f0f9ff;
  color: #0ea5e9;
}

.bills__status-badge--unpaid {
  background: #fff1f0;
  color: #f56c6c;
}

.bills__action-buttons {
  display: flex;
  gap: 8px;
}

.bills__action-button {
  padding: 4px 12px;
  border: 1px solid var(--color-border);
  background: white;
  color: var(--color-text-secondary);
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.bills__action-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.bills__action-button--primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.bills__action-button--primary:hover {
  opacity: 0.9;
}

.bills__modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.bills__modal-content {
  width: 90%;
  max-width: 600px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bills__modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.bills__modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.bills__modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.bills__modal-close:hover {
  background: var(--color-background-hover);
}

.bills__modal-body {
  padding: 24px;
}

.bills__detail-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.bills__detail-row:last-child {
  border-bottom: none;
}

.bills__detail-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.bills__detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
}

.bills__detail-value--amount {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
}

.bills__modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  background: #fafafa;
}

.bills__modal-button {
  padding: 8px 20px;
  border: 1px solid var(--color-border);
  background: white;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.bills__modal-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.bills__modal-button--primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.bills__modal-button--primary:hover {
  opacity: 0.9;
}

@media (max-width: 768px) {
  .bills__filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .bills__filter-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .bills__input--number {
    width: 100%;
  }
  
  .bills__summary {
    grid-template-columns: 1fr;
  }
  
  .bills__action-buttons {
    flex-direction: column;
  }
}
</style>
