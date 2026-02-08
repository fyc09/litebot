<template>
  <t-chat-list :clear-history="false" class="messages-wrapper">
    <template v-for="message in messages" :key="message.id">
      <t-chat-message
        v-if="message.role === 'user'"
        :message="message"
        placement="right"
        variant="base"
      />
      <t-chat-message
        v-else-if="message.role === 'assistant'"
        :message="message"
        placement="left"
        variant="text"
      >
        <template #content>
          <div v-for="(item, idx) in message.content" :key="idx">
            <ToolCallMessage
              v-if="
                item.type === 'custom' &&
                item.data.componentType === 'tool-call'
              "
              :tool-data="item.data"
            />
            <t-chat-markdown
              v-else-if="item.type === 'markdown'"
              :content="item.data"
              :options="markdownOptions"
            />
            <div v-else>{{ item.data }}</div>
          </div>
        </template>
      </t-chat-message>
      <t-chat-message
        v-else
        :message="message"
        :placement="message.role === 'user' ? 'right' : 'left'"
        :variant="message.role === 'user' ? 'base' : 'text'"
      >
        <template #content>
          <div v-for="(item, idx) in message.content" :key="idx">
            <t-chat-markdown
              v-if="message.role === 'assistant' && item.type === 'markdown'"
              :content="item.data"
              :options="markdownOptions"
            />
            <div v-else>{{ item.data }}</div>
          </div>
        </template>
      </t-chat-message>
    </template>
  </t-chat-list>
</template>

<script setup>
import katex from "katex";
import "katex/dist/katex.min.css";
import ToolCallMessage from "./ToolCallMessage.vue";

// 将 katex 挂载到 window 对象上
window.katex = katex;

defineProps({
  messages: {
    type: Array,
    default: () => [],
  },
});

const markdownOptions = {
  themeSettings: {
    codeBlockTheme: "dark",
  },
  engine: {
    syntax: {
      mathBlock: {
        engine: "katex",
      },
      inlineMath: {
        engine: "katex",
      },
    },
  },
};
</script>

<style scoped lang="less">
.messages-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
</style>
