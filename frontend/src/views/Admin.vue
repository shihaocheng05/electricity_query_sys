<template>
  <div class="admin">
    <h1 class="admin__title">系统管理</h1>

    <!-- 价格政策管理 -->
    <div class="admin__card">
      <div class="admin__card-header">
        <h2 class="admin__card-title">价格政策管理</h2>
        <button class="admin__button admin__button--primary" @click="showPriceModal = true">
          ➕ 新建价格政策
        </button>
      </div>
      <div class="admin__table-container">
        <table class="admin__table">
          <thead>
            <tr>
              <th>政策ID</th>
              <th>政策名称</th>
              <th>价格类型</th>
              <th>基础单价</th>
              <th>片区</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="price in priceList" :key="price.policy_id">
              <td>{{ price.policy_id }}</td>
              <td>{{ price.policy_name }}</td>
              <td>{{ getPriceTypeLabel(price.price_type) }}</td>
              <td>¥{{ price.base_unit_price }}/kWh</td>
              <td>{{ price.region_name || '-' }}</td>
              <td>
                <span :class="['admin__status', price.is_active ? 'admin__status--active' : 'admin__status--inactive']">
                  {{ price.is_active ? '启用' : '停用' }}
                </span>
              </td>
              <td>{{ price.create_time }}</td>
              <td>
                <button class="admin__button admin__button--text" @click="editPrice(price)">编辑</button>
                <button class="admin__button admin__button--text admin__button--danger" @click="deletePrice(price.policy_id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="priceList.length === 0" class="admin__empty">
          暂无价格政策
        </div>
      </div>
    </div>

    <!-- 片区管理 -->
    <div class="admin__card">
      <div class="admin__card-header">
        <h2 class="admin__card-title">片区管理</h2>
        <button class="admin__button admin__button--primary" @click="showRegionModal = true">
          ➕ 新建片区
        </button>
      </div>
      <div class="admin__table-container">
        <table class="admin__table">
          <thead>
            <tr>
              <th>片区ID</th>
              <th>片区名称</th>
              <th>片区编码</th>
              <th>管理员</th>
              <th>上级片区</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="region in regionList" :key="region.region_id">
              <td>{{ region.region_id }}</td>
              <td>{{ region.region_name }}</td>
              <td>{{ region.region_code }}</td>
              <td>{{ region.manager_name || '未分配' }}</td>
              <td>{{ region.parent_name || '无' }}</td>
              <td>
                <button class="admin__button admin__button--text" @click="editRegion(region)">编辑</button>
                <button class="admin__button admin__button--text admin__button--danger" @click="deleteRegion(region.region_id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="regionList.length === 0" class="admin__empty">
          暂无片区数据
        </div>
      </div>
    </div>

    <!-- 价格政策模态框 -->
    <div v-if="showPriceModal" class="admin__modal" @click.self="closePriceModal">
      <div class="admin__modal-content">
        <div class="admin__modal-header">
          <h3>{{ priceForm.policy_id ? '编辑' : '新建' }}价格政策</h3>
          <button class="admin__modal-close" @click="closePriceModal">✕</button>
        </div>
        <div class="admin__modal-body">
          <div v-if="priceForm.policy_id" class="admin__warning-box">
            ⚠️ 注意：价格类型、所属片区、开始时间和规则设置创建后不可修改。如需修改这些内容，请删除后重新创建。
          </div>
          
          <div class="admin__form-item">
            <label>政策名称 <span class="admin__required">*</span></label>
            <input v-model="priceForm.policy_name" type="text" placeholder="如：居民阶梯电价" />
          </div>
          <div class="admin__form-item">
            <label>价格类型 <span class="admin__required">*</span></label>
            <select v-model="priceForm.price_type" class="admin__form-select" :disabled="!!priceForm.policy_id">
              <option value="">请选择价格类型</option>
              <option value="ladder">阶梯电价</option>
              <option value="time_share">分时电价</option>
              <option value="combined">混合电价</option>
            </select>
          </div>
          <div class="admin__form-item">
            <label>所属片区 <span class="admin__required">*</span></label>
            <select v-model.number="priceForm.region_id" class="admin__form-select" :disabled="!!priceForm.policy_id">
              <option :value="undefined">请选择片区</option>
              <option v-for="region in regionList" :key="region.region_id" :value="region.region_id">
                {{ region.region_name }}
              </option>
            </select>
          </div>
          <div class="admin__form-item">
            <label>基础单价（元/kWh）<span class="admin__required">*</span></label>
            <input v-model.number="priceForm.base_unit_price" type="number" step="0.01" placeholder="0.60" />
          </div>
          <div class="admin__form-item">
            <label>开始时间 <span class="admin__required">*</span></label>
            <input v-model="priceForm.start_time" type="datetime-local" :disabled="!!priceForm.policy_id" />
          </div>
          <div class="admin__form-item">
            <label>结束时间</label>
            <input v-model="priceForm.end_time" type="datetime-local" />
          </div>

          <!-- 阶梯电价规则 -->
          <div v-if="(priceForm.price_type === 'ladder' || priceForm.price_type === 'combined') && !priceForm.policy_id" class="admin__rules-section">
            <div class="admin__rules-header">
              <label>阶梯电价规则（简化配置）</label>
            </div>
            <div class="admin__form-item">
              <label>低阶梯最高电量（kWh）<span class="admin__required">*</span></label>
              <input v-model.number="ladderConfig.lowMax" type="number" min="0" step="1" placeholder="如：200" />
            </div>
            <div class="admin__form-item">
              <label>高阶梯最低电量（kWh）<span class="admin__required">*</span></label>
              <input v-model.number="ladderConfig.highMin" type="number" min="0" step="1" placeholder="如：400" />
            </div>
            <div class="admin__form-item">
              <label>低阶梯倍率</label>
              <input v-model.number="ladderConfig.lowRatio" type="number" step="0.1" placeholder="默认：1.0" />
            </div>
            <div class="admin__form-item">
              <label>中阶梯倍率</label>
              <input v-model.number="ladderConfig.middleRatio" type="number" step="0.1" placeholder="默认：1.5" />
            </div>
            <div class="admin__form-item">
              <label>高阶梯倍率</label>
              <input v-model.number="ladderConfig.highRatio" type="number" step="0.1" placeholder="默认：2.0" />
            </div>
            <p class="admin__hint">系统将自动生成三个阶梯：低阶梯(0-{{ ladderConfig.lowMax }})，中阶梯({{ ladderConfig.lowMax }}-{{ ladderConfig.highMin }})，高阶梯({{ ladderConfig.highMin }}-无穷)</p>
          </div>
          
          <!-- 编辑模式下显示现有规则 -->
          <div v-if="(priceForm.price_type === 'ladder' || priceForm.price_type === 'combined') && priceForm.policy_id && priceForm.ladder_rules" class="admin__rules-section admin__rules-readonly">
            <div class="admin__rules-header">
              <label>阶梯电价规则（仅查看）</label>
            </div>
            <div v-for="(rule, index) in priceForm.ladder_rules" :key="index" class="admin__rule-display">
              <span class="rule-label">{{ rule.ladder_level === 'low' ? '低阶梯' : rule.ladder_level === 'middle' ? '中阶梯' : '高阶梯' }}</span>: 
              {{ rule.min_electricity }}kWh - {{ rule.max_electricity || '∞' }}kWh (倍率: {{ rule.ratio }})
            </div>
          </div>

          <!-- 分时电价规则 -->
          <div v-if="(priceForm.price_type === 'time_share' || priceForm.price_type === 'combined') && !priceForm.policy_id" class="admin__rules-section">
            <div class="admin__rules-header">
              <label>分时电价规则（简化配置）</label>
            </div>
            <div class="admin__form-item">
              <label>第一分界点（小时）<span class="admin__required">*</span></label>
              <input v-model.number="timeShareConfig.firstBoundary" type="number" min="0" max="23" step="1" placeholder="如：8" />
            </div>
            <div class="admin__form-item">
              <label>第二分界点（小时）<span class="admin__required">*</span></label>
              <input v-model.number="timeShareConfig.secondBoundary" type="number" min="0" max="23" step="1" placeholder="如：22" />
            </div>
            <div class="admin__form-item">
              <label>谷时倍率</label>
              <input v-model.number="timeShareConfig.valleyRatio" type="number" step="0.1" placeholder="默认：0.5" />
            </div>
            <div class="admin__form-item">
              <label>平时倍率</label>
              <input v-model.number="timeShareConfig.flatRatio" type="number" step="0.1" placeholder="默认：1.0" />
            </div>
            <div class="admin__form-item">
              <label>峰时倍率</label>
              <input v-model.number="timeShareConfig.peakRatio" type="number" step="0.1" placeholder="默认：1.5" />
            </div>
            <p class="admin__hint">系统将自动生成三个时段：谷时(0-{{ timeShareConfig.firstBoundary }})，峰时({{ timeShareConfig.firstBoundary }}-{{ timeShareConfig.secondBoundary }})，平时({{ timeShareConfig.secondBoundary }}-24)</p>
          </div>
          
          <!-- 编辑模式下显示现有分时规则 -->
          <div v-if="(priceForm.price_type === 'time_share' || priceForm.price_type === 'combined') && priceForm.policy_id && priceForm.time_share_rules" class="admin__rules-section admin__rules-readonly">
            <div class="admin__rules-header">
              <label>分时电价规则（仅查看）</label>
            </div>
            <div v-for="(rule, index) in priceForm.time_share_rules" :key="index" class="admin__rule-display">
              <span class="rule-label">{{ rule.time_period === 'valley' ? '谷时' : rule.time_period === 'peak' ? '峰时' : '平时' }}</span>: 
              {{ rule.start_hour }}:00 - {{ rule.end_hour }}:00 (倍率: {{ rule.ratio }})
            </div>
          </div>

          <div class="admin__form-item">
            <label>
              <input v-model="priceForm.is_active" type="checkbox" />
              启用该价格政策
            </label>
          </div>
        </div>
        <div class="admin__modal-footer">
          <button class="admin__button" @click="closePriceModal">取消</button>
          <button class="admin__button admin__button--primary" @click="savePricePolicy">保存</button>
        </div>
      </div>
    </div>

    <!-- 片区模态框 -->
    <div v-if="showRegionModal" class="admin__modal" @click.self="closeRegionModal">
      <div class="admin__modal-content">
        <div class="admin__modal-header">
          <h3>{{ regionForm.region_id ? '编辑' : '新建' }}片区</h3>
          <button class="admin__modal-close" @click="closeRegionModal">✕</button>
        </div>
        <div class="admin__modal-body">
          <div class="admin__form-item">
            <label>片区名称 <span class="admin__required">*</span></label>
            <input v-model="regionForm.region_name" type="text" placeholder="如：嘉定区" />
          </div>
          <div class="admin__form-item">
            <label>片区编码 <span class="admin__required">*</span></label>
            <input v-model="regionForm.region_code" type="text" placeholder="如：JD001" />
          </div>
          <div class="admin__form-item">
            <label>片区描述</label>
            <textarea v-model="regionForm.description" rows="3" placeholder="片区详细描述信息"></textarea>
          </div>
        </div>
        <div class="admin__modal-footer">
          <button class="admin__button" @click="closeRegionModal">取消</button>
          <button class="admin__button admin__button--primary" @click="saveRegion">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { toast } from '@/utils/toast'
import { loading } from '@/utils/loading'
import systemApi from '@/services/api/system'

interface PricePolicy {
  policy_id?: number
  policy_name: string
  price_type: string
  base_unit_price: number
  region_id: number
  region_name?: string
  is_active: boolean
  start_time: string
  end_time?: string
  create_time?: string
  ladder_rules?: LadderRule[]
  time_share_rules?: TimeShareRule[]
}

interface LadderRule {
  ladder_level: string
  min_electricity: number
  max_electricity: number | null
  ratio: number
}

interface TimeShareRule {
  time_period: string
  start_hour: number
  end_hour: number
  ratio: number
}

// 简化的阶梯电价配置
interface LadderConfig {
  lowMax: number
  highMin: number
  lowRatio: number
  middleRatio: number
  highRatio: number
}

// 简化的分时电价配置
interface TimeShareConfig {
  firstBoundary: number
  secondBoundary: number
  valleyRatio: number
  flatRatio: number
  peakRatio: number
}

interface Region {
  region_id?: number
  region_name: string
  region_code: string
  parent_id?: number
  parent_name?: string
  manager_id?: number
  manager_name?: string
  description?: string
}

const priceList = ref<PricePolicy[]>([])
const regionList = ref<Region[]>([])

const showPriceModal = ref(false)
const showRegionModal = ref(false)

// 价格类型标签映射
const getPriceTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    'ladder': '阶梯电价',
    'time_share': '分时电价',
    'combined': '混合电价'
  }
  return typeMap[type] || type
}

const priceForm = ref<PricePolicy>({
  policy_name: '',
  price_type: '',
  base_unit_price: 0,
  region_id: 0,
  start_time: new Date().toISOString().slice(0, 16),
  is_active: true,
  ladder_rules: [],
  time_share_rules: []
})

const regionForm = ref<Region>({
  region_name: '',
  region_code: '',
  description: ''
})

// 简化的阶梯电价配置
const ladderConfig = ref<LadderConfig>({
  lowMax: 200,
  highMin: 400,
  lowRatio: 1.0,
  middleRatio: 1.5,
  highRatio: 2.0
})

// 简化的分时电价配置
const timeShareConfig = ref<TimeShareConfig>({
  firstBoundary: 8,
  secondBoundary: 22,
  valleyRatio: 0.5,
  flatRatio: 1.0,
  peakRatio: 1.5
})

// 加载价格政策列表
const loadPricePolicies = async () => {
  try {
    const response = await systemApi.getPricePolicies()
    if (response.data && response.data.policies) {
      priceList.value = response.data.policies
    }
  } catch (error) {
    console.error('加载价格政策失败:', error)
    toast.error('加载价格政策失败')
  }
}

// 加载片区列表
const loadRegions = async () => {
  try {
    const response = await systemApi.getRegions()
    if (response.data && response.data.regions) {
      regionList.value = response.data.regions
    }
  } catch (error) {
    console.error('加载片区列表失败:', error)
    toast.error('加载片区列表失败')
  }
}

// 根据简化配置生成阶梯规则
const generateLadderRules = (): LadderRule[] => {
  return [
    {
      ladder_level: 'low',
      min_electricity: 0,
      max_electricity: ladderConfig.value.lowMax,
      ratio: ladderConfig.value.lowRatio
    },
    {
      ladder_level: 'middle',
      min_electricity: ladderConfig.value.lowMax,
      max_electricity: ladderConfig.value.highMin,
      ratio: ladderConfig.value.middleRatio
    },
    {
      ladder_level: 'high',
      min_electricity: ladderConfig.value.highMin,
      max_electricity: null,
      ratio: ladderConfig.value.highRatio
    }
  ]
}

// 根据简化配置生成分时规则
const generateTimeShareRules = (): TimeShareRule[] => {
  return [
    {
      time_period: 'valley',
      start_hour: 0,
      end_hour: timeShareConfig.value.firstBoundary,
      ratio: timeShareConfig.value.valleyRatio
    },
    {
      time_period: 'peak',
      start_hour: timeShareConfig.value.firstBoundary,
      end_hour: timeShareConfig.value.secondBoundary,
      ratio: timeShareConfig.value.peakRatio
    },
    {
      time_period: 'flat',
      start_hour: timeShareConfig.value.secondBoundary,
      end_hour: 24,
      ratio: timeShareConfig.value.flatRatio
    }
  ]
}

// 验证阶梯配置
const validateLadderConfig = (): boolean => {
  if (!ladderConfig.value.lowMax || ladderConfig.value.lowMax <= 0) {
    toast.warning('请输入有效的低阶梯最高电量')
    return false
  }
  if (!ladderConfig.value.highMin || ladderConfig.value.highMin <= 0) {
    toast.warning('请输入有效的高阶梯最低电量')
    return false
  }
  if (ladderConfig.value.highMin <= ladderConfig.value.lowMax) {
    toast.error('高阶梯最低电量必须大于低阶梯最高电量')
    return false
  }
  return true
}

// 验证分时配置
const validateTimeShareConfig = (): boolean => {
  if (timeShareConfig.value.firstBoundary < 0 || timeShareConfig.value.firstBoundary > 23) {
    toast.warning('第一分界点必须在0-23小时之间')
    return false
  }
  if (timeShareConfig.value.secondBoundary < 0 || timeShareConfig.value.secondBoundary > 23) {
    toast.warning('第二分界点必须在0-23小时之间')
    return false
  }
  if (timeShareConfig.value.secondBoundary <= timeShareConfig.value.firstBoundary) {
    toast.error('第二分界点必须大于第一分界点')
    return false
  }
  return true
}

// 保存价格政策
const savePricePolicy = async () => {
  if (!priceForm.value.policy_name) {
    toast.warning('请输入政策名称')
    return
  }
  if (!priceForm.value.price_type) {
    toast.warning('请选择价格类型')
    return
  }
  if (!priceForm.value.region_id) {
    toast.warning('请选择所属片区')
    return
  }
  if (!priceForm.value.base_unit_price || priceForm.value.base_unit_price <= 0) {
    toast.warning('请输入有效的基础单价')
    return
  }
  if (!priceForm.value.start_time) {
    toast.warning('请选择开始时间')
    return
  }

  // 新建模式下验证阶梯电价配置
  if (!priceForm.value.policy_id && (priceForm.value.price_type === 'ladder' || priceForm.value.price_type === 'combined')) {
    if (!validateLadderConfig()) {
      return
    }
  }

  // 新建模式下验证分时电价配置
  if (!priceForm.value.policy_id && (priceForm.value.price_type === 'time_share' || priceForm.value.price_type === 'combined')) {
    if (!validateTimeShareConfig()) {
      return
    }
  }

  try {
    loading.show('保存中...')
    
    // 转换时间格式: datetime-local (YYYY-MM-DDTHH:mm) => YYYY-MM-DD HH:MM:SS
    const formatDateTime = (dateTimeLocal: string | undefined) => {
      if (!dateTimeLocal || dateTimeLocal.trim() === '') return undefined
      return dateTimeLocal.replace('T', ' ') + ':00'
    }
    
    if (priceForm.value.policy_id) {
      // 编辑模式：只更新允许修改的字段
      const payload: any = {
        policy_id: priceForm.value.policy_id,
        policy_name: priceForm.value.policy_name,
        base_unit_price: priceForm.value.base_unit_price,
        is_active: priceForm.value.is_active
      }
      
      // 只有当 end_time 有值时才添加到 payload
      const formattedEndTime = formatDateTime(priceForm.value.end_time)
      if (formattedEndTime !== undefined) {
        payload.end_time = formattedEndTime
      }
      
      console.log('准备更新价格政策，payload:', payload)
      await systemApi.updatePricePolicy(priceForm.value.policy_id, payload)
      toast.success('价格政策更新成功')
    } else {
      // 新建模式：包含所有字段和规则
      const ladder_rules = (priceForm.value.price_type === 'ladder' || priceForm.value.price_type === 'combined') 
        ? generateLadderRules() 
        : undefined
      
      const time_share_rules = (priceForm.value.price_type === 'time_share' || priceForm.value.price_type === 'combined')
        ? generateTimeShareRules()
        : undefined
      
      const payload = {
        ...priceForm.value,
        start_time: formatDateTime(priceForm.value.start_time),
        end_time: formatDateTime(priceForm.value.end_time),
        ladder_rules,
        time_share_rules
      }
      await systemApi.createPricePolicy(payload)
      toast.success('价格政策创建成功')
    }
    
    closePriceModal()
    loadPricePolicies()
  } catch (error: any) {
    console.error('保存价格政策失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '保存失败'
    toast.error(errorMsg)
  } finally {
    loading.hide()
  }
}

// 保存片区
const saveRegion = async () => {
  if (!regionForm.value.region_name) {
    toast.warning('请输入片区名称')
    return
  }
  if (!regionForm.value.region_code) {
    toast.warning('请输入片区编码')
    return
  }

  try {
    loading.show('保存中...')
    if (regionForm.value.region_id) {
      await systemApi.updateRegion(regionForm.value.region_id, regionForm.value)
      toast.success('片区更新成功')
    } else {
      await systemApi.createRegion(regionForm.value)
      toast.success('片区创建成功')
    }
    closeRegionModal()
    loadRegions()
  } catch (error: any) {
    toast.error(error.message || '保存失败')
  } finally {
    loading.hide()
  }
}

// 编辑价格政策
const editPrice = (price: PricePolicy) => {
  // 转换时间格式: "YYYY-MM-DD HH:MM:SS" => "YYYY-MM-DDTHH:mm"
  const convertToDateTimeLocal = (dateTimeStr: string | undefined) => {
    if (!dateTimeStr) return ''
    // 去掉秒数，将空格替换为T
    return dateTimeStr.slice(0, 16).replace(' ', 'T')
  }
  
  priceForm.value = {
    ...price,
    start_time: convertToDateTimeLocal(price.start_time),
    end_time: convertToDateTimeLocal(price.end_time)
  }
  
  console.log('编辑价格政策:', priceForm.value)
  
  // 如果有阶梯规则，解析出简化配置
  if (price.ladder_rules && price.ladder_rules.length > 0) {
    const lowRule = price.ladder_rules.find(r => r.ladder_level === 'low')
    const middleRule = price.ladder_rules.find(r => r.ladder_level === 'middle')
    const highRule = price.ladder_rules.find(r => r.ladder_level === 'high')
    
    if (lowRule && middleRule && highRule) {
      ladderConfig.value = {
        lowMax: lowRule.max_electricity || 200,
        highMin: highRule.min_electricity || 400,
        lowRatio: lowRule.ratio,
        middleRatio: middleRule.ratio,
        highRatio: highRule.ratio
      }
    }
  }
  
  // 如果有分时规则，解析出简化配置
  if (price.time_share_rules && price.time_share_rules.length > 0) {
    const valleyRule = price.time_share_rules.find(r => r.time_period === 'valley')
    const peakRule = price.time_share_rules.find(r => r.time_period === 'peak')
    const flatRule = price.time_share_rules.find(r => r.time_period === 'flat')
    
    if (valleyRule && peakRule && flatRule) {
      timeShareConfig.value = {
        firstBoundary: valleyRule.end_hour,
        secondBoundary: peakRule.end_hour,
        valleyRatio: valleyRule.ratio,
        flatRatio: flatRule.ratio,
        peakRatio: peakRule.ratio
      }
    }
  }
  
  showPriceModal.value = true
}

// 删除价格政策
const deletePrice = async (policyId: number) => {
  if (!confirm('确定要删除这个价格政策吗？')) {
    return
  }
  try {
    loading.show('删除中...')
    await systemApi.deletePricePolicy(policyId)
    toast.success('删除成功')
    loadPricePolicies()
  } catch (error: any) {
    toast.error(error.message || '删除失败')
  } finally {
    loading.hide()
  }
}

// 编辑片区
const editRegion = (region: Region) => {
  regionForm.value = { ...region }
  showRegionModal.value = true
}

// 删除片区
const deleteRegion = async (regionId: number) => {
  if (!confirm('确定要删除这个片区吗？此操作不可恢复！')) {
    return
  }
  try {
    loading.show('删除中...')
    await systemApi.deleteRegion(regionId)
    toast.success('删除成功')
    loadRegions()
  } catch (error: any) {
    toast.error(error.message || '删除失败')
  } finally {
    loading.hide()
  }
}

// 关闭模态框
const closePriceModal = () => {
  showPriceModal.value = false
  priceForm.value = {
    policy_name: '',
    price_type: '',
    base_unit_price: 0,
    region_id: 0,
    start_time: new Date().toISOString().slice(0, 16),
    is_active: true,
    ladder_rules: [],
    time_share_rules: []
  }
  // 重置简化配置
  ladderConfig.value = {
    lowMax: 200,
    highMin: 400,
    lowRatio: 1.0,
    middleRatio: 1.5,
    highRatio: 2.0
  }
  timeShareConfig.value = {
    firstBoundary: 8,
    secondBoundary: 22,
    valleyRatio: 0.5,
    flatRatio: 1.0,
    peakRatio: 1.5
  }
}

const closeRegionModal = () => {
  showRegionModal.value = false
  regionForm.value = {
    region_name: '',
    region_code: '',
    description: ''
  }
}

onMounted(() => {
  loadPricePolicies()
  loadRegions()
})
</script>

<style scoped>
.admin {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.admin__title {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-text);
}

.admin__card {
  background: var(--color-surface);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.admin__card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.admin__card-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
}

.admin__button {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.admin__button:hover {
  background: var(--color-hover);
}

.admin__button--primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.admin__button--primary:hover {
  opacity: 0.9;
}

.admin__button--text {
  border: none;
  background: transparent;
  color: var(--color-primary);
  padding: 4px 8px;
}

.admin__button--danger {
  color: #ef4444;
}

.admin__table-container {
  overflow-x: auto;
}

.admin__table {
  width: 100%;
  border-collapse: collapse;
}

.admin__table th,
.admin__table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.admin__table th {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.admin__table td {
  color: var(--color-text);
}

.admin__status {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.admin__status--active {
  background: #d1fae5;
  color: #065f46;
}

.admin__status--inactive {
  background: #fee2e2;
  color: #991b1b;
}

.admin__empty {
  padding: 40px;
  text-align: center;
  color: var(--color-text-secondary);
}

/* 模态框样式 */
.admin__modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.admin__modal-content {
  background: var(--color-surface);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.admin__modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.admin__modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.admin__modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.admin__modal-close:hover {
  background: var(--color-hover);
}

.admin__modal-body {
  padding: 24px;
  overflow-y: auto;
  max-height: calc(90vh - 140px);
}

.admin__modal-body::-webkit-scrollbar {
  width: 8px;
}

.admin__modal-body::-webkit-scrollbar-track {
  background: var(--color-hover);
  border-radius: 4px;
}

.admin__modal-body::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

.admin__modal-body::-webkit-scrollbar-thumb:hover {
  background: #999;
}

.admin__modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
}

.admin__form-item {
  margin-bottom: 20px;
}

.admin__form-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--color-text);
}

.admin__form-item input[type="text"],
.admin__form-item input[type="number"],
.admin__form-item input[type="datetime-local"],
.admin__form-item textarea,
.admin__form-item select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.admin__form-item input[type="checkbox"] {
  margin-right: 8px;
}

.admin__required {
  color: #ef4444;
}

/* 规则配置区域样式 */
.admin__rules-section {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--color-hover);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.admin__rules-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.admin__rules-header label {
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.admin__button--small {
  padding: 4px 12px;
  font-size: 13px;
}

.admin__rule-item {
  margin-bottom: 8px;
}

.admin__rule-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.admin__rule-input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 13px;
  box-sizing: border-box;
}

.admin__rule-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.admin__hint {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-left: 3px solid var(--color-primary);
  color: #0369a1;
  font-size: 13px;
  line-height: 1.5;
}

.admin__warning-box {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  color: #92400e;
  font-size: 14px;
  line-height: 1.6;
  border-radius: 4px;
}

.admin__rules-readonly {
  background: #f9fafb;
  border-color: #d1d5db;
}

.admin__rule-display {
  padding: 10px 12px;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--color-text);
}

.admin__rule-display .rule-label {
  font-weight: 600;
  color: var(--color-primary);
}

.admin__form-select:disabled,
.admin__form-item input:disabled {
  background: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}
</style>
