APP_CSS = """
<style>
:root {
  --ink: #1b1d20;
  --muted: #6e7378;
  --line: #dedfdf;
  --line-dark: #b8bbbd;
  --canvas: #f7f7f5;
  --paper: #ffffff;
  --ok: #35664d;
  --warn: #8b651f;
  --bad: #9b4141;
}

.stApp {
  background: var(--canvas);
  color: var(--ink);
}

.block-container {
  max-width: 1320px;
  padding-top: 1.35rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: #f2f2f0;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .block-container {
  padding-top: 1.15rem;
}

#MainMenu, footer { visibility: hidden; }

h1, h2, h3 {
  color: var(--ink);
  letter-spacing: -0.012em;
}

h2 { font-size: 1.28rem; }
h3 { font-size: 1rem; margin-top: 1.2rem; }

.sidebar-title {
  margin: 0 0 .65rem 0;
  font-size: .92rem;
  font-weight: 700;
  color: #2a2d30;
}

.workspace-heading {
  margin: .1rem 0 .18rem 0;
  font-size: 1.46rem;
  line-height: 1.3;
  font-weight: 680;
  color: #17191c;
}

.workspace-meta {
  color: var(--muted);
  font-size: .84rem;
  margin: 0 0 1rem 0;
}

.workspace-meta > span:not(.status-label) {
  padding: 0 .25rem;
  color: #a0a3a6;
}

.status-label {
  display: inline;
  padding: 0;
  border: 0;
  background: transparent;
  color: #555b60;
  font-size: .82rem;
  font-weight: 520;
  white-space: nowrap;
}
.status-label.ok { color: var(--ok); }
.status-label.warn { color: var(--warn); }
.status-label.bad { color: var(--bad); }

.gate-list .status-label {
  display: inline-block;
  min-width: 9rem;
  margin: .08rem .55rem .08rem 0;
}

/* Streamlit controls: quiet, utilitarian, no SaaS-card feel. */
button[kind="primary"], button[kind="secondary"] {
  border-radius: 3px !important;
  box-shadow: none !important;
}

[data-baseweb="tab-list"] {
  gap: 1.15rem;
  border-bottom: 1px solid var(--line);
}

[data-baseweb="tab"] {
  padding-left: 0 !important;
  padding-right: 0 !important;
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

/* Exam surface: typography first. */
.exam-header,
.exam-section,
.exam-intro,
.exam-question,
.exam-subq-label,
.exam-prompt,
.option-row,
.q1-word,
.q1-choice {
  font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif;
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
  font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif;
  font-weight: 700;
  margin-bottom: .28rem;
}

.source-text {
  font-family: 'Songti SC', 'STSong', 'Noto Serif CJK SC', 'Yu Mincho', serif;
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
.exam-table th, .exam-table td {
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

.option-list { margin: .25rem 0 .82rem 0; }
.option-row {
  display: grid;
  grid-template-columns: 2rem minmax(0,1fr);
  gap: .22rem;
  padding: .17rem 0;
  line-height: 1.72;
}
.option-mark { font-weight: 700; }

.teacher-key {
  width: 100%;
  border-collapse: collapse;
  font-size: .9rem;
}
.teacher-key th, .teacher-key td {
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
</style>
"""
