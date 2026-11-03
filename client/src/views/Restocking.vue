<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.subtitle') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="budget-row">
          <label class="budget-label" for="restocking-budget">{{ t('restocking.budget') }}</label>
          <output class="budget-value" for="restocking-budget">{{ formatMoney(budget, 0) }}</output>
        </div>
        <input
          id="restocking-budget"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          max="100000"
          step="500"
        />
        <div class="budget-scale">
          <span>{{ formatMoney(0, 0) }}</span>
          <span>{{ formatMoney(100000, 0) }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ lines.length }})</h3>
        </div>

        <div v-if="lines.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <template v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.item') }}</th>
                  <th>{{ t('restocking.table.trend') }}</th>
                  <th class="num">{{ t('restocking.table.quantity') }}</th>
                  <th class="num">{{ t('restocking.table.unitCost') }}</th>
                  <th class="num">{{ t('restocking.table.lineCost') }}</th>
                  <th class="num">{{ t('restocking.table.leadTime') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in lines" :key="line.sku">
                  <td><strong>{{ line.sku }}</strong></td>
                  <td>{{ translateProductName(line.name) }}</td>
                  <td>
                    <span :class="['badge', line.trend]">{{ t(`trends.${line.trend}`) }}</span>
                  </td>
                  <td class="num">{{ line.quantity.toLocaleString() }}</td>
                  <td class="num">{{ formatMoney(line.unitCost, 2) }}</td>
                  <td class="num"><strong>{{ formatMoney(line.lineCost, 2) }}</strong></td>
                  <td class="num">{{ t('restocking.days', { count: line.leadTime }) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="summary">
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.summary.total') }}</span>
              <span class="summary-value">{{ formatMoney(totalCost, 2) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.summary.remaining') }}</span>
              <span class="summary-value">{{ formatMoney(remainingBudget, 2) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.summary.orderLeadTime') }}</span>
              <span class="summary-value">{{ t('restocking.days', { count: orderLeadTime }) }}</span>
            </div>
          </div>
        </template>

        <div class="actions">
          <button
            type="button"
            class="btn-primary"
            :disabled="lines.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="submittedOrder" class="success" role="status">
          {{ t('restocking.success', { orderNumber: submittedOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
        <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])

    // Budget is always held in USD; it is only converted for display
    const budget = ref(25000)
    const submitting = ref(false)
    const submittedOrder = ref(null)
    const submitError = ref(null)

    const formatMoney = (amount, decimals) =>
      formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
        console.error('Load error:', err)
      } finally {
        loading.value = false
      }
    }

    // Greedy recommendation: take non-decreasing items with a positive demand gap,
    // largest gap first, and buy up to the gap while the budget allows. Items that
    // cannot afford even one unit are skipped so cheaper later items can still fit.
    // Assumption: the demand gap (forecasted - current) is the restock quantity.
    // Inventory is not joined because most forecast SKUs are not in inventory.
    // Money is tracked in integer cents to avoid floating-point drift against the budget.
    const lines = computed(() => {
      const candidates = forecasts.value
        .map(f => ({ f, gap: f.forecasted_demand - f.current_demand }))
        .filter(({ f, gap }) => f.trend !== 'decreasing' && gap > 0)
        .sort((a, b) => b.gap - a.gap)

      let remainingCents = Math.round(budget.value * 100)
      const result = []
      for (const { f, gap } of candidates) {
        const unitCents = Math.round(f.unit_cost * 100)
        if (unitCents <= 0) continue
        const quantity = Math.min(gap, Math.floor(remainingCents / unitCents))
        if (quantity <= 0) continue
        remainingCents -= quantity * unitCents
        result.push({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          quantity,
          unitCost: unitCents / 100,
          lineCost: (quantity * unitCents) / 100,
          leadTime: f.lead_time_days
        })
      }
      return result
    })

    const totalCost = computed(() =>
      lines.value.reduce((sum, l) => sum + Math.round(l.lineCost * 100), 0) / 100
    )
    const remainingBudget = computed(() => Math.round((budget.value - totalCost.value) * 100) / 100)
    const orderLeadTime = computed(() =>
      lines.value.reduce((max, l) => Math.max(max, l.leadTime), 0)
    )

    // A stale confirmation or error no longer describes the current selection
    watch(budget, () => {
      submittedOrder.value = null
      submitError.value = null
    })

    const placeOrder = async () => {
      if (lines.value.length === 0 || submitting.value) return
      submitting.value = true
      submittedOrder.value = null
      submitError.value = null
      try {
        submittedOrder.value = await api.createRestockingOrder({
          budget: budget.value,
          items: lines.value.map(l => ({ sku: l.sku, quantity: l.quantity }))
        })
      } catch (err) {
        submitError.value = err.response?.data?.detail || t('restocking.error')
        console.error('Order error:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      lines,
      totalCost,
      remainingBudget,
      orderLeadTime,
      submitting,
      submittedOrder,
      submitError,
      formatMoney,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.813rem;
  color: #64748b;
}

/* Range slider */
.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  transition: box-shadow 0.15s ease;
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.35);
}

.budget-slider:focus-visible::-moz-range-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.35);
}

th.num,
td.num {
  text-align: right;
  white-space: nowrap;
}

.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(180px, 100%), 1fr));
  gap: var(--space-4);
  margin-top: var(--space-6);
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.actions {
  margin-top: var(--space-6);
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: 1px solid #2563eb;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.35);
}

.btn-primary:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
}

.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}

.success a {
  color: #166534;
  font-weight: 600;
  margin-left: 0.5rem;
  text-decoration: underline;
}
</style>
