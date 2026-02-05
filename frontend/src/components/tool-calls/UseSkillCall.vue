<template>
  <div class="use-skill-call">
    <t-collapse>
      <t-collapse-panel :value="1" destroy-on-close>
        <template #header>
          <div>
            <span>📚 Use Skill</span>
            &nbsp;
            <code>{{ args.skill_id }}</code>
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
                <div class="skill-content">
                  <div class="skill-meta">
                    <t-tag variant="light" size="small">Skill ID: {{ result.skill_id }}</t-tag>
                    <t-tag variant="light" size="small" v-if="result.path">Path: {{ result.path }}</t-tag>
                  </div>
                  <div class="markdown-content" v-html="renderedContent"></div>
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
import { computed } from 'vue';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

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

const renderedContent = computed(() => {
  if (!props.result?.success || !props.result?.content) {
    return '';
  }

  // Configure marked
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  // Render markdown
  let html = marked(props.result.content);

  // Render KaTeX
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (match, math) => {
    try {
      return katex.renderToString(math, {
        throwOnError: false
      });
    } catch (e) {
      return match;
    }
  });

  return html;
});
</script>

<style scoped>
.content-area {
  max-height: var(--tool-call-max-height);
  overflow: auto;
}

.skill-content {
  margin-top: 8px;
}

.skill-meta {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
}

.markdown-content {
  line-height: 1.6;
}

.markdown-content :deep(h1) {
  font-size: 1.5rem;
  margin: 1rem 0;
}

.markdown-content :deep(h2) {
  font-size: 1.3rem;
  margin: 0.8rem 0;
}

.markdown-content :deep(h3) {
  font-size: 1.1rem;
  margin: 0.6rem 0;
}

.markdown-content :deep(code) {
  background: var(--token-tag-bg-color);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: var(--font-family-mono);
}

.markdown-content :deep(pre) {
  background: var(--token-tag-bg-color);
  padding: 1rem;
  border-radius: 6px;
  overflow: auto;
  margin: 1rem 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(li) {
  margin: 0.2rem 0;
}

.markdown-content :deep(p) {
  margin: 0.5rem 0;
}
</style>