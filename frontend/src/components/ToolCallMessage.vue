<template>
  <div class="tool-call-message">
    <ShellStartCall
      v-if="toolData.funcName === 'shell_start'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ShellRunCall
      v-else-if="toolData.funcName === 'shell_run'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ShellWriteCall
      v-else-if="toolData.funcName === 'shell_write'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ShellReadCall
      v-else-if="toolData.funcName === 'shell_read'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ShellStopCall
      v-else-if="toolData.funcName === 'shell_stop'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ReadFileCall
      v-else-if="toolData.funcName === 'read_file'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <WriteFileCall
      v-else-if="toolData.funcName === 'write_file'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <ListDirectoryCall
      v-else-if="toolData.funcName === 'list_directory'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <UseSkillCall
      v-else-if="toolData.funcName === 'use_skill'"
      :args="toolData.args"
      :result="toolData.result"
      :success="toolData.success"
    />
    <div v-else class="unknown-tool">
      <p>Unknown tool: {{ toolData.funcName }}</p>
      <pre>{{ JSON.stringify(toolData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import ShellStartCall from "./tool-calls/ShellStartCall.vue";
import ShellRunCall from "./tool-calls/ShellRunCall.vue";
import ShellWriteCall from "./tool-calls/ShellWriteCall.vue";
import ShellReadCall from "./tool-calls/ShellReadCall.vue";
import ShellStopCall from "./tool-calls/ShellStopCall.vue";
import ReadFileCall from "./tool-calls/ReadFileCall.vue";
import WriteFileCall from "./tool-calls/WriteFileCall.vue";
import ListDirectoryCall from "./tool-calls/ListDirectoryCall.vue";
import UseSkillCall from "./tool-calls/UseSkillCall.vue";

defineProps({
  toolData: {
    type: Object,
    default: () => ({}),
  },
});
</script>

<style scoped lang="less">
.tool-call-message {
  margin: 8px 0;

  .unknown-tool {
    padding: 12px;
    background: var(--td-bg-color-container);
    border-radius: 4px;

    p {
      margin: 0 0 8px 0;
      color: var(--td-warning-color);
    }

    pre {
      margin: 0;
      padding: 8px;
      background: var(--td-bg-color-page);
      border-left: 2px solid var(--td-warning-color);
      max-height: 300px;
      overflow: auto;
      font-size: 12px;
    }
  }
}
</style>

