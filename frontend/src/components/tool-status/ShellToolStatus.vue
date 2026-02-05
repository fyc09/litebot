<template>
  <div class="execute-command-status">
    <div v-if="sessions.length > 0" class="sessions-container">
      <t-collapse v-model="expandedSessions" class="sessions-collapse">
        <t-collapse-panel
          v-for="session in sessions"
          :key="session.session_id"
          :value="session.session_id"
        >
          <template #header>
            <div class="session-title">
              <span
                >Session: <code>{{ session.session_id }}</code></span
              >
              <t-tag v-if="session.alive" theme="success" variant="light"
                >Running</t-tag
              >
              <t-tag v-else theme="default" variant="light">Stoped</t-tag>
            </div>
          </template>

          <div class="content-area">
            <t-space direction="vertical">
              <div v-if="session.working_dir">
                <span
                  >Working Directory:
                  <code>{{ session.working_dir }}</code></span
                >
              </div>
              <div>
                <span
                  >Process ID: <code>{{ session.pid || "N/A" }}</code></span
                >
              </div>
              <template v-if="session.log && session.log.length > 0">
                <div class="logs-list">
                  <pre class="log-entry">
                    <span v-for="(log, idx) in session.log" :key="idx" :class="logClass(log.stream)">{{ log.data }}</span>
                  </pre>
                </div>
              </template>
              <div v-else>
                <t-space>
                  <div>No logs</div>
                </t-space>
              </div>
            </t-space>
          </div>
        </t-collapse-panel>
      </t-collapse>
    </div>
    <div v-else>
      <t-alert
        title="No active sessions"
        description="There are no active shell sessions"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  status: {
    type: Object,
    default: () => ({}),
  },
});

const expandedSessions = ref([]);

const sessions = computed(() => {
  return props.status?.sessions || [];
});

function logClass(stream) {
  switch (stream) {
    case "stdout":
      return "stream-stdout";
    case "stderr":
      return "stream-stderr";
    case "stdin":
      return "stream-stdin";
    default:
      return "stream-default";
  }
}
</script>

<style scoped>
.session-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.content-area {
  max-height: var(--tool-status-max-height);
  overflow: auto;
}

.stream-stdout {
  color: #00a870;
}

.stream-stderr {
  color: #e34d59;
}

.stream-stdin {
  color: #0052d9;
}

.stream-default {
  color: #666;
}
</style>
