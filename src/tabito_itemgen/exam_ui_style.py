APP_CSS = """
<style>
:root {
  --ink: #202225;
  --muted: #71767b;
  --line: #dedfdf;
  --line-strong: #b9bdc0;
  --canvas: #f6f6f3;
  --paper: #ffffff;
  --sidebar: #f0f0ec;
  --ok: #35664d;
  --warn: #8a651f;
  --bad: #9a4242;
  --focus: #2d3945;
}

html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans",
               "Yu Gothic", "Noto Sans CJK JP", sans-serif;
}

.stApp {
  background: var(--canvas);
  color: var(--ink);
}

.block-container {
  max-width: 1180px;
  padding-top: 1.25rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: var(--sidebar);
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .block-container {
  padding-top: 1.15rem;
}

#MainMenu, footer {
  visibility: hidden;
}

header[data-testid="stHeader"] {
  background: transparent;
}

h1, h2, h3, h4 {
  color: var(--ink);
  letter-spacing: -0.012em;
}

h3 {
  margin-top: 1.25rem;
  font-size: 1.08rem;
}

h4 {
  font-size: .94rem;
}

.sidebar-brand {
  color: #74787c;
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .13em;
  margin-bottom: .12rem;
}

.sidebar-title {
  color: #222529;
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: .85rem;
}

.sidebar-rule {
  border-top: 1px solid var(--line);
  margin: 1rem 0 .75rem 0;
}

.workspace-heading {
  color: #17191b;
  font-size: 1.48rem;
  font-weight: 700;
  line-height: 1.3;
  margin: .08rem 0 .18rem 0;
}

.workspace-meta {
  color: var(--muted);
  font-size: .84rem;
  margin: 0 0 1.15rem 0;
}

.workspace-meta > span {
  color: #a0a4a7;
  padding: 0 .3rem;
}

.section-workspace-heading {
  color: #191b1e;
  font-size: 1.22rem;
  font-weight: 700;
  margin: .15rem 0 .18rem 0;
}

.section-workspace-meta {
  color: var(--muted);
  font-size: .84rem;
  margin-bottom: .9rem;
}

.status-label {
  display: inline;
  font-size: .82rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-label.muted { color: #6f7478; }
.status-label.ok { color: var(--ok); }
.status-label.warn { color: var(--warn); }
.status-label.bad { color: var(--bad); }

.workflow-list,
.release-list {
  margin: .25rem 0 1rem 0;
  border-top: 1px solid var(--line-strong);
}

.workflow-row {
  display: grid;
  grid-template-columns: .65fr 2.7fr 1.45fr 1.15fr;
  align-items: center;
  min-height: 3rem;
  border-bottom: 1px solid var(--line);
  gap: .7rem;
}

.workflow-code {
  font-weight: 700;
  color: #25282b;
}

.workflow-name {
  color: #25282b;
}

.workflow-score {
  color: var(--muted);
  font-size: .84rem;
}

.workflow-status {
  text-align: right;
}

.release-row {
  display: grid;
  grid-template-columns: 2.1rem 1fr 5rem;
  align-items: center;
  min-height: 2.7rem;
  border-bottom: 1px solid var(--line);
}

.release-mark,
.gate-mark {
  color: #8b9094;
  font-weight: 700;
}

.release-mark.ok,
.gate-mark.ok {
  color: var(--ok);
}

.release-name {
  color: #282b2e;
}

.release-state {
  color: var(--muted);
  font-size: .82rem;
  text-align: right;
}

.gate-row {
  display: grid;
  grid-template-columns: 2rem 1fr;
  align-items: center;
  min-height: 2.2rem;
  border-bottom: 1px solid #ececeb;
}

.next-action {
  display: grid;
  grid-template-columns: 4.7rem 1fr;
  gap: .7rem;
  align-items: start;
  border-left: 2px solid #66717b;
  padding: .48rem 0 .48rem .72rem;
  margin: .85rem 0 1.15rem 0;
  color: #2b2e31;
  line-height: 1.55;
}

.next-action b {
  font-size: .83rem;
}

.next-action span {
  font-size: .9rem;
}

/* Streamlit controls: quiet and editorial rather than dashboard-like. */
button[kind="primary"],
button[kind="secondary"],
button[kind="tertiary"] {
  border-radius: 3px !important;
  box-shadow: none !important;
  min-height: 2.25rem;
}

button[kind="primary"] {
  background: #26313b !important;
  border-color: #26313b !important;
}

[data-testid="stDownloadButton"] button {
  border-radius: 3px !important;
  box-shadow: none !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea {
  border-radius: 2px !important;
}

[data-baseweb="tab-list"] {
  gap: 1.35rem;
  border-bottom: 1px solid var(--line);
  margin-bottom: .55rem;
}

[data-baseweb="tab"] {
  padding-left: 0 !important;
  padding-right: 0 !important;
}

[data-baseweb="tab"][aria-selected="true"] {
  font-weight: 700;
}

[data-testid="stSidebar"] [role="radiogroup"] {
  gap: .12rem;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
  padding-top: .18rem;
  padding-bottom: .18rem;
}

div[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 2px !important;
  background: transparent !important;
  box-shadow: none !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent;
  border-color: var(--line) !important;
  border-radius: 2px !important;
  box-shadow: none !important;
}

[data-testid="stAlert"] {
  border-radius: 2px !important;
  box-shadow: none !important;
}

[data-testid="stCode"] {
  border-radius: 2px !important;
}

/* Exam surface: the preview should read like a paper, not an app card. */
.exam-header,
.exam-section,
.exam-intro,
.exam-question,
.exam-subq-label,
.exam-prompt,
.option-row,
.q1-word,
.q1-choice {
  font-family: Georgia, "Yu Mincho", "Hiragino Mincho ProN", serif;
  color: #111;
}

.exam-title {
  font-size: 1.18rem;
  line-height: 1.7;
}

.exam-rule {
  border-top: 1.15px solid #222;
  margin: .5rem 0 1rem 0;
}

.exam-section {
  font-size: 1.08rem;
  font-weight: 700;
  margin: 1.25rem 0 .28rem 0;
}

.exam-intro {
  line-height: 1.9;
  margin: .1rem 0 .72rem 0;
}

.exam-question {
  font-size: 1rem;
  font-weight: 700;
  margin: 1.05rem 0 .42rem 0;
}

.exam-subq-label {
  font-weight: 700;
  margin: .65rem 0 .12rem 0;
}

.exam-prompt {
  line-height: 1.9;
  margin: .55rem 0 .42rem 0;
}

.answer-badge {
  display: inline-block;
  min-width: 2.05rem;
  margin-left: .22rem;
  padding: .01rem .28rem;
  border: 1px solid #222;
  background: #fff;
  text-align: center;
  font-family: Georgia, serif;
  font-weight: 700;
}

.q1-word {
  margin: .45rem 0 .55rem 0;
  font-size: 1.02rem;
}

.q1-choice-row {
  display: flex;
  flex-wrap: wrap;
  gap: .55rem 2.2rem;
  margin: .15rem 0 .55rem 0;
}

.q1-choice {
  display: inline-block;
  min-width: 7rem;
  font-size: 1.02rem;
}

.source {
  margin: .65rem 0 .85rem 0;
  color: #111;
}

.source-title {
  font-family: Georgia, "Yu Mincho", "Hiragino Mincho ProN", serif;
  font-weight: 700;
  margin-bottom: .28rem;
}

.source-text {
  font-family: "Songti SC", "STSong", "Noto Serif CJK SC", "Yu Mincho", serif;
  font-size: .98rem;
  line-height: 1.92;
  white-space: normal;
}

.source-note {
  color: #686c70;
  font-size: .79rem;
  line-height: 1.6;
  margin-top: .28rem;
}

.glossary {
  margin-top: .38rem;
  padding-top: .3rem;
  border-top: 1px dotted #aaa;
  color: #555;
  font-size: .78rem;
}

.exam-table {
  width: 100%;
  border-collapse: collapse;
  margin: .55rem 0 .35rem 0;
  font-size: .9rem;
  background: #fff;
}

.exam-table th,
.exam-table td {
  border: 1px solid #777;
  padding: .42rem .5rem;
  text-align: center;
  vertical-align: middle;
}

.exam-table th {
  background: #f3f3f1;
  font-weight: 700;
}

.social-post {
  border-top: 1px solid #9d9d9d;
  border-bottom: 1px solid #9d9d9d;
  padding: .55rem .2rem;
  margin: .45rem 0;
  background: transparent;
}

.social-meta {
  font-size: .75rem;
  color: #666;
  margin-bottom: .24rem;
}

.option-list {
  margin: .25rem 0 .82rem 0;
}

.option-row {
  display: grid;
  grid-template-columns: 2rem minmax(0, 1fr);
  gap: .22rem;
  padding: .17rem 0;
  line-height: 1.72;
}

.option-mark {
  font-weight: 700;
}

.teacher-key {
  width: 100%;
  border-collapse: collapse;
  font-size: .9rem;
}

.teacher-key th,
.teacher-key td {
  border-bottom: 1px solid var(--line);
  padding: .42rem .5rem;
  text-align: left;
}

.teacher-key th {
  color: #666b70;
  font-size: .78rem;
  letter-spacing: .02em;
}

.small-muted,
.paper-note {
  color: var(--muted);
  font-size: .82rem;
}

@media (max-width: 800px) {
  .workflow-row {
    grid-template-columns: .55fr 2fr 1fr;
  }

  .workflow-score {
    display: none;
  }

  .next-action {
    grid-template-columns: 4rem 1fr;
  }
}
</style>
"""
