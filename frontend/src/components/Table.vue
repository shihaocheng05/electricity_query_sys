<template>
  <div class="table-container">
    <table class="table">
      <thead class="table__header">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="table__cell table__cell--header"
            :style="{ width: column.width }"
            @click="column.sortable && handleSort(column.key)"
          >
            <div class="table__cell-content">
              <span>{{ column.label }}</span>
              <span v-if="column.sortable" class="table__sort-icon">
                {{ getSortIcon(column.key) }}
              </span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="table__body">
        <tr
          v-for="(row, index) in paginatedData"
          :key="index"
          class="table__row"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            class="table__cell"
          >
            <slot
              :name="`cell-${column.key}`"
              :row="row"
              :value="row[column.key]"
            >
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
        <tr v-if="paginatedData.length === 0" class="table__empty">
          <td :colspan="columns.length" class="table__cell table__cell--empty">
            <div class="table__empty-content">
              <span class="table__empty-icon">📭</span>
              <p>暂无数据</p>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    
    <div v-if="pagination && data.length > 0" class="table__pagination">
      <div class="table__pagination-info">
        共 {{ total }} 条，第 {{ currentPage }} / {{ totalPages }} 页
      </div>
      <div class="table__pagination-buttons">
        <button
          class="table__pagination-button"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          上一页
        </button>
        <button
          v-for="page in pageNumbers"
          :key="page"
          class="table__pagination-button"
          :class="{ 'table__pagination-button--active': page === currentPage }"
          @click="handlePageChange(page)"
        >
          {{ page }}
        </button>
        <button
          class="table__pagination-button"
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          下一页
        </button>
      </div>
      <select
        v-model="currentPageSize"
        class="table__pagination-select"
        @change="handlePageSizeChange"
      >
        <option :value="10">10 条/页</option>
        <option :value="20">20 条/页</option>
        <option :value="50">50 条/页</option>
        <option :value="100">100 条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Column {
  key: string
  label: string
  width?: string
  sortable?: boolean
}

interface Props {
  columns: Column[]
  data: any[]
  pagination?: boolean
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  pagination: true,
  pageSize: 10
})

const emit = defineEmits<{
  pageChange: [page: number, pageSize: number]
}>()

const currentPage = ref(1)
const currentPageSize = ref(props.pageSize)
const sortKey = ref<string>('')
const sortOrder = ref<'asc' | 'desc'>('asc')

const sortedData = computed(() => {
  if (!sortKey.value) return props.data
  
  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    
    if (aVal === bVal) return 0
    
    const order = sortOrder.value === 'asc' ? 1 : -1
    return aVal > bVal ? order : -order
  })
})

const total = computed(() => props.data.length)
const totalPages = computed(() => Math.ceil(total.value / currentPageSize.value))

const paginatedData = computed(() => {
  if (!props.pagination) return sortedData.value
  
  const start = (currentPage.value - 1) * currentPageSize.value
  const end = start + currentPageSize.value
  return sortedData.value.slice(start, end)
})

const pageNumbers = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

const handleSort = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const getSortIcon = (key: string) => {
  if (sortKey.value !== key) return '⇅'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const handlePageChange = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  emit('pageChange', page, currentPageSize.value)
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  emit('pageChange', 1, currentPageSize.value)
}

// 重置分页当数据变化时
watch(() => props.data, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = 1
  }
})
</script>

<style scoped>
.table-container {
  width: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table__header {
  background-color: #f5f7fa;
  border-bottom: 2px solid var(--color-border);
}

.table__cell {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.table__cell--header {
  font-weight: 600;
  color: var(--color-text-primary);
  cursor: pointer;
  user-select: none;
}

.table__cell--empty {
  padding: 48px 16px;
  text-align: center;
}

.table__cell-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table__sort-icon {
  color: var(--color-text-tertiary);
  font-size: 12px;
}

.table__row {
  transition: background-color 0.2s;
}

.table__row:hover {
  background-color: var(--color-background-hover);
}

.table__empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.table__empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.table__empty-content p {
  margin: 0;
  color: var(--color-text-tertiary);
  font-size: 14px;
}

.table__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-top: 1px solid var(--color-border);
  background-color: #fafafa;
}

.table__pagination-info {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.table__pagination-buttons {
  display: flex;
  gap: 8px;
}

.table__pagination-button {
  min-width: 36px;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  background-color: white;
  color: var(--color-text-primary);
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.table__pagination-button:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.table__pagination-button--active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.table__pagination-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.table__pagination-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  background-color: white;
}

@media (max-width: 768px) {
  .table__pagination {
    flex-direction: column;
    gap: 12px;
  }
  
  .table__cell {
    padding: 8px 12px;
    font-size: 14px;
  }
}
</style>
