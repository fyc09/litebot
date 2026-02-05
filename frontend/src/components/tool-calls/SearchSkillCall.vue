<template>
  <div class="search-skill-call">
    <t-collapse>
      <t-collapse-panel :value="1" destroy-on-close>
        <template #header>
          <div>
            <span>🔍 Search Skill</span>
            &nbsp;
            <code>{{ args.keyword }}</code>
            &nbsp;
            <t-tag
              v-if="result?.success === true"
              theme="success"
              variant="light"
              >Success</t-tag
            >
            <t-tag
              v-else-if="result?.success === false"
              theme="danger"
              variant="light"
              >Failed</t-tag
            >
            <t-tag v-else theme="warning" variant="light">Running</t-tag>
          </div>
        </template>
        <div class="content-area">
          <t-space direction="vertical">
            <template v-if="result">
              <div v-if="result.success">
                <div v-if="result.skills && result.skills.length > 0">
                  <t-space direction="vertical" size="small">
                    <div v-for="(skill, index) in result.skills" :key="index">
                      <t-card>
                        <template #header>
                          <div class="skill-header">
                            <span class="skill-title">{{ skill.title }}</span>
                            <t-tag variant="light">{{ skill.id }}</t-tag>
                          </div>
                        </template>
                        <div class="skill-description">{{ skill.description }}</div>
                      </t-card>
                    </div>
                  </t-space>
                </div>
                <div v-else>
                  <t-alert theme="info">No skills found matching "{{ args.keyword }}"</t-alert>
                </div>
              </div>
              <t-alert v-else theme="error">
                <pre>{{ result.error }}</pre>
              </t-alert>
            </template>
          </t-space>
        </div>
      </t-collapse-panel>
    </t-collapse>
  </div>
</template>

<script setup>
const props = defineProps({
  args: {
    type: Object,
    default: () => ({}),
  },
  result: {
    type: Object,
    default: null,
  },
});
</script>

<style scoped>
.content-area {
  max-height: var(--tool-call-max-height);
  overflow: auto;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-title {
  font-weight: 600;
}

.skill-description {
  margin-top: 8px;
  color: var(--text-color-secondary);
}
</style>