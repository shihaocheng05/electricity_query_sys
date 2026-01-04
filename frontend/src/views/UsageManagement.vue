<template>
  <div class="usage-management">
    <h1 class="usage-management__title">用电数据管理</h1>

    <!-- 人工录入表单卡片 -->
    <div class="usage-management__card">
      <div class="usage-management__card-header">
        <h2 class="usage-management__card-title">人工录入数据</h2>
      </div>
      <div class="usage-management__form">
        <div class="usage-management__form-row">
          <div class="usage-management__form-group">
            <label class="usage-management__label">电表ID *</label>
            <input
              v-model.number="form.meter_id"
              type="number"
              class="usage-management__input"
              placeholder="请输入电表ID"
              required
            />
          </div>
          <div class="usage-management__form-group">
            <label class="usage-management__label">电量读数 (kWh) *</label>
            <input
              v-model.number="form.electricity"
              type="number"
              step="0.01"
              class="usage-management__input"
              placeholder="请输入电量读数"
              required
            />
          </div>
        </div>
        <div class="usage-management__form-row">
          <div class="usage-management__form-group">
            <label class="usage-management__label">采集时间 *</label>
            <input
              v-model="form.collect_time"
              type="datetime-local"
              class="usage-management__input"
              required
            />
          </div>
          <div class="usage-management__form-group">
            <label class="usage-management__label">电压 (V)</label>
            <input
              v-model.number="form.voltage"
              type="number"
              step="0.1"
              class="usage-management__input"
              placeholder="请输入电压"
            />
          </div>
        </div>
        <div class="usage-management__form-row">
          <div class="usage-management__form-group">
            <label class="usage-management__label">电流 (A)</label>
            <input
              v-model.number="form.current"
              type="number"
              step="0.01"
              class="usage-management__input"
              placeholder="请输入电流"
            />
          </div>
          <div class="usage-management__form-group">
            <!-- 占位 -->
          </div>
        </div>
        <div class="usage-management__form-actions">
          <button class="usage-management__button usage-management__button--secondary" @click="resetForm">
            重置
          </button>
          <button class="usage-management__button usage-management__button--primary" @click="handleSubmit" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交数据' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 数据查询和列表 -->
    <div class="usage-management__card">
      <div class="usage-management__card-header">
        <h2 class="usage-management__card-title">用电数据查询</h2>
        <button class="usage-management__button usage-management__button--primary" @click="loadUsageData">
          🔄 刷新数据
        </button>
      </div>
      
      <!-- 查询条件 -->
      <div class="usage-management__filters">
        <div class="usage-management__filter-group">
          <label class="usage-management__filter-label">电表ID:</label>
          <input
            v-model.number="filters.meter_id"
            type="number"
            class="usage-management__filter-input"
            placeholder="电表ID"
          />
        </div>
        <div class="usage-management__filter-group">
          <label class="usage-management__filter-label">开始时间:</label>
          <input
            v-model="filters.start_date"
            type="datetime-local"
            class="usage-management__filter-input"
          />
        </div>
        <div class="usage-management__filter-group">
          <label class="usage-management__filter-label">结束时间:</label>
          <input
            v-model="filters.end_date"
            type="datetime-local"
            class="usage-management__filter-input"
          />
        </div>
        <button class="usage-management__button usage-management__button--primary" @click="loadUsageData">
          查询
        </button>
      </div>

      <!-- 数据表格 -->
      <div class="usage-management__table-container">
        <table class="usage-management__table" v-if="usageList.length > 0">
          <thead>
            <tr>
              <th>记录ID</th>
              <th>电表ID</th>
              <th>电量读数 (kWh)</th>
              <th>电压 (V)</th>
              <th>电流 (A)</th>
              <th>采集时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="usage in usageList" :key="usage.usage_id">
              <td>{{ usage.usage_id }}</td>
              <td>{{ usage.meter_id }}</td>
              <td>{{ usage.electricity }}</td>
              <td>{{ usage.voltage || '-' }}</td>
              <td>{{ usage.current || '-' }}</td>
              <td>{{ usage.collect_time }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="usage-management__empty">
          暂无数据
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="usage-management__pagination">
        <button 
          class="usage-management__pagination-btn" 
          @click="changePage(pagination.page - 1)"
          :disabled="!pagination.has_prev"
        >
          上一页
        </button>
        <span class="usage-management__pagination-info">
          第 {{ pagination.page }} / {{ pagination.pages }} 页，共 {{ pagination.total }} 条
        </span>
        <button 
          class="usage-management__pagination-btn" 
          @click="changePage(pagination.page + 1)"
          :disabled="!pagination.has_next"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { manualInput, queryUsage } from '@/services/api/usage'
import { toast } from '@/utils/toast'

// 表单数据
const form = reactive({
  meter_id: null as number | null,
  electricity: null as number | null,
  collect_time: '',
  voltage: null as number | null,
  current: null as number | null
})

// 查询条件
const filters = reactive({
  meter_id: null as number | null,
  start_date: '',
  end_date: '',
  page: 1,
  per_page: 20
})

// 数据列表
const usageList = ref<any[]>([])
const submitting = ref(false)

// 分页信息
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 20,
  pages: 1,
  has_next: false,
  has_prev: false
})

// 重置表单
const resetForm = () => {
  form.meter_id = null
  form.electricity = null
  form.collect_time = ''
  form.voltage = null
  form.current = null
}

// 提交数据
const handleSubmit = async () => {
  // 验证必填字段
  if (!form.meter_id || !form.electricity || !form.collect_time) {
    toast.error('请填写所有必填字段')
    return
  }

  submitting.value = true
  try {
    const data: any = {
      meter_id: form.meter_id,
      electricity: form.electricity,
      collect_time: form.collect_time
    }

    if (form.voltage !== null) {
      data.voltage = form.voltage
    }
    if (form.current !== null) {
      data.current = form.current
    }

    const response = await manualInput(data)
    
    if (response.data.success) {
      toast.success('数据录入成功')
      resetForm()
      loadUsageData() // 刷新列表
    } else {
      toast.error(response.data.message || '数据录入失败')
    }
  } catch (error: any) {
    console.error('录入数据失败:', error)
    toast.error(error.response?.data?.message || '数据录入失败')
  } finally {
    submitting.value = false
  }
}

// 加载用电数据
const loadUsageData = async () => {
  try {
    const params: any = {
      page: filters.page,
      per_page: filters.per_page
    }

    if (filters.meter_id) {
      params.meter_id = filters.meter_id
    } else {
      // 如果没有指定电表ID，不自动加载数据
      usageList.value = []
      return
    }
    
    if (filters.start_date) {
      params.start_date = filters.start_date
    }
    if (filters.end_date) {
      params.end_date = filters.end_date
    }

    const response = await queryUsage(params)
    
    if (response.success) {
      usageList.value = response.data.usages || []
      
      if (response.data.pagination) {
        Object.assign(pagination, response.data.pagination)
      }
    } else {
      toast.error(response.message || '查询失败')
    }
  } catch (error: any) {
    console.error('加载数据失败:', error)
    toast.error(error.response?.data?.message || '查询失败')
  }
}

// 切换页码
const changePage = (page: number) => {
  filters.page = page
  loadUsageData()
}

// 初始化
onMounted(() => {
  // 不自动加载数据，等待用户输入电表ID后点击查询
})
</script>

<style scoped>
.usage-management {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.usage-management__title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 24px;
}

.usage-management__card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  padding: 24px;
}

.usage-management__card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.usage-management__card-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.usage-management__form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.usage-management__form-group {
  display: flex;
  flex-direction: column;
}

.usage-management__label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.usage-management__input {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.usage-management__input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.usage-management__form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.usage-management__button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.usage-management__button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.usage-management__button--primary {
  background: #3b82f6;
  color: white;
}

.usage-management__button--primary:hover:not(:disabled) {
  background: #2563eb;
}

.usage-management__button--secondary {
  background: #f3f4f6;
  color: #374151;
}

.usage-management__button--secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.usage-management__filters {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.usage-management__filter-group {
  display: flex;
  flex-direction: column;
  min-width: 200px;
}

.usage-management__filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.usage-management__filter-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
}

.usage-management__filter-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.usage-management__table-container {
  overflow-x: auto;
}

.usage-management__table {
  width: 100%;
  border-collapse: collapse;
}

.usage-management__table th,
.usage-management__table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.usage-management__table th {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  background: #f9fafb;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.usage-management__table td {
  font-size: 14px;
  color: #1f2937;
}

.usage-management__table tbody tr:hover {
  background: #f9fafb;
}

.usage-management__empty {
  text-align: center;
  padding: 48px 20px;
  color: #9ca3af;
  font-size: 14px;
}

.usage-management__pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.usage-management__pagination-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  color: #374151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.usage-management__pagination-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.usage-management__pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.usage-management__pagination-info {
  font-size: 14px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .usage-management {
    padding: 16px;
  }

  .usage-management__form-row {
    grid-template-columns: 1fr;
  }

  .usage-management__filters {
    flex-direction: column;
    align-items: stretch;
  }

  .usage-management__filter-group {
    min-width: auto;
  }
}
</style>
