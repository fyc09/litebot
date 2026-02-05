<template>
  <div class="skill-status">
    <div v-if="skills.length > 0" class="skills-container">
      <t-space direction="vertical" size="small">
        <div v-for="skill in skills" :key="skill.name" class="skill-item">
          <t-card>
            <template #header>
              <div class="skill-header">
                <span class="skill-name">{{ skill.name }}</span>
                <t-tag variant="light" theme="primary">{{ skill.version || 'v1.0.0' }}</t-tag>
              </div>
            </template>
            <div class="skill-content">
              <div class="skill-description">{{ skill.description }}</div>
              <div v-if="skill.author" class="skill-meta">
                <span class="meta-label">Author:</span>
                <span class="meta-value">{{ skill.author }}</span>
              </div>
              <div v-if="skill.tags && skill.tags.length > 0" class="skill-tags">
                <t-tag v-for="tag in skill.tags" :key="tag" size="small" variant="outline">{{ tag }}</t-tag>
              </div>
            </div>
          </t-card>
        </div>
      </t-space>
    </div>
    <div v-else>
      <t-alert
        title="No skills available"
        description="There are no skills currently loaded"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  status: {
    type: Object,
    default: () => ({}),
  },
});

const skills = computed(() => {
  return props.status?.skills || [];
});
</script>

<style scoped lang="less">
.skill-status {
  padding: 12px;
}

.skills-container {
  .skill-item {
    .skill-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .skill-name {
        font-weight: 600;
        font-size: 14px;
      }
    }

    .skill-content {
      .skill-description {
        margin-bottom: 8px;
        color: var(--td-text-color-secondary);
        font-size: 13px;
      }

      .skill-meta {
        margin-bottom: 4px;
        font-size: 12px;
        
        .meta-label {
          color: var(--td-text-color-placeholder);
          margin-right: 4px;
        }
        
        .meta-value {
          color: var(--td-text-color-secondary);
        }
      }

      .skill-tags {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
        margin-top: 8px;
      }
    }
  }
}
</style>
