#!/usr/bin/env python3
"""
Kaizan website build script.

Generates static HTML pages from shared templates + data dicts.
Run: `python tools/build.py` from the repo root.
Output: writes index.html, product/index.html, etc. into the current dir.

When you add a blog post, append to POSTS at the bottom of this file
and re-run the script. /blog/index.html (hidden) will pick it up.
"""

from __future__ import annotations
import os
from html import escape
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote


# ─────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]

# Top-nav. The "Blog" item points to /insights/ (matches the design canvas
# behaviour where the "Blog" nav target was the Insights page). The hidden
# /blog/ landing is NOT in the nav by design.
NAV = [
    ('Product',      'product/'),
    ('Integrations', 'integrations/'),
    # TODO: re-enable "Blog" once posts are ready.
    # ('Blog',         'insights/'),
    ('Pricing',      'pricing/'),
    # TODO: re-enable "Clients" nav item once the customer-stories content is ready.
    # ('Clients',      'customers/'),
    ('Security',     'security/'),
    ('FAQs',         'faq/'),
    ('About',        'about/'),
]

# Client-logo marquee. Each entry is a dict with name + filename in
# assets/img/clients/. Add or remove entries here to update the homepage
# marquee — the build picks them up automatically.
CLIENT_LOGOS = [
    dict(name='The Kite Factory',         file='the-kite-factory.svg'),
    dict(name='Searchlab',                file='searchlab.png'),
    dict(name='NP Digital',               file='np-digital.png'),
    dict(name='The Gap Partnership',      file='the-gap-partnership.svg'),
    dict(name='Scale Digital',            file='scale-digital.png'),
    dict(name='Tradedoubler',             file='tradedoubler.png'),
    dict(name='Open Partners',            file='open-partners.svg'),
    dict(name='Verkeer',                  file='verkeer.png'),
    dict(name='AMS',                      file='ams.png'),
    dict(name='Assembly Global',          file='assembly-global.svg'),
    dict(name='Click Through Marketing',  file='click-through-marketing.png'),
    dict(name='Collective Content',       file='collective-content.svg'),
    dict(name='Gifta',                    file='gifta.png'),
    dict(name='Gravity Global',           file='gravity-global.svg'),
    dict(name='Kohort',                   file='kohort.png'),
    dict(name='Marketing Architects',     file='marketing-architects.png'),
    dict(name='Medialab',                 file='medialab.png'),
    dict(name='PASHN Media Agency',       file='pashn-media-agency.svg'),
    dict(name='Viola',                    file='viola.png'),
    dict(name='Webtopia',                 file='webtopia.png'),
]
INTEGRATIONS = ['Salesforce', 'Gmail', 'Slack', 'Google Calendar',
                'Teams', 'Zoom', 'Outlook', 'Notion', 'Asana']

# Acme Creative — the dummy customer used in product mocks
ACME = dict(name='Acme Creative', arr='£1.2M ARR', health=87, delta='+12',
            csat=8.4, escalations='−30%')

# Customer pull-quotes (verbatim from the brief)
QUOTES = [
    dict(q='Kaizan provides a view of the real-time sentiment and service levels across our clients.',
         name='Mark Raymond', role='Co-founder', co='Anything Is Possible', tone='warm'),
    dict(q='Our clients expect us to innovate, and they’ve been excited about our use of Kaizan.',
         name='Gabriella Krite', role='Head of Operations', co='The Kite Factory', tone='sand'),
    dict(q='Kaizan improves our client interactions — the most valuable thing we have.',
         name='Samantha Bessant', role='Head of Client Success', co='Adimo', tone='blush'),
    dict(q='We’ve seen the sentiment of every client go up.',
         name='Hannah Carthy', role='MD', co='Verkeer', tone='olive'),
    dict(q='Kaizan is now fundamental to the team and managing client relationships.',
         name='Stephen Kerin', role='Director', co='Scale Digital', tone='gold'),
    dict(q='30% fewer client escalations since we rolled out Kaizan across the team.',
         name='Gravity Team', role='Client Services', co='Gravity Advertising', tone='clay'),
]

# Personas — one template, eight personas
PERSONAS = {
    'account-manager': dict(
        eyebrow='FOR · CLIENT SERVICE / ACCOUNT MANAGER',
        h1=('The hour you save every morning —', 'the save you used to miss.'),
        sub=("Running 10, 15, 20+ accounts means the signal is always somewhere — in an inbox, "
             "a Slack thread, a meeting recording. Kaizan reads everything overnight and tells "
             "you the three things to do before standup."),
        quote_bg='radial-gradient(circle at 35% 30%, #D8A056, #6E3E10)',
        quote_pull='I get to my Monday inbox already prioritised. The dread is gone.',
        quote_role='ACCOUNT MANAGER',
        pillars=[
            ('01', 'Morning briefing',
             'Three things to do before 10am: a stakeholder going quiet, an unanswered objection, '
             'an opportunity to expand. Generated overnight.'),
            ('02', 'Drafts in your voice',
             "First-draft replies, follow-ups, status emails — written in your tone, with the right "
             "people CC’d. One click to edit or send."),
            ('03', 'Quiet-contact radar',
             'Every stakeholder ranked by days-since-last-touch. Suggested re-intros for anyone '
             'going dark. Saves 4–6 hours a week.'),
        ],
        product_h2='A junior on every account — the kind that never forgets and never sleeps.',
        products=[
            ('Morning inbox',
             'Accounts prioritised by what changed overnight. Risks, replies-needed, opportunities. '
             'Three actions before standup.'),
            ('Reply drafter',
             'Long thread? Kaizan summarises and drafts the next message in your voice — with the '
             'right CCs and the right tone.'),
            ('Coverage radar',
             "Senior contacts going quiet, stakeholders you haven’t engaged in 30+ days, "
             "single-threaded risk highlighted in red."),
        ],
        quote_idx=0, quote_cta='Read the Verkeer case study →', quote_cta_href='customers/verkeer/',
        objections=[
            ('Will the AI sound like me?',
             'It learns your voice from your last 90 days of email. Drafts come back in your tone. '
             'Editable in one click.'),
            ('What if it sends something wrong?',
             "It doesn’t send anything until you hit go. Optional auto-send only for low-stakes "
             "templates you pre-approve."),
            ('Will my clients know an AI is involved?',
             "You decide. Most AMs don’t disclose draft assistance any more than they disclose "
             "Grammarly. Invisible to the client unless you choose otherwise."),
            ('How long to ramp?',
             "Day one: morning briefing. Week two: drafts in your voice. Week four: the six-hour-a-week "
             "saving most AMs report."),
        ],
        cta='Get your six hours back.',
    ),
    'client-service-director': dict(
        eyebrow='FOR · CLIENT SERVICE DIRECTOR',
        h1=('Every account, every AM,', 'one honest view.'),
        sub=("You run a team of account leads across a portfolio of clients. The CRM lags reality, "
             "the Friday status calls are theatre, and you only learn an account is wobbling when "
             "it’s already wobbling. Kaizan turns the whole portfolio into a live, scoreable, "
             "defensible view — so you can coach the team and steer the book before anything breaks."),
        quote_bg='radial-gradient(circle at 30% 30%, #B58A4F, #4A2A0E)',
        quote_pull='I can see which accounts need air cover this week, and which AMs need coaching — without sitting in a single status call.',
        quote_role='CLIENT SERVICE DIRECTOR',
        pillars=[
            ('01', 'Portfolio health, scored',
             "Every account in your team’s book ranked by CARE score, with the evidence "
             "underneath. Spot drift before the AM does."),
            ('02', 'Coverage and risk map',
             'Single-threaded accounts, dormant senior contacts, stalled expansion threads — '
             'surfaced for you and your AMs.'),
            ('03', 'Coaching, with receipts',
             'See which AMs are following up, which are drafting in their voice, which accounts '
             'are slipping. Coach with evidence, not gut feel.'),
        ],
        product_h2="The whole book of business, on one page — built from what your team is actually doing.",
        products=[
            ('Portfolio dashboard',
             "Every account in the team’s book, scored across CARE. Click any row for the "
             "conversations, contacts and signals underneath."),
            ('Risk and coverage',
             "Accounts where coverage has thinned, sentiment has shifted or expansion threads have "
             "gone cold — flagged before the QBR."),
            ('Team performance',
             "How each AM is using Kaizan, where they’re getting leverage, and where they need "
             "coaching. No micromanagement — just a clear view."),
        ],
        quote_idx=1, quote_cta='See how Jellyfish uses Kaizan →', quote_cta_href='customers/jellyfish/',
        objections=[
            ('Won’t my team feel surveilled?',
             "Kaizan measures account health, not keystrokes. AMs see the same view you see. "
             "They’d rather know what’s drifting than be ambushed."),
            ('How is this different from a CRM?',
             'Your CRM is a memory humans update. Kaizan updates itself from email, calls and '
             'meetings, then writes back so reports finally match reality.'),
            ('What about confidentiality across accounts?',
             'Workspaces are permissioned. AMs see their accounts; you see the portfolio; nothing '
             'leaves the org boundary.'),
            ('How fast does it ramp across a team?',
             'First useful portfolio view in week two. Coaching signals calibrated by month two. '
             'Most CSDs see retained-revenue lift in quarter two.'),
        ],
        cta='Run the book of business, not the inbox.',
    ),
    'leadership': dict(
        eyebrow='FOR · SENIOR LEADERSHIP / DIRECTOR',
        h1=('Stop discovering churn in the', 'QBR.'),
        sub=("You own the P&L. Right now your forward view is a CRM that lags reality and a Friday "
             "gut-check from your Heads. Kaizan turns the book of business into a live, scoreable, "
             "defensible forecast — months before the renewal call."),
        quote_bg='radial-gradient(circle at 30% 30%, #C99A66, #5A2E14)',
        quote_pull="I can see which clients will renew, which won’t, and why — before the executive review.",
        quote_role='MANAGING DIRECTOR',
        pillars=[
            ('01', 'NDR, live',
             'Net dollar retention by client, by team, by quarter. A forward-looking pipeline of '
             'risk and expansion, not a backwards number.'),
            ('02', 'Forecast you can defend',
             'Renewal probability with the evidence underneath: coverage, sentiment, recency, '
             'expansion signals. Not vibes.'),
            ('03', 'Time back, every Monday',
             'One executive briefing replacing five status calls. The leadership view of every '
             'senior account, in one page.'),
        ],
        product_h2="The forward view of the business — built from the team’s actual conversations.",
        products=[
            ('Executive briefing',
             'Monday morning: one page on revenue at risk, expansion in flight, and which Heads '
             'need air cover this week.'),
            ('Renewal forecast',
             'Probability-weighted ARR for the next 4 quarters. Click any account to see the '
             'evidence underneath the score.'),
            ('Board view',
             'Export-ready slides for the quarterly board pack: NDR, coverage, time-to-resolve, '
             'expansion pipeline.'),
        ],
        quote_idx=1, quote_cta='Read the Jellyfish case study →', quote_cta_href='customers/jellyfish/',
        objections=[
            ('Isn’t this what my CRM does?',
             'Your CRM is a memory humans update. Kaizan is a memory that updates itself — from '
             'email, calls, meetings — and writes back into the CRM so reports finally match reality.'),
            ('What if my Heads don’t want to be measured?',
             "Kaizan measures account health, not individual performance. Your Heads get the same "
             "view you get — they’d rather know what’s drifting than be ambushed in the QBR."),
            ('How accurate is the forecast?',
             'Calibrated quarterly against your actuals. Most customers see renewal-prediction '
             'accuracy above 90% by month four; we publish the curve.'),
            ('What does it cost in time to roll out?',
             'Two weeks to first briefing. No data migration, no team retraining.'),
        ],
        cta='See your book of business, scored.',
    ),
    'head-of-ai': dict(
        eyebrow='FOR · HEAD OF AI / CTO',
        h1=('An AI platform you', 'don’t have to build.'),
        sub=("You’ve been asked to put AI in front of every client-facing team — but the "
             "off-the-shelf options are demos, and building it yourself is a 12-month roadmap you "
             "can’t fund. Kaizan is the platform layer for client service AI: tenant-isolated, "
             "model-agnostic, MCP-native, and audit-ready out of the box."),
        quote_bg='radial-gradient(circle at 30% 30%, #5F7E94, #1A2D3D)',
        quote_pull='I evaluated build-vs-buy for nine months. Kaizan is a year of platform engineering I no longer have to do.',
        quote_role='CHIEF TECHNOLOGY OFFICER',
        pillars=[
            ('01', 'Tenant-isolated, model-agnostic',
             'Per-customer data isolation, BYO-LLM (Anthropic, OpenAI, Azure, Bedrock), private '
             'deployments available. Your data stays where you need it to stay.'),
            ('02', 'MCP-native, integration-first',
             'Native MCP server. First-class connectors for Salesforce, Microsoft 365, Google '
             'Workspace, Slack, Zoom, Asana, Monday, ClickUp. Webhooks and API for everything else.'),
            ('03', 'Audit, governance, evals',
             'Per-prompt audit trail, model-output evals, redaction policies, role-based access. '
             'SOC 2 Type II, ISO 27001, GDPR. Built for the questions InfoSec will ask.'),
        ],
        product_h2='The platform layer your team would have to build — already built.',
        products=[
            ('Kaizan API',
             'RESTful and MCP endpoints for every primitive: clients, conversations, signals, '
             'drafts, scores. Drop into your existing internal tools.'),
            ('Model routing',
             'Route by cost, latency, sensitivity or task class. Plug in your preferred frontier '
             'model; swap it out without rewriting prompts.'),
            ('Governance console',
             'Eval runs, prompt versions, redaction rules, access logs. Everything your security '
             'review will ask for, in one place.'),
        ],
        quote_idx=1, quote_cta='Read the engineering architecture →', quote_cta_href='insights/',
        objections=[
            ('How does this play with our existing AI stack?',
             'Side-by-side. Kaizan is a domain platform for client service; it sits on top of your '
             'model layer (Bedrock, Azure OpenAI, Anthropic) and feeds your data warehouse.'),
            ('Can we self-host or use a private VPC?',
             'Yes. SaaS, dedicated tenant, or private VPC deployment. Quarterly model updates; '
             'you control the rollout window.'),
            ('What about prompt injection and data leakage?',
             'Per-tenant retrieval boundaries, output classifiers, redaction-before-retrieval, '
             'full audit trail. We publish the threat model.'),
            ('How do you handle model deprecation?',
             'Model-agnostic by design. Prompts are versioned; evals run on every model swap; we '
             'hold a 30-day rollback window on every change.'),
        ],
        cta='The AI platform, without the build.',
    ),
    'project-manager': dict(
        eyebrow='FOR · PROJECT MANAGER',
        h1=('No more chasing.', 'No more surprises.'),
        sub=("Project delays trace back to two things: unclear scope and missed updates. Kaizan "
             "reads every conversation across the project, surfaces drift early, and drafts the "
             "status updates that used to take you a Friday afternoon."),
        quote_bg='radial-gradient(circle at 30% 30%, #6F8474, #1F3025)',
        quote_pull='Status updates write themselves. I spend Friday afternoons doing real PM work — not chasing inputs.',
        quote_role='SENIOR PROJECT MANAGER',
        pillars=[
            ('01', 'Scope drift detector',
             'When the conversation moves outside the SOW, Kaizan flags it — before it becomes a '
             'difficult invoice conversation.'),
            ('02', 'Status updates, drafted',
             "The weekly client status, written from what actually happened — pulled from Slack, "
             "email, meetings, Asana / Monday / ClickUp."),
            ('03', 'Risk register, live',
             "Open risks aren’t in a doc someone updates monthly. They’re in the "
             "conversations every day. Kaizan keeps the register honest."),
        ],
        product_h2="The PM’s leverage: less chasing, more steering.",
        products=[
            ('Status drafter',
             'Every Friday — or every Monday — a draft client update built from the week’s '
             'actual conversations, ready to edit.'),
            ('Scope sentinel',
             'Flag the moment client language drifts beyond the SOW. Optional auto-tag in the '
             'project tracker.'),
            ('Risk feed',
             'A live risk register fed from conversations across the team. No more "we should’ve '
             'seen that coming".'),
        ],
        quote_idx=0, quote_cta='Read the Verkeer case study →', quote_cta_href='customers/verkeer/',
        objections=[
            ('We use Asana / Monday / ClickUp — does this replace it?',
             'No. Kaizan reads from those tools and writes back into them. Status fields update themselves.'),
            ('Will it create busywork for the team?',
             'It removes the busywork — the chasing, the manual status drafting, the Friday '
             'afternoon catch-ups.'),
            ('How does it handle multi-agency projects?',
             'Account-level workspaces with permissioned views. Other agencies see what you decide they see.'),
            ('What if the client wants their own view?',
             'Optional client-share view. Filtered, branded, read-only.'),
        ],
        cta='Get Friday afternoons back.',
    ),
    'new-business': dict(
        eyebrow='FOR · NEW BUSINESS / SALES',
        h1=('Win more pitches with the same', 'pipeline.'),
        sub=("Tens of new-business conversations a year — chemistry meetings, briefings, "
             "capability decks, sales calls. Kaizan reads every prospect interaction and tells you "
             "what they’re really weighing, where the competition stands, and how to win the room."),
        quote_bg='radial-gradient(circle at 35% 30%, #8AAEAE, #1F4040)',
        quote_pull='We stopped sending generic decks. The shortlist hit-rate doubled inside one quarter.',
        quote_role='HEAD OF NEW BUSINESS',
        pillars=[
            ('01', 'What the prospect actually wants',
             "Beyond the brief: what came up in the chemistry meeting, what they didn’t say "
             "in the RFP, where the budget really sits."),
            ('02', 'Competitive intelligence',
             "Who else is on the shortlist, where you’re strong, where you’re behind. "
             "Pulled from what the prospect tells you."),
            ('03', 'Pitch decks that target the room',
             'Auto-draft the deck around the three things this specific prospect cares about — '
             'not the same template that worked twice last year.'),
        ],
        product_h2='Pitch from a position of knowing — not guessing.',
        products=[
            ('Prospect dossier',
             'Every chemistry meeting and call distilled into a one-page brief: priorities, '
             'language, decision criteria, internal politics.'),
            ('Shortlist intel',
             'When prospects mention competitors, you see it. Build the rebuttal slide before they '
             'ask the question.'),
            ('Pitch tailoring',
             "Pre-pitch checklist: have we addressed what they actually said matters? What’s "
             "missing from this deck?"),
        ],
        quote_idx=1, quote_cta='See how Jellyfish uses Kaizan →', quote_cta_href='customers/jellyfish/',
        objections=[
            ('Doesn’t every pitch feel unique?',
             "They feel unique. The patterns underneath aren’t. Kaizan finds the patterns — "
             "without making your decks generic."),
            ('What about confidential prospect data?',
             'Workspaces are isolated. Nothing crosses agencies. Each pitch has its own retention policy.'),
            ('How fast does this work?',
             'Most new-business teams see calibration after 8–10 pitches. Win-rate lift typically '
             'lands in quarter two.'),
            ('Can we use this in the room?',
             'Yes — sales-floor mode for live calls. Prompts surface as the conversation moves. '
             'Optional, never recording without consent.'),
        ],
        cta='Pitch from a position of knowing.',
    ),
    'performance': dict(
        eyebrow='FOR · PERFORMANCE / OPERATIONS',
        h1=('Run the operation on', 'the same source of truth.'),
        sub=("Performance and operations live or die on signal-to-noise. The dashboards say one "
             "thing; the client conversations say another; the team is firefighting in between. "
             "Kaizan reads every conversation, maps it to the metrics that matter, and turns "
             "operational chaos into a single live view."),
        quote_bg='radial-gradient(circle at 35% 30%, #708FAA, #1F3A50)',
        quote_pull='We were optimising for ROAS while the client cared about brand-search lift. Kaizan caught it in week one.',
        quote_role='HEAD OF PERFORMANCE',
        pillars=[
            ('01', 'The KPI behind the KPI',
             'What the client says they want vs what they actually grade you on. Surface the gap '
             'before the QBR.'),
            ('02', 'Operational early warning',
             'Picks up the moment a client questions delivery, attribution, or resourcing — before '
             'it becomes a renewal conversation.'),
            ('03', 'Reporting that lands',
             "Auto-draft the weekly update around the metrics this client cares about — not the "
             "dashboard’s defaults."),
        ],
        product_h2='Operational reporting that finally maps to what the client is actually thinking.',
        products=[
            ('Expectation map',
             'For every client, what they say they care about, ranked by how often they raise it '
             'in conversation. Update weekly.'),
            ('Drift alerts',
             "When the client’s language about success changes — different metrics, different "
             "timeframes, different competitors — you get the alert."),
            ('Auto-drafted weekly',
             'The Friday client update, drafted in your voice, around the metrics this client '
             'actually grades you on.'),
        ],
        quote_idx=1, quote_cta='See how Jellyfish uses Kaizan →', quote_cta_href='customers/jellyfish/',
        objections=[
            ('Does this replace our analytics platform?',
             "No. Kaizan reads conversations; your platform reads numbers. Together they tell you "
             "why the numbers don’t land."),
            ('What about confidentiality on operational data?',
             'Read-only access; nothing flows to third parties. Your spend and ops data stays where it is.'),
            ('Will it surface things I’d rather not flag?',
             'Yes. The whole point. Better you see it Monday than the client raises it at the QBR.'),
            ('How long until the alerts are useful?',
             'First useful alert typically inside 14 days; calibration sharpens through month two.'),
        ],
        cta='See what the client is really grading you on.',
    ),
    'strategy-creative-marketing': dict(
        eyebrow='FOR · STRATEGY, CREATIVE, MARKETING',
        h1=('The brief, the room,', 'and the case study — already there.'),
        sub=("Strategy, creative and marketing all run on the same scarce input: real client "
             "language. Kaizan reads every meeting, brief and conversation across your accounts "
             "and turns it into sharper strategy, tighter briefs, and case-study-grade quotes — "
             "without anyone re-typing a transcript."),
        quote_bg='radial-gradient(circle at 35% 30%, #B5A06D, #4A3D1A)',
        quote_pull='The decks are sharper, the briefs are tighter, and the marketing team finally has fuel that sounds like clients — because it is.',
        quote_role='CHIEF STRATEGY OFFICER',
        pillars=[
            ('01', 'Insight from the source',
             'Themes, language patterns and decision-driver shifts — extracted from every client '
             'conversation, not from your memory of them.'),
            ('02', 'Brief vs reality',
             'See where the brief diverges from what the client is actually saying in meetings. '
             'Stop solving the wrong problem in round one.'),
            ('03', 'Marketing fuel on tap',
             "Testimonial pull-quotes in your client’s words, category-level signal across "
             "the book, battlecards built from real objections."),
        ],
        product_h2='Strategy, creative and marketing — all running off the same live signal.',
        products=[
            ('Theme synthesis',
             "Cluster the language across 50+ meetings into the three themes that matter for next "
             "quarter’s strategy."),
            ('Brief enrichment',
             'Every brief auto-augmented with the last 30 days of client context: meetings, '
             'references, language patterns, hot buttons.'),
            ('Quote miner',
             'Every flattering thing a client said about working with you — surfaced, attributed, '
             'ready for sign-off and the next case study.'),
        ],
        quote_idx=2, quote_cta='Read the Adimo case study →', quote_cta_href='customers/adimo/',
        objections=[
            ('Doesn’t qualitative insight need a human?',
             'Yes — and Kaizan gives the human the raw material. Less time gathering, more time interpreting.'),
            ('Are the marketing quotes real or paraphrased?',
             'Real. Verbatim from client conversations, time-stamped and attributable. Nothing is '
             'published until your client signs off.'),
            ('What about confidentiality on competitor mentions?',
             'Cross-account patterns are surfaced anonymously by default. You see the signal, not '
             'the source — unless you have permission to dig in.'),
            ('Can we export to our research repo?',
             'Yes. CSV, Notion, Confluence, your data warehouse. The insight sits where your team '
             'already looks for it.'),
        ],
        cta='Sharper strategy. Tighter briefs. Better case studies.',
    ),
}

PERSONA_LIST = [
    ('account-manager',            'Client Service / Account Manager'),
    ('client-service-director',    'Client Service Director'),
    ('leadership',                 'Senior Leadership / Director'),
    ('head-of-ai',                 'Head of AI / CTO'),
    ('project-manager',            'Project Manager'),
    ('new-business',               'New Business / Sales'),
    ('performance',                'Performance / Operations'),
    ('strategy-creative-marketing','Strategy, Creative, Marketing'),
]

# Case studies — full detail pages
CASE_DATA = {
    'verkeer': dict(
        co='Verkeer', kind='Dutch agency · 40 people', tone='olive',
        headline='How Verkeer cut QBR prep from 6 hours to 40 minutes.',
        metric='2× QBR prep speed · 9.1 CSAT',
        quote='We cut account review prep from 6 hours to 40 minutes. The brief writes itself.',
        name='Hannah Carthy', role='MD',
        stats=[('83%','time saved on prep'), ('9.1','CSAT after 6 months'), ('28','accounts on Kaizan')],
        body=[
            ('Before Kaizan',
             "Quarterly business reviews were Hannah's least favourite part of the month. Each one "
             "meant pulling threads out of HubSpot, exporting Slack, scrubbing Gong calls, and "
             "writing a brief from scratch. The work was real but it was repeatable — which made "
             "it doubly painful."),
            ('What changed',
             "Kaizan's Insights agent now drafts the QBR brief automatically the week before each "
             "review. Health, sentiment, expansion signals and risk flags are all there in a "
             "single doc. Hannah edits — she doesn't write."),
            ('What it unlocked',
             "Verkeer's account managers spend the saved time on the conversations themselves. "
             "CSAT moved 1.4 points in two quarters. Three accounts that were quietly drifting got "
             "escalated and saved."),
        ],
    ),
    'the-kite-factory': dict(
        co='The Kite Factory', kind='Media agency · 120 people', tone='sand',
        headline='Three saves in one quarter that we would have missed.',
        metric='3 client saves · £480k retained',
        quote='Three client saves this quarter we would have missed without the Risk agent.',
        name='Gabriella Krite', role='Head of Operations',
        stats=[('3','at-risk saves in Q2'), ('£480k','revenue retained'), ('100%','AM adoption')],
        body=[
            ('The pattern',
             "Mid-tier accounts at TKF were churning quietly — sentiment dropped on calls a few "
             "weeks before any explicit signal. By the time the AM noticed, the client had already "
             "had the internal conversation."),
            ('What changed',
             "The Risk agent surfaces sentiment delta, response-time slippage and stakeholder "
             "change in a single weekly digest. Three accounts in Q2 were flagged early enough for "
             "the client partner to step in personally."),
            ('What it unlocked',
             "£480k of revenue retained that would otherwise have been a churn line item. More "
             "importantly, AMs trust the signal — adoption hit 100% within six weeks."),
        ],
    ),
    'adimo': dict(
        co='Adimo', kind='SaaS · 60 people', tone='blush',
        headline='CSAT moved before pipeline did. Then pipeline followed.',
        metric='+18pt CSAT · 1.4× expansion',
        quote='Our CSAT moved before our pipeline did — and then pipeline followed.',
        name='Samantha Bessant', role='Head of Client Success',
        stats=[('+18pt','CSAT in 2 quarters'), ('1.4×','expansion bookings'), ('12','agents using Kaizan')],
        body=[
            ('The hypothesis',
             "Sam believed that retention was a leading indicator of expansion. The data lived in "
             "five tools and nobody had time to assemble it."),
            ('What changed',
             "Kaizan's Health agent gave every CSM a single dashboard — engagement, sentiment, "
             "exec touch, expansion fit. Weekly digests went from “what happened” to "
             "“what to do”."),
            ('What it unlocked',
             "Eighteen points of CSAT in two quarters. Expansion bookings followed at 1.4× the "
             "previous run rate."),
        ],
    ),
    'jellyfish': dict(
        co='Jellyfish', kind='Global agency', tone='gold',
        headline='Standardised account health across 9 offices in a quarter.',
        metric='9 offices · 1 source of truth',
        quote='We standardised account health across 9 offices in a quarter.',
        name='Priya Shah', role='MD, EMEA',
        stats=[('9','offices live'), ('Q1 → Q2','rollout time'), ('1','source of truth')],
        body=[
            ('Before Kaizan',
             "Every Jellyfish region ran a slightly different account health framework. Comparing "
             "accounts globally was impossible; escalations got lost between time zones."),
            ('What changed',
             "Kaizan rolled out as the shared health layer. The Insights agent normalised signal "
             "across regions; the Risk agent gave global ops a single watchlist."),
            ('What it unlocked',
             "Priya's team can now answer “which accounts in EMEA need a partner conversation "
             "this week” in one minute, not one day."),
        ],
    ),
    'scale': dict(
        co='Scale Digital', kind='Consulting · 200 people', tone='warm',
        headline='Expansion signals that used to take weeks now hit the desk same day.',
        metric='2.1× upsell · same-day signal',
        quote='Expansion signals we used to miss now hit our desk the same day.',
        name='Stephen Kerin', role='Director',
        stats=[('2.1×','upsell vs prior year'), ('<24h','signal to action'), ('64','partners on platform')],
        body=[
            ('The problem',
             "Scale's partners knew expansion signals were buried in client conversations. The cost "
             "of mining them manually meant they almost never did."),
            ('What changed',
             "The Expansion agent watches every client thread for buying language, scope creep, "
             "and stakeholder shifts — flagging the partner the same day."),
            ('What it unlocked',
             "Upsell pipeline doubled year-on-year, and partners spend their selling time on real "
             "signals instead of cold check-ins."),
        ],
    ),
}

# Insights cards (the design's editorial blog) — content-light placeholders.
def cover(a, b, glyph):
    """Return a data:image SVG cover with a 2-stop gradient and a glyph."""
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 600 360'>"
        f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{a}'/><stop offset='1' stop-color='{b}'/>"
        f"</linearGradient></defs>"
        f"<rect width='600' height='360' fill='url(%23g)'/>"
        f"<text x='50%' y='54%' text-anchor='middle' font-family='Georgia, serif' "
        f"font-size='120' fill='rgba(10,10,10,0.85)' font-weight='400'>{glyph}</text>"
        f"</svg>"
    )
    return f"data:image/svg+xml;utf8,{svg}"

INSIGHTS_POSTS = [
    dict(cat='POV', t='What the top 10% of account managers do differently',
         d='Patterns we found across the highest-NPS teams — from briefing rituals to how they handle silence.',
         meta='9 min read', author='Glen Calvert', date='2 May 2026',
         img=cover('#FFB900', '#FFD86B', '01')),
    dict(cat='PRODUCT', t='Want to see Kaizan in action?',
         d='A 6-minute walk-through of the AI Assistant capturing a real client call and shipping the work behind it.',
         meta='6 min watch', author='Kaizan team', date='28 Apr 2026',
         img=cover('#0A0A0A', '#3A3A3A', '02')),
    dict(cat='WHITE PAPER', t='The 146% paradox',
         d='Why headline numbers hide risk — and the four leading indicators that actually predict the next year.',
         meta='18 min · gated', author='Pravin Paratey', date='21 Apr 2026',
         img=cover('#F1ECDD', '#E0D6BB', '03')),
    dict(cat='FIELD NOTES', t='The Monday briefing, decoded',
         d='What a good weekly client-health ritual looks like — from the firms running Kaizan in production.',
         meta='9 min read', author='Hannah Bowes', date='14 Apr 2026',
         img=cover('#D9E5DA', '#A8C4AE', '04')),
    dict(cat='INTERVIEW', t='A conversation with Waseem Ali',
         d='Why we call it Client Super Intelligence — and what changes when judgement becomes infrastructure.',
         meta='22 min listen', author='Glen Calvert', date='7 Apr 2026',
         img=cover('#FFB900', '#0A0A0A', '05')),
    dict(cat='BENCHMARK', t='The 2026 client-services benchmarks',
         d='Industry baselines for sentiment, coverage, account activity and engagement growth — with sources.',
         meta='12 min read', author='Kaizan Labs', date='30 Mar 2026',
         img=cover('#E8DFCB', '#FFB900', '06')),
]

# Hidden blog posts — start empty. Append new dicts here to publish.
# Schema:
#   slug  (URL-safe), title, excerpt, date, author, category, cover (img URL), body (HTML)
POSTS: list[dict] = [
    # Example (uncomment to test):
    # dict(slug='hello-world', title='Hello, world',
    #      excerpt='A short opener.', date='9 May 2026', author='Glen Calvert',
    #      category='POV', cover=cover('#FFB900', '#FFD86B', 'KZ'),
    #      body='<p>First post.</p>'),
]


# ─────────────────────────────────────────────────────────────────────
# RENDER HELPERS
# ─────────────────────────────────────────────────────────────────────

def E(s):
    """HTML-escape a string."""
    return escape(str(s), quote=True)


def relpath(depth: int) -> str:
    """Return ../../../ chain for a page nested N folders deep."""
    return '../' * depth


def asset_v(rel: str) -> str:
    """Cache-busting query string based on the asset's mtime.

    Returns "?v=<int>" if the file exists, or "" otherwise. Appended to CSS
    and JS hrefs so a fresh build invalidates browser caches automatically.
    """
    f = ROOT / rel
    try:
        return f'?v={int(f.stat().st_mtime)}'
    except OSError:
        return ''


def page_head(title: str, depth: int, description: str = '') -> str:
    p = relpath(depth)
    desc = description or 'Kaizan — client super intelligence for professional services firms.'
    # Cache-busting query strings deliberately disabled — easier on the CDN.
    # If you need to force a refresh after deploying CSS/JS, set these to
    # asset_v('assets/css/tokens.css') etc.
    tokens_v = ''
    site_css_v = ''
    site_js_v = ''
    return dedent(f'''\
        <!doctype html>
        <html lang="en">
        <head>
        <!-- Google Tag Manager -->
        <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
        new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        }})(window,document,'script','dataLayer','GTM-PNFJD9DV');</script>
        <!-- End Google Tag Manager -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{E(title)} · Kaizan</title>
        <meta name="description" content="{E(desc)}">
        <link rel="icon" type="image/png" sizes="32x32" href="{p}assets/img/favicon-32x32.png">
        <link rel="icon" type="image/webp" sizes="16x16" href="{p}assets/img/favicon-16x16.webp">
        <link rel="apple-touch-icon" sizes="180x180" href="{p}assets/img/apple-touch-icon.png">
        <link rel="mask-icon" href="{p}assets/img/safari-pinned-tab.svg" color="#FFB900">
        <link rel="stylesheet" href="{p}assets/css/tokens.css{tokens_v}">
        <link rel="stylesheet" href="{p}assets/css/site.css{site_css_v}">
        <script defer src="{p}assets/js/site.js{site_js_v}"></script>
        </head>
        <body>
        <!-- Google Tag Manager (noscript) -->
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PNFJD9DV"
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        <!-- End Google Tag Manager (noscript) -->
        <div class="kz-page">
        <main class="kz-main">
        ''')


def page_foot() -> str:
    return '</main>\n</div>\n</body>\n</html>\n'


def nav_html(depth: int, active: str | None = None, with_mega: bool = True) -> str:
    p = relpath(depth)
    items_html = []
    for label, target in NAV:
        href = p + target
        cls = ' class="is-active"' if active == label else ''
        if label == 'Product' and with_mega:
            # Product mega-menu is disabled until sub-pages exist. The "Product"
            # link is just a plain link to /product/ for now. To re-enable the
            # dropdown later, restore the mega-menu block below (currently in
            # the triple-quoted comment) and remove this simple anchor branch.
            items_html.append(f'<a href="{E(href)}"{cls}>{E(label)}</a>')
            _PRODUCT_MEGA_DISABLED = '''
              <span class="kz-mega-wrap" data-mega-menu style="position:relative;display:inline-block;">
                <a href="{E(href)}"{cls} class="kz-mega-trigger" aria-expanded="false">
                  Product <span class="kz-mega-caret">▾</span>
                </a>
                <div class="kz-mega-panel" role="menu">
                  <div>
                    <a href="{p}product/" class="kz-mega-cta-row">Explore the Kaizan platform <span class="arrow">↗</span></a>
                    <div class="kz-mega-cols">
                      <div>
                        <div class="kz-mega-label">Applications</div>
                        <a class="kz-mega-link" href="{p}product/#client-overview"><span class="glyph is-yellow">K</span>Client overview</a>
                        <a class="kz-mega-link" href="{p}product/#care"><span class="glyph is-yellow">K</span>CARE</a>
                        <a class="kz-mega-link" href="{p}product/#chatbot"><span class="glyph is-yellow">K</span>Chatbot</a>
                        <a class="kz-mega-link" href="{p}product/#client-360"><span class="glyph is-yellow">K</span>Client 360</a>
                      </div>
                      <div>
                        <div class="kz-mega-label">Foundation</div>
                        <a class="kz-mega-link" href="{p}integrations/"><span class="glyph is-mute">•</span>Integrations</a>
                        <a class="kz-mega-link" href="{p}security/"><span class="glyph is-mute">•</span>Trust &amp; Security</a>
                        <a class="kz-mega-link" href="{p}insights/"><span class="glyph is-mute">•</span>Insights &amp; research</a>
                        <div class="kz-mega-label" style="margin-top:18px;">Partners</div>
                        <a class="kz-mega-link" href="{p}customers/"><span class="glyph is-mute">•</span>Customer stories</a>
                      </div>
                    </div>
                  </div>
                  <aside class="kz-mega-side">
                    <div>
                      <h4>Take a self-guided tour</h4>
                      <a href="{p}product/">Start tour now →</a>
                    </div>
                    <div class="kz-mega-mini">
                      <div class="kz-mega-mini-head"><span>CARE · Acme Creative</span><span class="v">87 ↑</span></div>
                      <div class="kz-mega-mini-row"><span>Coverage</span><span class="v">9/12</span></div>
                      <div class="kz-mega-mini-row"><span>Activity</span><span class="v">+24%</span></div>
                      <div class="kz-mega-mini-row"><span>Relationship</span><span class="v">warm</span></div>
                      <div class="kz-mega-mini-row"><span>Expansion</span><span class="v">£82k</span></div>
                    </div>
                  </aside>
                </div>
              </span>'''
        else:
            items_html.append(f'<a href="{E(href)}"{cls}>{E(label)}</a>')

    return f'''<header class="kz-nav" role="banner">
      <a class="kz-nav-logo" href="{p}index.html">
        <img class="icon" src="{p}assets/img/kaizan-icon.png" alt="">
        <img class="word" src="{p}assets/img/kaizan-logo.png" alt="Kaizan">
      </a>
      <nav class="kz-nav-links" aria-label="Primary">
        {''.join(items_html)}
      </nav>
      <div class="kz-nav-cta">
        <a class="kz-btn kz-btn-ghost" href="https://app.kaizan.ai/">Client log in</a>
        <a class="kz-btn kz-btn-yellow" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
        <button class="kz-nav-toggle" aria-label="Open menu" type="button"><span class="bar"></span></button>
      </div>
    </header>
    '''


def footer_html(depth: int) -> str:
    p = relpath(depth)
    cols = [
        ('Product', [('Overview', f'{p}product/'),
                     # TODO: re-enable "Sandbox" once the sandbox experience is ready.
                     # ('Sandbox', f'{p}product/'),
                     ('Integrations', f'{p}integrations/'), ('Security', f'{p}security/')]),
        # TODO: re-enable the "For" column once persona pages are ready.
        # ('For', [('Account Manager', f'{p}for/account-manager/'),
        #          ('Project Manager', f'{p}for/project-manager/'),
        #          ('Leadership', f'{p}for/leadership/'),
        #          ('New Business', f'{p}for/new-business/')]),
        ('Company', [('About', f'{p}about/'),
                     # TODO: re-enable "Careers", "Insights", "Clients" once that content is ready.
                     # ('Careers', f'{p}careers/'),
                     ('Security', f'{p}security/'),
                     # ('Insights', f'{p}insights/'),
                     # ('Clients', f'{p}customers/'),
                     ('FAQ', f'{p}faq/')]),
        ('Get in touch', [('Book a demo', 'https://calendar.app.google/V9mCxVimwFr2ynSQ7'), ('Contact', 'mailto:hello@kaizan.ai'),
                          ('LinkedIn', 'https://www.linkedin.com/company/kaizan')]),
    ]
    cols_html = []
    for title, links in cols:
        anchors = '\n'.join(f'<a href="{E(href)}">{E(label)}</a>' for label, href in links)
        cols_html.append(f'<div class="col"><h4>{E(title)}</h4>{anchors}</div>')

    return f'''<footer class="kz-footer">
      <div class="kz-footer-grid">
        <div class="kz-footer-brand logo-light">
          <a class="kz-nav-logo" href="{p}index.html">
            <img class="icon" src="{p}assets/img/kaizan-icon.png" alt="">
            <img class="word" src="{p}assets/img/kaizan-logo.png" alt="Kaizan">
          </a>
          <p class="blurb">Client super intelligence for professional services firms. Runway East, Covent Garden · London.</p>
        </div>
        {''.join(cols_html)}
      </div>
      <div class="kz-footer-bot">
        <span>© 2026 Kaizan Labs Ltd. Series A announced 6 May 2026.</span>
        <span>
          <a href="https://help.kaizan.ai/en/articles/6028739-privacy-policy">Privacy</a> ·
          <a href="https://help.kaizan.ai/en/articles/6045324-license-agreement">Terms</a> ·
          <a href="https://help.kaizan.ai/en/articles/6014333-cookie-policy">Cookies</a>
        </span>
      </div>
    </footer>'''


def marquee_html(items, depth: int = 0):
    """Render the scrolling logo wall.

    Items may be:
      • a plain string  → rendered as text
      • a dict with `file` key → rendered as <img> from assets/img/clients/
      • a dict with only `name` → rendered as text fallback
    Triple-runs the list so the CSS marquee animation loops seamlessly.
    """
    p = relpath(depth)

    def render_one(x):
        if isinstance(x, str):
            return f'<span class="kz-marquee-text">{E(x)}</span>'
        name = x.get('name', '')
        if 'file' in x and x['file']:
            src = f'{p}assets/img/clients/{x["file"]}'
            return (f'<span class="kz-marquee-logo">'
                    f'<img src="{E(src)}" alt="{E(name)}" loading="lazy">'
                    f'</span>')
        return f'<span class="kz-marquee-text">{E(name)}</span>'

    one_run = ''.join(
        f'<span class="kz-marquee-item">{render_one(x)}<span class="sep">✺</span></span>'
        for x in items
    )
    return f'''<div class="kz-marquee" aria-hidden="true">
      <div class="kz-marquee-track">{one_run}{one_run}{one_run}</div>
    </div>'''


# Real headshots, keyed by full name. Drop a file in assets/img/people/
# and add an entry here to swap the gradient-initials avatar for a photo.
PEOPLE_PHOTOS = {
    'Mark Raymond':      'mark-raymond.png',
    'Gabriella Krite':   'gabriella-krite.png',
    'Hannah Carthy':     'hannah-carthy.png',
    'Samantha Bessant':  'samantha-bessant.png',
    'Stephen Kerin':     'stephen-kerin.png',
}


def portrait(name, role, co=None, tone='warm', size='', layout='', depth=0):
    initials = ''.join(p[0] for p in name.split()[:2]).upper()
    cls = ['kz-portrait', f'tone-{tone}']
    if size: cls.append(f'size-{size}')
    if layout: cls.append(f'layout-{layout}')
    role_text = role if not co else f'{role}, {co}'
    photo = PEOPLE_PHOTOS.get(name)
    if photo:
        cls.append('has-photo')
        src = f'{relpath(depth)}assets/img/people/{photo}'
        avatar_inner = f'<img src="{E(src)}" alt="{E(name)}" loading="lazy">'
    else:
        avatar_inner = E(initials)
    return f'''<div class="{' '.join(cls)}">
      <div class="avatar">{avatar_inner}</div>
      <div class="meta">
        <div class="name">{E(name)}</div>
        <div class="role">{E(role_text)}</div>
      </div>
    </div>'''


def _mock_chrome(url: str, label: str = 'DEMO · fictional data') -> str:
    """Browser-style chrome (red/yellow/green dots + url + demo tag)."""
    return f'''<div class="kz-product-tb">
        <div class="dot" style="background:#FF5F57;"></div>
        <div class="dot" style="background:#FEBC2E;"></div>
        <div class="dot" style="background:#28C840;"></div>
        <div class="url">{E(url)}</div>
        <div class="demo">{E(label)}</div>
      </div>'''


def scene_assistant() -> str:
    """Scene 01 — single workspace / client list."""
    # name, tier, comms, care, trend, ai_total, ai_auto, ai_pending, active
    rows = [
        ('Acme Creative',     'Annual',     32, '7.6', '+0.4',  18, 12, 6, True),
        ('Northwind',         'Gold',       14, '6.2', '−0.3',   9,  6, 3, False),
        ('Stark Industries',  'Annual',     28, '8.1', '+0.5',  15, 14, 1, False),
        ('Hooli',             'Annual',     21, '7.4', '+1.0',  11,  8, 3, False),
        ('Wayne Media',       'Independent', 7, '5.9', 'flat',   4,  4, 0, False),
        ('Pied Piper',        'Bronze',     18, '7.0', '+0.2',   8,  5, 3, False),
    ]
    initials_palette = ['warm','sand','olive','blush','slate','gold']

    def trend_class(t):
        if t.startswith('+'): return 'up'
        if t.startswith('−'): return 'down'
        return 'flat'

    rows_html = '\n'.join(
        f'''<div class="kz-mock-row{" is-active" if active else ""}">
          <div class="kz-mock-row-name">
            <span class="kz-mock-avatar tone-{initials_palette[i % len(initials_palette)]}">
              {E("".join(p[0] for p in name.split()[:2]))}
            </span>
            <span>{E(name)}</span>
          </div>
          <span class="kz-mock-pill">{E(tier)}</span>
          <span class="kz-mock-num">{comms}</span>
          <span class="kz-mock-care-cell">
            <span class="kz-mock-num">{E(care)}</span>
            <span class="kz-mock-trend {trend_class(trend)}">{E(trend)}</span>
          </span>
          <span class="kz-mock-actions">
            <span class="kz-mock-actions-total">{ai_total}</span>
            <span class="kz-mock-actions-split">
              <span class="auto">✓ {ai_auto}</span>
              <span class="pending">⏳ {ai_pending}</span>
            </span>
          </span>
        </div>''' for i, (name, tier, comms, care, trend, ai_total, ai_auto, ai_pending, active) in enumerate(rows)
    )
    return f'''<div class="kz-mock kz-mock-assistant">
      {_mock_chrome('app.kaizan.ai / dashboard / my-clients')}
      <div class="kz-mock-body">
        <div class="kz-mock-titlebar">
          <h4>My Clients</h4>
          <div class="kz-mock-tabs"><span class="is-active">My Clients</span><span>All Clients</span></div>
        </div>
        <div class="kz-mock-tablehead">
          <span>Client</span>
          <span>Tier</span>
          <span class="r">Comms</span>
          <span class="r">CARE</span>
          <span class="r">AI Actions</span>
        </div>
        <div class="kz-mock-rows">{rows_html}</div>
      </div>
    </div>'''


def scene_helpers() -> str:
    """Scene 02 — AI Helpers acting on Acme."""
    helpers = [
        ('K', 'Reply drafter',     'Drafted QBR follow-up to Sarah — adds three outcomes from yesterday\'s call.', '2 min ago'),
        ('K', 'Risk watcher',      'Mike has been quiet 21 days. Re-intro draft ready, CC\'d James.',                '14 min ago'),
        ('K', 'Expansion scout',   '"Do you do analytics?" — picked up on Tue\'s call. Scoped pitch ready.',         '1 hr ago'),
        ('K', 'QBR builder',       'Friday deck compiled from 12 meetings. Awaiting your review.',                    'today'),
    ]
    cards_html = '\n'.join(
        f'''<div class="kz-mock-helper">
          <span class="kz-mock-helper-icon">{E(icon)}</span>
          <div class="kz-mock-helper-body">
            <div class="kz-mock-helper-name">{E(name)}</div>
            <div class="kz-mock-helper-text">{E(text)}</div>
          </div>
          <div class="kz-mock-helper-meta">
            <div class="kz-mock-helper-when">{E(when)}</div>
            <a class="kz-mock-helper-open">Open →</a>
          </div>
        </div>''' for icon, name, text, when in helpers
    )
    return f'''<div class="kz-mock kz-mock-helpers">
      {_mock_chrome('app.kaizan.ai / clients / acme-creative / helpers')}
      <div class="kz-mock-body">
        <div class="kz-mock-titlebar">
          <h4>Helpers · Acme Creative</h4>
          <span class="kz-mock-running"><span class="kz-mock-dot"></span> auto-running</span>
        </div>
        <div class="kz-mock-helpers-list">{cards_html}</div>
      </div>
    </div>'''


def scene_care() -> str:
    """Scene 03 — CARE radar + dimension scores."""
    dims = [
        ('C', 'Client sentiment',  '8.4', 84),
        ('A', 'Activity',          '7.2', 72),
        ('R', 'Relationship',      '6.8', 68),
        ('E', 'Expansion',         '7.9', 79),
    ]
    bars_html = '\n'.join(
        f'''<div class="kz-mock-bar">
          <span class="kz-mock-bar-letter">{E(k)}</span>
          <span class="kz-mock-bar-name">{E(name)}</span>
          <span class="kz-mock-bar-track"><span style="width:{pct}%"></span></span>
          <span class="kz-mock-bar-num">{E(score)}</span>
        </div>''' for k, name, score, pct in dims
    )
    # Simple SVG radar — 4-axis polygon. Cleaner than 6 axes; fits aesthetic.
    radar_svg = '''<svg viewBox="-110 -110 220 220" class="kz-mock-radar">
      <!-- grid rings -->
      <polygon points="0,-100 100,0 0,100 -100,0" fill="none" stroke="rgba(0,0,0,0.08)" stroke-width="1"/>
      <polygon points="0,-66 66,0 0,66 -66,0"     fill="none" stroke="rgba(0,0,0,0.08)" stroke-width="1"/>
      <polygon points="0,-33 33,0 0,33 -33,0"     fill="none" stroke="rgba(0,0,0,0.08)" stroke-width="1"/>
      <!-- spokes -->
      <line x1="0" y1="-100" x2="0" y2="100" stroke="rgba(0,0,0,0.08)"/>
      <line x1="-100" y1="0" x2="100" y2="0" stroke="rgba(0,0,0,0.08)"/>
      <!-- score polygon  C 84  A 72  R 68  E 79 -->
      <polygon points="0,-84 72,0 0,68 -79,0" fill="rgba(255,185,0,0.30)" stroke="#FFB900" stroke-width="2"/>
      <circle cx="0"   cy="-84" r="3.5" fill="#FFB900" stroke="#0A0A0A" stroke-width="1"/>
      <circle cx="72"  cy="0"   r="3.5" fill="#FFB900" stroke="#0A0A0A" stroke-width="1"/>
      <circle cx="0"   cy="68"  r="3.5" fill="#FFB900" stroke="#0A0A0A" stroke-width="1"/>
      <circle cx="-79" cy="0"   r="3.5" fill="#FFB900" stroke="#0A0A0A" stroke-width="1"/>
      <!-- axis labels -->
      <text x="0"   y="-110" text-anchor="middle" font-size="11" font-weight="700" fill="#0A0A0A">C</text>
      <text x="112" y="4"    text-anchor="start"  font-size="11" font-weight="700" fill="#0A0A0A">A</text>
      <text x="0"   y="120"  text-anchor="middle" font-size="11" font-weight="700" fill="#0A0A0A">R</text>
      <text x="-112" y="4"   text-anchor="end"    font-size="11" font-weight="700" fill="#0A0A0A">E</text>
    </svg>'''
    return f'''<div class="kz-mock kz-mock-care">
      {_mock_chrome('app.kaizan.ai / clients / acme-creative / care')}
      <div class="kz-mock-body">
        <div class="kz-mock-titlebar">
          <h4>CARE · Acme Creative</h4>
          <div class="kz-mock-score">
            <span class="num">7.6</span><span class="lbl">overall · ↑ +0.4 7d</span>
          </div>
        </div>
        <div class="kz-mock-care-grid">
          <div class="kz-mock-care-radar">{radar_svg}</div>
          <div class="kz-mock-care-bars">{bars_html}</div>
        </div>
      </div>
    </div>'''


def scene_chatbot() -> str:
    """Scene 04 — chatbot with citations."""
    user1 = "What's the renewal risk on Acme?"
    bot1_lines = [
        "Two flags worth a look this week:",
        "• Mike (procurement) hasn’t replied in 21 days &mdash; usually 3.",
        "• Sentiment dipped 0.4 after the May 6 review.",
        "Otherwise activity and expansion signals stay healthy.",
    ]
    user2 = "Draft a re-intro to Mike."
    bot2_lines = [
        "Drafted &mdash; tone matches your last 8 emails to procurement.",
        "Included the analytics add-on context from Tuesday’s call.",
    ]
    citations1 = ['Email · 21d ago', 'May 6 review', 'CARE A · 7.2']
    citations2 = ['Tue call · 14:30', 'Email pattern · 90d']
    cit1_html = ' '.join(f'<span class="kz-mock-cite">{E(c)}</span>' for c in citations1)
    cit2_html = ' '.join(f'<span class="kz-mock-cite">{E(c)}</span>' for c in citations2)
    chips = ['Recent key moments', 'Renewal risk', 'Coverage gaps', 'Expansion ideas']
    chips_html = ' '.join(f'<span class="kz-mock-chip">{E(c)}</span>' for c in chips)
    return f'''<div class="kz-mock kz-mock-chatbot">
      {_mock_chrome('app.kaizan.ai / clients / acme-creative / chatbot')}
      <div class="kz-mock-body">
        <div class="kz-mock-titlebar">
          <h4>Chatbot · Acme Creative</h4>
          <span class="kz-mock-mcp">MCP · CLAUDE</span>
        </div>
        <div class="kz-mock-chat">
          <div class="kz-mock-msg user"><div class="bubble">{E(user1)}</div></div>
          <div class="kz-mock-msg ai">
            <div class="bubble">
              {''.join(f"<p>{l}</p>" for l in bot1_lines)}
              <div class="cites">{cit1_html}</div>
            </div>
          </div>
          <div class="kz-mock-msg user"><div class="bubble">{E(user2)}</div></div>
          <div class="kz-mock-msg ai">
            <div class="bubble">
              {''.join(f"<p>{l}</p>" for l in bot2_lines)}
              <div class="cites">{cit2_html}</div>
            </div>
          </div>
        </div>
        <div class="kz-mock-input">
          <span class="placeholder">Ask about this client&hellip;</span>
          <span class="send">↗</span>
        </div>
        <div class="kz-mock-chips">{chips_html}</div>
      </div>
    </div>'''


# Scene index → renderer (kept in sync with scene tab labels in render_home)
SCENES = [scene_assistant, scene_helpers, scene_care, scene_chatbot]


# ─────────────────────────────────────────────────────────────────────
# PAGE TEMPLATES
# ─────────────────────────────────────────────────────────────────────

def render_home() -> str:
    scenes = [
        ('AI Assistant for the team',
         'Joins every call, understands every email, updates your systems. A unified system of intelligence housing what you need to know about every client relationship.'),
        ('AI Helpers on every client',
         "Specialist agents on every account, working 24/7: drafting replies, prepping QBRs, watching for risk, surfacing expansion the moment it lands."),
        ('CARE Model · Relationship health',
         "The four-pillar framework — Client satisfaction, Activity with stakeholders, Relationship strength, Expansion opportunities — scored and tracked on every account."),
        ('Chatbot and MCP',
         "Ask anything in natural language. Connect Kaizan to Claude, ChatGPT or any MCP-aware tool — answers with citations from the source conversations."),
    ]
    tour_tabs = '\n'.join(
        f'<button class="kz-tour-tab{" is-active" if i == 0 else ""}" data-tour-tab type="button">'
        f'<div class="scene">SCENE 0{i+1}</div>'
        f'<div class="title">{E(t)}</div>'
        f'<div class="desc">{E(d)}</div>'
        f'</button>'
        for i, (t, d) in enumerate(scenes)
    )

    care = [
        ('C', 'Client satisfaction',
         "Sentiment on every stakeholder and thread. Not RAG guesses — evidence pulled from the source conversations."),
        ('A', 'Activity with stakeholders',
         'Every meeting, email and call summarised against the people who matter; CRM kept honest automatically.'),
        ('R', 'Relationship strength',
         'Coverage gaps, dormant contacts, single-threaded risk and warm re-intros — handled before you ask.'),
        ('E', 'Expansion opportunities',
         'Upsell and cross-sell signals surfaced the moment a client raises them — not next quarter.'),
    ]
    care_html = '\n'.join(
        f'<div class="kz-care-cell"><div class="glyph">{E(k)}</div>'
        f'<div class="title">{E(t)}</div><div class="desc">{E(d)}</div></div>'
        for k, t, d in care
    )

    persona_pills = '\n'.join(
        f'<a class="kz-persona-pill kz-shadow-card" href="for/{slug}/">'
        f'<span>{E(label)}</span><span class="arr">→</span></a>'
        for slug, label in PERSONA_LIST
    )

    quote_cards = '\n'.join(
        f'<div class="kz-quote-card kz-shadow-card">'
        f'<q>{E(q["q"])}</q>'
        f'{portrait(q["name"], q["role"], q["co"], q["tone"], depth=0)}'
        f'</div>'
        for q in QUOTES[:2]
    )

    body = f'''
    {nav_html(0, active='Home')}

    <!-- HERO -->
    <section class="kz-hero kz-wash-gold-pale">
      <div class="kz-hero-copy">
        <h1 class="kz-h1">
          Client Service<br>
          <span class="kz-mark" style="margin-top:10px;">Excellence</span>
        </h1>
        <p class="kz-lede" style="margin-top:24px;font-size:18px;max-width:520px;">
          Kaizan is the AI platform for client service professionals. Where AI Helpers work 24/7
          so your team increases the ROI and Revenue across all your clients.
        </p>
        <div class="kz-hero-cta-stack">
          <a class="kz-cta-card is-yellow" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">
            <div>
              <div class="kz-cta-eyebrow">30-min live demo</div>
              <div class="kz-cta-headline">See Kaizan in action</div>
            </div>
            <div class="kz-cta-pill"><span>Book a demo</span><span class="kz-cta-arrow">→</span></div>
          </a>
          <!-- TODO: re-enable when the CARE white paper is ready
          <a class="kz-cta-card is-ghost" href="#whitepaper">
            <div>
              <div class="kz-cta-eyebrow">CARE white paper · 18 min</div>
              <div class="kz-cta-headline">What the top 10% do differently?</div>
            </div>
            <div class="kz-cta-pill"><span>Whitepaper</span><span class="kz-cta-arrow">↓</span></div>
          </a>
          -->
        </div>
      </div>
      <div class="kz-hero-video">
        <video data-hero-video src="assets/video/hero.mp4"
               poster="assets/video/hero-poster.jpg"
               loop playsinline preload="metadata"></video>
        <button class="overlay" type="button" data-hero-overlay aria-label="Play video">
          <div class="head">
            <span>▶ KAIZAN · 2 MIN OVERVIEW</span>
            <span>00:00 / 02:07</span>
          </div>
          <div class="play-row">
            <div class="play">▶</div>
            <div class="play-title">See Kaizan in action</div>
          </div>
        </button>
      </div>
    </section>

    {marquee_html(CLIENT_LOGOS + INTEGRATIONS, depth=0)}

    <!-- PRODUCT TOUR -->
    <section class="kz-section-loose" data-tour>
      <div class="kz-eyebrow">Product tour</div>
      <h2 class="kz-h1" style="margin:12px 0 24px;font-size:clamp(36px,4.6vw,72px);">
        AI Assistant &amp; Agents for elite client service
      </h2>
      <div class="kz-tour">
        <div class="kz-tour-tabs">{tour_tabs}</div>
        <div class="kz-tour-stage">
          <div class="kz-tour-badge" data-tour-badge>LIVE · ACME CREATIVE</div>
          {''.join(f'<div class="kz-tour-frame{" is-active" if i == 0 else ""}" data-scene="{i}">{render()}</div>' for i, render in enumerate(SCENES))}
        </div>
      </div>
    </section>

    <!-- CARE -->
    <section class="kz-section">
      <div class="kz-eyebrow">The CARE framework · the source of truth for your client relationships</div>
      <h2 class="kz-h2" style="margin-top:12px;max-width:880px;">
        AI Helpers working 24/7 to grow every client relationship.
      </h2>
      <div class="kz-care">{care_html}</div>
    </section>

    <!-- PERSONAS — TODO: re-enable once persona pages content is ready
    <section class="kz-personas">
      <h2 class="kz-h2" style="margin-bottom:8px;">I am a…</h2>
      <p class="kz-lede" style="margin-bottom:28px;max-width:640px;font-size:16px;">
        Pick your role to see how Kaizan fits into your week — personalised guidance, real use cases and daily workflows.
      </p>
      <div class="kz-personas-grid">{persona_pills}</div>
    </section>
    -->

    <!-- PROOF -->
    <section class="kz-proof">
      <div class="kz-proof-stat">
        <div class="kz-eyebrow" style="color:rgba(255,251,240,.6);">Measured</div>
        <div>
          <div class="num">21%+</div>
          <div class="lbl">average revenue growth per client across the full client portfolio.</div>
        </div>
      </div>
      <div class="kz-proof-quotes">{quote_cards}</div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band">
      <h2 class="head">See your clients, clearly.</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
      </div>
    </section>

    {footer_html(0)}
    '''
    return page_head('Client super intelligence for client service teams', 0,
                     'Kaizan is the AI platform for client service professionals — '
                     'AI Helpers that work 24/7 to grow client ROI, satisfaction and revenue.') + body + page_foot()


def render_product() -> str:
    helpers = [
        dict(k='$', name='ROI Helpers', tag='Grow client ROI',
             blurb=('Agents that read every piece of work — every brief, deck, recap, deliverable, call — across every client, and tell you where the work itself is leaking value. They benchmark across the book, then suggest exactly what would lift output for that one client.'),
             signals=[
                'Acme briefs 28% shorter than top-quartile clients · template suggested',
                'Verkeer creative review skipped 3 weeks running · cadence fix drafted',
                'Northwind targeting brief missing 4 fields your best work always has',
                'Hooli campaign tracking 12% under benchmark · two playbooks pulled from wins',
             ],
             evidence=("Helpers compare each client’s work against the patterns your best work follows — pulled live from your docs, decks, transcripts and outcomes. Continuously learning, so the suggestion for Acme on Friday is sharper than the one on Monday.")),
        dict(k='❤', name='Relationship Helpers', tag='Deepen relationship strength',
             blurb='Agents that map every stakeholder and act on the gaps. They catch silence, dormant champions and thin coverage — and write the warm re-intro before your weekly review.',
             signals=[
                '21 days silent — Mike @ Acme · re-intro draft ready',
                'No senior coverage at Northwind · exec match suggested',
                'New buyer joined at Stark · onboarding note drafted',
                'Tone shift on Sarah @ Hooli · escalation flagged with evidence',
             ],
             evidence='Trained on your conversations: who replies fast, who goes quiet, what tone your champions actually use. The longer you run it, the more the helpers sound like your best AM at their best moment.'),
        dict(k='⚙', name='Growth Helpers', tag='Proactive client growth',
             blurb=("Agents that listen for the moment a client says something they didn’t mean as a buying signal — and turn it into a proactive, client-specific suggestion. Not generic upsell. The next right move for that client, this week."),
             signals=[
                '"Do you do analytics?" — Acme · scoped pitch drafted using 3 lookalike wins',
                "Hooli mentioned a new product line on Tuesday’s call · launch playbook pulled",
                'Verkeer brief widened to include retention work · capacity check + brief drafted',
                'Scale CMO joined Stark · suggest re-pitching the measurement workstream',
             ],
             evidence=("Suggestions are specific to that client’s objectives, history and tone — not a template. Helpers read every conversation across every account, so a cue heard on a Wednesday call shows up as a written-up move on Thursday morning.")),
        dict(k='+', name='Custom Helpers', tag='Build your own',
             blurb='Spin up a helper grounded in your data and your objective — onboarding QA, exec read-outs, pitch prep, capacity planning. Describe the outcome; Kaizan assembles the agent.',
             signals=[
                '"Flag any account where the senior buyer has gone quiet 14d+"',
                "\"Draft a renewal narrative using last quarter’s wins on this client\"",
                '"Brief me before every Acme call with the last 5 decisions"',
                '"Watch for capacity asks across all retainer clients"',
             ],
             evidence=("Custom helpers inherit the same private memory: every doc, deck, call and Slack channel you connect. They keep learning from your outcomes, so each run is more personalised to that client’s objectives than the last.")),
    ]

    care_dims = [
        ('C', 'Client sentiment',
         'How the client actually feels about the work — tone, effort, intent, pulled from every email, call and review.', 78, '+3'),
        ('A', 'Account activity',
         'Volume, velocity and seniority of two-way contact. Catches drift before the client feels it.', 64, '+1'),
        ('R', 'Relationship coverage',
         'Who you know, how senior, how warm. Spots thin coverage and dormant champions before the work suffers.', 52, '-9'),
        ('E', 'Engagement growth',
         'Where the scope can deepen — capability gaps, brief widenings, exec asks. Pulled from the language clients actually use.', 71, '+2'),
    ]

    pillar_hero = [
        ('01','AI Assistant',     'Captures every meeting. Ships the work behind it.'),
        ('02','AI Helpers',       'Outcome-shaped agents that actually act'),
        ('03','Client Health Model','Self-learning relationship score'),
        ('04','Client 360',       'Market context for every account'),
    ]
    pillar_html = '\n'.join(
        f'<div class="kz-pillar"><div class="num">{E(n)}</div>'
        f'<div class="title">{E(t)}</div><div class="desc">{E(d)}</div></div>'
        for n, t, d in pillar_hero
    )

    asst_features = [
        ('Joins every call', 'Teams · Zoom · Google Meet · in-person uploads.'),
        ('Decisions, not transcripts', 'Action items, owners and dates. The shape of work.'),
        ('Does the work',
         'Meeting recaps, follow-ups, status notes, CRM hygiene, brief-backs. Humans approve what matters; the rest just gets done.'),
        ('Sounds like you',
         "Reads every doc, deck and Slack thread for that client — so a draft for Acme actually sounds like Acme, not a template."),
    ]
    asst_html = '\n'.join(
        f'<div class="kz-dark-feature"><h4>{E(t)}</h4><p>{E(d)}</p></div>'
        for t, d in asst_features
    )

    timeline_cards = [
        dict(when='Today · 14:30', who='Quarterly review',
             sum='Renewal pushed to Q3. Mike concerned about analytics gap. Senior buyer (Sarah) joining next call.',
             tags=['Renewal slip','New buyer']),
        dict(when='Tue · 11:00', who='Creative brief',
             sum='New campaign signed off. Wants ROI deck before exec read-out on Friday.',
             tags=['Action: deck']),
        dict(when='Mon · 09:15', who='Slack — #acme-team',
             sum='Three messages on attribution model. Resolved by lunch. No blocker.',
             tags=['Resolved']),
    ]
    timeline_html = '\n'.join(
        f'''<div class="kz-timeline-card">
            <div class="top"><div class="who">{E(c["who"])}</div><div class="when">{E(c["when"])}</div></div>
            <div class="sum">{E(c["sum"])}</div>
            <div class="tags">{''.join(f'<span class="tag">{E(t.upper())}</span>' for t in c["tags"])}</div>
          </div>''' for c in timeline_cards
    )

    helpers_tabs = '\n'.join(
        f'''<button type="button" class="kz-helpers-tab{" is-active" if i == 0 else ""}" data-helper-tab>
          <span class="glyph">{E(h["k"])}</span>
          <div><div class="num">0{i+1}</div><div class="label">{E(h["tag"])}</div></div>
        </button>''' for i, h in enumerate(helpers)
    )

    def helper_panel(h, i):
        signals = '\n'.join(
            f'''<div class="row">
              <span class="glyph">{E(h["k"])}</span>
              <div style="flex:1;">
                <div class="text">{E(s)}</div>
                <div class="meta">evidence · {2+j*3}m ago</div>
              </div>
              <a class="open" href="#">OPEN →</a>
            </div>'''
            for j, s in enumerate(h["signals"])
        )
        return f'''<div class="kz-helpers-detail" data-helper-panel>
          <div>
            <div class="kz-eyebrow">Helper 0{i+1} · {E(h["tag"])}</div>
            <div class="name">{E(h["name"])}</div>
            <div class="blurb">{E(h["blurb"])}</div>
            <div class="behaviour">
              <div class="kz-eyebrow" style="margin-bottom:10px;">How it behaves</div>
              <div class="body">{E(h["evidence"])}</div>
            </div>
          </div>
          <div class="kz-helper-feed">
            <div class="head"><span class="label">LIVE · ACME CREATIVE</span><span class="meta">auto-running</span></div>
            <div class="body">{signals}</div>
          </div>
        </div>'''
    helpers_panels = '\n'.join(helper_panel(h, i) for i, h in enumerate(helpers))

    care_cards = '\n'.join(
        f'''<div class="kz-care-card">
          <div class="top">
            <div class="glyph">{E(k)}</div>
            <div><div class="num">0{i+1}</div><div class="label">{E(name)}</div></div>
          </div>
          <div class="desc">{E(desc)}</div>
          <div class="bar">
            <div class="bar-track"><div class="bar-fill" style="width:{score}%;"></div></div>
            <div class="bar-val">{score}</div>
          </div>
        </div>''' for i, (k, name, desc, score, _) in enumerate(care_dims)
    )

    composite_cells = '\n'.join(
        f'''<div class="cell{' is-warn' if delta.startswith("-") else ''}">
          <div class="k">{E(k)} · {E(name.split(" ")[0])}</div>
          <div class="v">{score}</div>
          <div class="d">{E(delta)} 7d</div>
        </div>''' for k, name, _, score, delta in care_dims
    )

    c360_rows = [
        ('EXEC MOVE', 'New CMO joined from Stark — Jen Patel',
         'Likely to push for analytics tooling. Buyer profile updated.', '→ Growth helper'),
        ('EARNINGS', 'Q1 call: cost discipline; growth still funded',
         'CFO emphasised brand spend. Renewal posture: positive.', '→ Relationship helper'),
        ('HIRING', '12 open roles in performance marketing',
         'Capability gap that overlaps Kaizan capacity. Brief drafted.', '→ Growth helper'),
        ('COMPETITOR', 'Competitor X announced agency-wide AI tool',
         'No customer overlap mentioned. Watching for client reaction.', '→ Watch-list'),
    ]
    c360_html = '\n'.join(
        f'''<div class="kz-c360-row">
          <span class="tag">{E(tag)}</span>
          <div><div class="head">{E(head)}</div><div class="sub">{E(sub)}</div></div>
          <div class="route">{E(route)}</div>
        </div>''' for tag, head, sub, route in c360_rows
    )

    pipeline_steps = [
        ('01','Ingest','Gmail, Outlook, Teams, Zoom, Slack, HubSpot, Salesforce. Zero-retention by default.'),
        ('02','Analyse','Client health scoring runs continuously. Sentiment, activity, coverage, growth.'),
        ('03','Act','Helpers draft, chase, schedule, summarise. Humans approve what matters.'),
        ('04','Learn','Outcomes feed back: what predicts a healthy engagement, per segment, per team.'),
    ]
    pipeline_html = '\n'.join(
        f'<div class="kz-pipeline-cell"><div class="num">{E(n)}</div>'
        f'<div class="title">{E(t)}</div><div class="desc">{E(d)}</div></div>'
        for n, t, d in pipeline_steps
    )

    trust_items = [
        ('SOC 2 Type II', 'Independently audited. Report available under NDA.'),
        ('Zero retention', 'Your conversations never train foundation models.'),
        ('EU + US residency', 'Pick your region. Data stays where you need it.'),
        ('MCP + REST API', 'Wire Kaizan into your own agents and tools.'),
        ('SSO + SCIM', 'Okta, Azure AD, Google Workspace. Managed provisioning.'),
        ('Per-role access', 'Scoped by account, team or client. Never leaky.'),
    ]
    trust_html = '\n'.join(
        f'<div class="kz-trust-card"><h4>{E(t)}</h4><p>{E(d)}</p></div>'
        for t, d in trust_items
    )

    q = QUOTES[3]

    body = f'''
    {nav_html(1, active='Product')}

    <!-- HERO -->
    <section class="kz-section-tight" id="product-hero">
      <div class="kz-eyebrow">PRODUCT · CLIENT SUPER INTELLIGENCE</div>
      <h1 class="kz-h1 kz-h1-xl" style="margin-top:20px;max-width:1180px;">
        One platform for <span class="kz-mark">AI-first</span><br>
        client service teams.
      </h1>
      <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:48px;margin-top:32px;align-items:flex-end;">
        <p class="kz-lede" style="font-size:19px;max-width:640px;">
          The AI Assistant captures and unifies every meeting, chat and email.
          The CARE Client Health Model scores every relationship.
          AI Helpers act on every client for you.
          Client360 shares market intel that affects clients.
          Together they form a system of truth and action for your client teams.
        </p>
        <div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap;">
          <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo →</a>
        </div>
      </div>
      <div class="kz-pillars">{pillar_html}</div>
    </section>

    <!-- 01 · AI ASSISTANT -->
    <section class="kz-dark-section" id="ai-assistant">
      <div class="kz-eyebrow-row">
        <span class="kz-eyebrow kz-eyebrow-yellow">01 · AI Assistant</span>
        <span class="kz-eyebrow" style="color:rgba(255,251,240,.45);">The pillar everything else stands on</span>
      </div>
      <h2 class="kz-h1" style="font-size:84px;line-height:1.02;max-width:1100px;">
        Every meeting captured.<br>
        <span class="kz-mark" style="color:#0A0A0A;">The work, done.</span>
      </h2>
      <div class="kz-dark-grid">
        <div>
          <p class="copy">
            The AI Assistant joins every call — Teams, Zoom, Google Meet — and turns it into structured,
            searchable memory by client automatically. Decisions, owners, deadlines, sentiment. A living
            personalised memory of every client. Then it ships the work behind the meeting: recaps,
            follow-ups, status notes, CRM hygiene. Humans approve what matters; the rest just gets done.
          </p>
          <div class="kz-dark-features">{asst_html}</div>
        </div>
        <div class="kz-timeline">
          <div class="head">
            <span class="label">ACME · TIMELINE</span>
            <span class="meta">last 7 days</span>
          </div>
          <div class="body">{timeline_html}</div>
        </div>
      </div>
    </section>

    <!-- 02 · AI HELPERS -->
    <section class="kz-helpers" id="care" data-helpers>
      <div style="max-width:900px;">
        <div class="kz-eyebrow">02 · AI Helpers</div>
        <h2 class="kz-h2 kz-h2-lg" style="margin-top:14px;">Helpers built for client growth. Acting around the clock.</h2>
        <p class="kz-lede" style="font-size:18px;margin-top:18px;max-width:720px;">
          Three packs of AI Helpers — plus your own. Every helper is grounded in your company data:
          docs, decks, transcripts, Slack, CRM, email. They keep learning from every new conversation,
          so the output gets more personal to each client&rsquo;s objectives the longer you run them.
        </p>
      </div>
      <div class="kz-helpers-tabs">{helpers_tabs}</div>
      {helpers_panels}
    </section>

    <!-- 03 · CARE MODEL -->
    <section class="kz-section-loose" id="health-model">
      <div style="display:grid;grid-template-columns:1fr 1.1fr;gap:48px;align-items:flex-start;">
        <div>
          <div class="kz-eyebrow">03 · CARE Client Health Model</div>
          <h2 class="kz-h2 kz-h2-lg" style="margin-top:14px;max-width:520px;">
            A self-learning relationship score, grounded in your data.
          </h2>
          <p class="kz-lede" style="font-size:18px;margin-top:22px;max-width:520px;">
            The unifying score across every Helper. It learns from your won pitches, kept clients and
            lost briefs — what predicts a healthy engagement in your company, not the average of someone
            else&rsquo;s. Not a biased RAG status. Re-tuned weekly against your data.
          </p>
          <div style="margin-top:26px;padding:18px 22px;background:var(--kz-paper);border:1px solid var(--kz-line);border-radius:12px;max-width:520px;">
            <div class="kz-eyebrow" style="margin-bottom:10px;">Trained on you</div>
            <p style="font-size:15px;line-height:1.55;color:rgba(10,10,10,.78);">
              The weights that drive CARE for a 200-person agency look nothing like a 20-person consultancy.
              We tune privately, per tenant — your model never trains a foundation model and never crosses
              tenant lines.
            </p>
          </div>
        </div>
        <div class="kz-care-grid">{care_cards}</div>
      </div>

      <div class="kz-composite">
        <div>
          <div class="lbl">COMPOSITE · ACME</div>
          <div class="num">66</div>
          <div class="delta">↓ 8 vs. last week</div>
        </div>
        <div class="grid">{composite_cells}</div>
        <div class="note">
          Relationship dipped after senior contact dropped from the meeting cadence. Helper drafted a re-engagement.
        </div>
      </div>
    </section>

    <!-- 04 · CLIENT 360 -->
    <section class="kz-c360" id="client-360">
      <div class="kz-c360-grid">
        <div>
          <div class="kz-eyebrow">04 · Client 360</div>
          <h2 class="kz-h2 kz-h2-lg" style="margin-top:14px;max-width:560px;">
            Market research on every client. Always-on context for every Helper.
          </h2>
          <p class="kz-lede" style="font-size:18px;margin-top:22px;max-width:560px;">
            Client 360 continuously researches every account — funding, hiring, exec moves, competitor noise,
            earnings tone, product launches — and feeds it into the Helpers as live ground truth. So when CARE drops,
            you don&rsquo;t just know <em>that</em> something changed — you know <em>what</em>.
          </p>
          <div class="kz-dark-features" style="margin-top:28px;color:var(--kz-ink);max-width:560px;">
            <div class="kz-dark-feature" style="border-color:var(--kz-line);"><h4 style="color:var(--kz-ink);">Always-on research</h4><p style="color:var(--kz-mute);">Re-checks every client every day. No briefs to commission.</p></div>
            <div class="kz-dark-feature" style="border-color:var(--kz-line);"><h4 style="color:var(--kz-ink);">Routed to Helpers</h4><p style="color:var(--kz-mute);">Context lands in the right Helper, not in a buried report.</p></div>
            <div class="kz-dark-feature" style="border-color:var(--kz-line);"><h4 style="color:var(--kz-ink);">Source-backed</h4><p style="color:var(--kz-mute);">Every claim links to the article, filing or post it came from.</p></div>
            <div class="kz-dark-feature" style="border-color:var(--kz-line);"><h4 style="color:var(--kz-ink);">Your watch-list</h4><p style="color:var(--kz-mute);">Tag what matters per account: comp moves, hiring, M&amp;A.</p></div>
          </div>
        </div>
        <div class="kz-c360-feed">
          <div class="head"><span>CLIENT 360 · ACME</span><span>updated 4m ago</span></div>
          <div class="body">{c360_html}</div>
        </div>
      </div>
    </section>

    <!-- HOW IT WORKS -->
    <section class="kz-section" id="how-it-works">
      <div class="kz-eyebrow">How it works</div>
      <h2 class="kz-h2" style="margin-top:10px;max-width:820px;">
        From conversation → signal → action, in minutes.
      </h2>
      <div class="kz-pipeline">{pipeline_html}</div>
    </section>

    <!-- ENTERPRISE TRUST -->
    <section class="kz-trust" id="security">
      <div class="kz-trust-grid">
        <div>
          <div class="kz-eyebrow">Built for enterprise</div>
          <h2 class="kz-h2" style="margin-top:10px;">Your conversations, your data, your control.</h2>
        </div>
        <div class="kz-trust-cards">{trust_html}</div>
      </div>
    </section>

    <!-- INTEGRATIONS anchor (used by mega-menu) -->
    <section class="kz-section-tight" id="integrations">
      <div class="kz-eyebrow">Integrations</div>
      <h2 class="kz-h3" style="margin-top:10px;font-size:24px;max-width:820px;">
        Native connectors for the tools your team already lives in.
      </h2>
      <p class="kz-lede" style="margin-top:14px;max-width:720px;">
        {E(', '.join(INTEGRATIONS))}, plus webhooks and a REST/MCP API for everything else.
      </p>
    </section>

    <!-- FAQ anchor (placeholder) -->
    <section class="kz-section-tight" id="faqs">
      <div class="kz-eyebrow">FAQs</div>
      <h2 class="kz-h3" style="margin-top:10px;font-size:24px;max-width:820px;">
        Common questions, ranked by how often a security review asks them.
      </h2>
      <p class="kz-lede" style="margin-top:14px;max-width:720px;">
        Answers ship with our security review pack. <a href="https://calendar.app.google/V9mCxVimwFr2ynSQ7" style="color:var(--kz-ink);font-weight:600;">Request the pack →</a>
      </p>
    </section>

    <!-- PRICING anchor (placeholder) -->
    <section class="kz-section-tight" id="pricing">
      <div class="kz-eyebrow">Pricing</div>
      <h2 class="kz-h3" style="margin-top:10px;font-size:24px;max-width:820px;">
        Tiered by seats and integration depth.
      </h2>
      <p class="kz-lede" style="margin-top:14px;max-width:720px;">
        Detailed pricing is shared in the demo. <a href="https://calendar.app.google/V9mCxVimwFr2ynSQ7" style="color:var(--kz-ink);font-weight:600;">Book a demo →</a>
      </p>
    </section>

    <!-- QUOTE -->
    <section class="kz-section">
      <div style="display:grid;grid-template-columns:1fr 1.5fr;gap:40px;align-items:center;">
        {portrait(q['name'], q['role'], q['co'], q['tone'], size='xl', depth=1)}
        <div style="font-family:var(--kz-display);font-size:36px;font-weight:400;line-height:1.25;letter-spacing:-0.015em;">
          &ldquo;{E(q['q'])}&rdquo;
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band kz-cta-band-md">
      <h2 class="head">Put the helpers to work.</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Product', 1,
                     'AI Assistant, AI Helpers, the Client Health Model and Client 360 — '
                     'one platform for AI-first client service teams.') + body + page_foot()


def render_persona(slug: str) -> str:
    p = PERSONAS[slug]
    q = QUOTES[p['quote_idx']]
    others = [(k, n) for k, n in PERSONA_LIST if k != slug][:3]

    pillars_html = '\n'.join(
        f'''<div class="kz-pillar" style="border-bottom:1px solid var(--kz-line);">
          <div class="num">{E(n)}</div>
          <div class="title">{E(t)}</div>
          <div class="desc">{E(d)}</div>
        </div>''' for n, t, d in p['pillars']
    )

    products_html = '\n'.join(
        f'''<div class="kz-product-row">
          <div class="n">0{i+1}</div>
          <div><div class="t">{E(name)}</div><div class="d">{E(desc)}</div></div>
          <div class="frame">
            <div class="frame-label">PRODUCT · {E(name.upper())}</div>
            <div class="frame-fill">GIF · product loop</div>
          </div>
        </div>''' for i, (name, desc) in enumerate(p['products'])
    )

    objections_html = '\n'.join(
        f'<div class="kz-objections-row"><div class="q">{E(qq)}</div><div class="a">{E(aa)}</div></div>'
        for qq, aa in p['objections']
    )

    others_html = '\n'.join(
        f'<a class="kz-persona-pill" href="../{k}/"><span>For {E(n)}</span><span class="arr">→</span></a>'
        for k, n in others
    )

    persona_label = p['eyebrow'].split('· ')[1].lower() if '· ' in p['eyebrow'] else 'people'

    body = f'''
    {nav_html(2)}

    <!-- HERO -->
    <section class="kz-persona-hero">
      <div class="kz-eyebrow">{E(p['eyebrow'])}</div>
      <div class="kz-persona-hero-grid">
        <div>
          <h1 class="kz-h1">
            {E(p['h1'][0])} <span class="kz-mark">{E(p['h1'][1])}</span>
          </h1>
          <p class="kz-lede" style="margin-top:26px;max-width:560px;">{E(p['sub'])}</p>
          <div class="kz-flex" style="gap:10px;margin-top:28px;">
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo →</a>
            <a class="kz-btn kz-btn-ghost" style="padding:14px 22px;" href="../../insights/">Download CARE white paper</a>
          </div>
        </div>
        <div class="kz-persona-quote" style="background:{p['quote_bg']};">
          <div class="copy">
            <div class="role">{E(p['quote_role'])}</div>
            <q>{E(p['quote_pull'])}</q>
          </div>
        </div>
      </div>
    </section>

    <!-- WHAT YOU'LL CARE ABOUT -->
    <section class="kz-section" style="border-top:1px solid var(--kz-line);">
      <div class="kz-eyebrow">What you&rsquo;ll care about</div>
      <div class="kz-pillars cols-3 is-thick" style="margin-top:24px;">
        {pillars_html}
      </div>
    </section>

    <!-- HOW KAIZAN HELPS -->
    <section class="kz-section">
      <div class="kz-eyebrow">How Kaizan helps</div>
      <h2 class="kz-h2" style="margin:12px 0 36px;max-width:900px;">{E(p['product_h2'])}</h2>
      {products_html}
    </section>

    <!-- QUOTE -->
    <section class="kz-persona-quote-section">
      <div style="font-family:var(--kz-display);font-size:36px;font-weight:400;line-height:1.25;letter-spacing:-0.015em;">
        &ldquo;{E(q['q'])}&rdquo;
      </div>
      <div>
        {portrait(q['name'], q['role'], q['co'], q['tone'], size='lg', depth=2)}
        <a style="display:inline-block;margin-top:20px;font-size:14px;font-weight:600;text-decoration:none;color:var(--kz-ink);" href="../../{p['quote_cta_href']}">{E(p['quote_cta'])}</a>
      </div>
    </section>

    <!-- OBJECTIONS -->
    <section class="kz-section">
      <div class="kz-eyebrow">Objections, answered</div>
      <h2 class="kz-h2" style="margin-top:10px;margin-bottom:32px;">
        The questions {E(persona_label)}s actually ask us.
      </h2>
      <div class="kz-objections">{objections_html}</div>
    </section>

    <!-- NOT QUITE YOU? -->
    <section class="kz-persona-ribbon">
      <div class="kz-eyebrow">Not quite you?</div>
      <div class="kz-persona-ribbon-grid">{others_html}</div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band-dark">
      <h2 class="head">{E(p['cta'])}</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-yellow" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
        <a class="kz-btn kz-btn-ghost-light" style="padding:14px 24px;font-size:15px;" href="../../about/">Talk to our CEO</a>
      </div>
    </section>

    {footer_html(2)}
    '''
    label = next((n for k, n in PERSONA_LIST if k == slug), slug.replace('-', ' ').title())
    return page_head(f'For {label}', 2, p['sub']) + body + page_foot()


def render_customers() -> str:
    cases = [
        ('Anything Is Possible','Media agency · 80 people','146% NDR','warm',
         'Kaizan is the account manager who never sleeps.','Mark Raymond','Co-founder', 'anything-is-possible'),
        ('Verkeer','Dutch agency · 40 people','2× QBR prep','olive',
         'We cut account review prep from 6 hours to 40 minutes.','Hannah Carthy','MD', 'verkeer'),
        ('The Kite Factory','Media · 120 people','3 saves / quarter','sand',
         'Three client saves this quarter we would have missed.','Gabriella Krite','Head of Operations', 'the-kite-factory'),
        ('Adimo','SaaS · 60 people','+18pt CSAT','blush',
         'Our CSAT moved before our pipeline did — and then pipeline followed.','Samantha Bessant','Head of Client Success', 'adimo'),
        ('Scale Digital','Consulting · 200 people','2.1× upsell','warm',
         'Expansion signals we used to miss now hit our desk the same day.','Stephen Kerin','Director', 'scale'),
    ]

    stats_html = '\n'.join(
        f'<div class="kz-stat-cell"><div class="num">{E(n)}</div><div class="lbl">{E(l)}</div></div>'
        for n, l in [('146%','avg NDR'), ('60+','client-services teams'),
                     ('3.2h','saved per AM / week'), ('9 / 10','would recommend')]
    )

    feat = cases[0]
    feat_panel_stats = '\n'.join(
        f'<div><div class="v">{E(n)}</div><div class="l">{E(l.upper())}</div></div>'
        for n, l in [('146%','NDR'), ('3.2h','saved / AM / week'), ('12','quarters running')]
    )

    other_cards = '\n'.join(
        f'''<a class="kz-case-card" href="{slug}/">
          <div class="top">
            <div class="name">{E(co)}</div>
            <div class="metric">{E(metric)}</div>
          </div>
          <div class="kind">{E(kind)}</div>
          <q>{E(q)}</q>
          <div class="foot">
            {portrait(name, role, tone=tone, size='xs', depth=1)}
            <span class="read">Read story →</span>
          </div>
        </a>''' for co, kind, metric, tone, q, name, role, slug in cases[1:]
    )

    body = f'''
    {nav_html(1, active='Clients')}

    <!-- HERO -->
    <section class="kz-section-tight">
      <div class="kz-eyebrow">Clients · 60+ client-services teams</div>
      <h1 class="kz-h1" style="margin:20px 0 0;max-width:1100px;">
        The teams running Kaizan keep their clients
        <span class="kz-mark">and grow them.</span>
      </h1>
    </section>

    <!-- STATS -->
    <section class="kz-stat-row">{stats_html}</section>

    <!-- FEATURED -->
    <section class="kz-featured-case">
      <div class="panel">
        <div class="kz-eyebrow" style="color:rgba(255,251,240,.6);">Featured case · Anything Is Possible</div>
        <q>{E(feat[4])}</q>
        <div class="stats">{feat_panel_stats}</div>
        <a class="read" href="#">Read the case study →</a>
      </div>
      {portrait('Mark Raymond', 'Co-founder · AIP', tone='warm', size='2xl', layout='stacked', depth=1)}
    </section>

    <!-- MORE STORIES -->
    <section class="kz-case-cards">
      <h2 class="kz-h2" style="margin-bottom:24px;">More stories.</h2>
      <div class="kz-case-grid">{other_cards}</div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band kz-cta-band-sm">
      <h2 class="head">Be the next case study.</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Clients', 1,
                     '60+ client-services teams running Kaizan to keep their clients and grow them.') + body + page_foot()


def render_case_study(slug: str) -> str:
    c = CASE_DATA[slug]
    stats_html = '\n'.join(
        f'<div class="kz-stat-cell"><div class="num">{E(n)}</div><div class="lbl">{E(l)}</div></div>'
        for n, l in c['stats']
    )
    body_html = '\n'.join(
        f'<section><h2 class="kz-h2">{E(h)}.</h2><p>{E(p)}</p></section>'
        for h, p in c['body']
    )

    body = f'''
    {nav_html(2, active='Clients')}

    <!-- BREADCRUMB -->
    <section class="kz-case-crumb">
      <a href="../">← Clients</a><span class="sep">/</span><span>{E(c['co'])}</span>
    </section>

    <!-- HERO -->
    <section class="kz-case-hero">
      <div>
        <div class="kz-eyebrow">Client story · {E(c['kind'])}</div>
        <div class="name">{E(c['co'])}</div>
        <h1 class="head">{E(c['headline'])}</h1>
        <div class="metric">{E(c['metric'].upper())}</div>
      </div>
      {portrait(c['name'], f"{c['role']} · {c['co']}", tone=c['tone'], size='2xl', layout='stacked', depth=2)}
    </section>

    <!-- STATS -->
    <section class="kz-stat-row">{stats_html}</section>

    <!-- BODY -->
    <section class="kz-case-body">
      <div class="pull">
        <q>{E(c['quote'])}</q>
        <div class="kz-mt-md">{portrait(c['name'], f"{c['role']} · {c['co']}", tone=c['tone'], size='sm', depth=2)}</div>
      </div>
      <div class="sections">{body_html}</div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band">
      <h2 class="head" style="font-size:48px;max-width:780px;margin:0 auto;">
        Want this kind of story for your firm?
      </h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
        <a class="kz-btn kz-btn-ghost" style="padding:14px 24px;background:transparent;" href="../">Read more stories</a>
      </div>
    </section>

    {footer_html(2)}
    '''
    return page_head(f'{c["co"]} · Client story', 2, c['headline']) + body + page_foot()


def render_insights() -> str:
    posts = INSIGHTS_POSTS
    feat = posts[0]
    side_html = '\n'.join(
        f'''<a class="kz-insights-side-card" href="#">
          <div class="cover" style="background-image:url(\'{E(p["img"])}\');"></div>
          <div class="body">
            <span class="kz-eyebrow">{E(p["cat"])}</span>
            <div class="kz-h3" style="font-size:18px;">{E(p["t"])}</div>
            <div class="meta">{E(p["date"].upper())} · {E(p["meta"].upper())}</div>
          </div>
        </a>''' for p in posts[1:3]
    )
    cards_html = '\n'.join(
        f'''<a class="kz-insights-card" href="#">
          <div class="cover" style="background-image:url(\'{E(p["img"])}\');"></div>
          <div class="body">
            <span class="kz-eyebrow">{E(p["cat"])}</span>
            <h3 class="title">{E(p["t"])}</h3>
            <p class="excerpt">{E(p["d"])}</p>
            <div class="meta">{E(p["author"].upper())} · {E(p["date"].upper())} · {E(p["meta"].upper())}</div>
          </div>
        </a>''' for p in posts
    )

    body = f'''
    {nav_html(1, active='Blog')}

    <section class="kz-insights-hero">
      <div class="kz-eyebrow">Blog · from the Kaizan team</div>
      <h1 class="kz-h1 kz-h1-xl" style="margin:20px 0 0;max-width:1100px;">
        Notes on building <span class="kz-mark kz-mark-tight">Client Super Intelligence.</span>
      </h1>
      <p class="kz-lede" style="margin-top:22px;max-width:680px;">
        Product updates, field notes from the firms running Kaizan, and the occasional strong opinion from the team.
      </p>
    </section>

    <section class="kz-insights-featured">
      <article class="kz-insights-feat-main">
        <div class="cover" style="background-image:url('{E(feat['img'])}');"></div>
        <div class="body">
          <div class="kz-flex" style="gap:14px;">
            <span class="kz-eyebrow">{E(feat['cat'])}</span>
            <span class="kz-eyebrow">FEATURED</span>
          </div>
          <h2 class="title">{E(feat['t'])}</h2>
          <p class="excerpt">{E(feat['d'])}</p>
          <div class="foot">
            <span class="meta">{E(feat['author'])} · {E(feat['date'])} · {E(feat['meta'])}</span>
            <a class="read" href="#">Read post →</a>
          </div>
        </div>
      </article>
      <div class="kz-insights-feat-side">{side_html}</div>
    </section>

    <section class="kz-insights-grid">
      <div class="head">
        <h2 class="title">Latest posts</h2>
        <a href="#" style="font-size:13px;font-weight:600;color:var(--kz-mute);text-decoration:none;">Sort · Newest ↓</a>
      </div>
      <div class="kz-insights-cards">{cards_html}</div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Blog', 1,
                     'Notes on building client super intelligence — POV, product updates, field notes and benchmarks.') + body + page_foot()


def render_blog_hidden() -> str:
    """The hidden /blog/ page. Not linked from anywhere.

    Renders an empty state when POSTS is empty; renders the same card grid as
    the Insights page when POSTS contains entries. Each entry needs:
      slug, title, excerpt, date, author, category, cover, body
    """
    has_posts = bool(POSTS)
    if has_posts:
        sorted_posts = sorted(POSTS, key=lambda p: p.get('date', ''), reverse=True)
        cards_html = '\n'.join(
            f'''<a class="kz-insights-card" href="{E(p["slug"])}/">
              <div class="cover" style="background-image:url(\'{E(p.get("cover", ""))}\');"></div>
              <div class="body">
                <span class="kz-eyebrow">{E(p.get("category", ""))}</span>
                <h3 class="title">{E(p["title"])}</h3>
                <p class="excerpt">{E(p.get("excerpt", ""))}</p>
                <div class="meta">{E(p.get("author", "").upper())} · {E(p.get("date", "").upper())}</div>
              </div>
            </a>''' for p in sorted_posts
        )
        grid = f'<section class="kz-insights-grid"><div class="kz-insights-cards">{cards_html}</div></section>'
    else:
        grid = '''<section class="kz-blog-empty">
          <div class="head">No posts yet.</div>
          <p>This page is hidden &mdash; not linked from the public nav.<br>
          Add entries to the <code>POSTS</code> list in <code>tools/build.py</code> and re-run the build.</p>
        </section>'''

    body = f'''
    {nav_html(1)}
    <section class="kz-insights-hero">
      <div class="kz-eyebrow">Blog · hidden landing</div>
      <h1 class="kz-h1" style="margin:20px 0 0;max-width:1100px;">
        Posts.
      </h1>
      <p class="kz-lede" style="margin-top:22px;max-width:680px;">
        A staging ground for the public blog. Not linked from the main navigation. Once we&rsquo;re ready,
        flip the &ldquo;Blog&rdquo; nav target to point here and unlist <code>/insights/</code>.
      </p>
    </section>
    {grid}
    {footer_html(1)}
    '''
    head = '''<!doctype html>
<html lang="en">
<head>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-PNFJD9DV');</script>
<!-- End Google Tag Manager -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog (hidden) · Kaizan</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Hidden blog landing.">
<link rel="icon" type="image/png" sizes="32x32" href="../assets/img/favicon-32x32.png">
<link rel="icon" type="image/webp" sizes="16x16" href="../assets/img/favicon-16x16.webp">
<link rel="apple-touch-icon" sizes="180x180" href="../assets/img/apple-touch-icon.png">
<link rel="mask-icon" href="../assets/img/safari-pinned-tab.svg" color="#FFB900">
<link rel="stylesheet" href="../assets/css/tokens.css">
<link rel="stylesheet" href="../assets/css/site.css">
<script defer src="../assets/js/site.js"></script>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PNFJD9DV"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<div class="kz-page">
<main class="kz-main">
'''
    return head + body + '</main>\n</div>\n</body>\n</html>\n'


def render_blog_post(post: dict) -> str:
    """Render a single hidden-blog post page at /blog/<slug>/index.html."""
    head = '''<!doctype html>
<html lang="en">
<head>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-PNFJD9DV');</script>
<!-- End Google Tag Manager -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Kaizan</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="{desc}">
<link rel="icon" type="image/png" sizes="32x32" href="../../assets/img/favicon-32x32.png">
<link rel="icon" type="image/webp" sizes="16x16" href="../../assets/img/favicon-16x16.webp">
<link rel="apple-touch-icon" sizes="180x180" href="../../assets/img/apple-touch-icon.png">
<link rel="mask-icon" href="../../assets/img/safari-pinned-tab.svg" color="#FFB900">
<link rel="stylesheet" href="../../assets/css/tokens.css">
<link rel="stylesheet" href="../../assets/css/site.css">
<script defer src="../../assets/js/site.js"></script>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-PNFJD9DV"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
<div class="kz-page">
<main class="kz-main">
'''.format(title=E(post['title']), desc=E(post.get('excerpt', '')))

    body = f'''
    {nav_html(2)}
    <article class="kz-essay" style="padding-top:48px;">
      <div class="kz-essay-body">
        <div class="kz-eyebrow">{E(post.get('category', ''))} · {E(post.get('date', ''))}</div>
        <h1 class="kz-h1" style="font-size:64px;margin:18px 0 0;">{E(post['title'])}</h1>
        <div class="kz-mute" style="font-size:14px;margin-top:12px;">{E(post.get('author', ''))}</div>
        {post.get('body', '<p>(empty)</p>')}
        <div style="margin-top:32px;"><a href="../" style="font-weight:600;color:var(--kz-ink);">← Back to all posts</a></div>
      </div>
    </article>
    {footer_html(2)}
    '''
    return head + body + '</main>\n</div>\n</body>\n</html>\n'


def render_about() -> str:
    body = f'''
    {nav_html(1, active='About')}

    <!-- HERO -->
    <section class="kz-about-hero">
      <div class="kz-eyebrow">Founder&rsquo;s Letter · Kaizan</div>
      <h1 class="kz-h1" style="margin:22px 0 0;max-width:1200px;">
        A proactive system of <span class="kz-mark">intelligence</span> for client service.
      </h1>
      <div class="kz-about-byline">
        <div class="avatar">GC</div>
        <div>
          <div class="name">Glen Calvert</div>
          <div class="meta">Co-founder &amp; CEO, Kaizan</div>
        </div>
      </div>
    </section>

    <!-- ESSAY -->
    <article class="kz-essay">
      <div class="kz-essay-body">

        <p class="kz-essay-pull">
          Services is the largest sector of the modern economy. It&rsquo;s also the least instrumented.
          Most departments have an operating system of record. Manufacturing has ERP. Trading has Bloomberg.
          Finance has Xero. Engineering has Github. The multi-trillion-dollar industry of people who serve
          clients for a living has a CRM &mdash; but a CRM is a sales and marketing tool. It was built to
          track the journey to a signature, not the years of work that come after it; delivering performance
          and value to the client, nurturing the relationship, delivering multiple projects globally, and
          becoming a true partner to that business. What this industry needs has never existed: an
          organisational brain with total context and knowledge on every aspect of every client relationship.
          A unified system of intelligence that fuses the external signals of the client and their sector,
          with the internal context of the work being delivered, on every account, in real time across calls,
          emails, chat messages, docs, reports and tool updates. It needs a Client Super Intelligence.
        </p>

        <p>Here&rsquo;s what its absence costs in practice.</p>

        <p>
          A senior account director at a marketing agency in London runs six clients. Her job is to be the
          domain expert in each &mdash; every campaign, every stakeholder, every promise made on every call.
          Instead, her Monday is spent reconstructing it from Slack, timesheets, and her inbox. By 11am
          she&rsquo;s on a call with a CMO firefighting an issue from last week, the full context of which
          she doesn&rsquo;t have. She works 60 hours &amp; does almost no actual client thinking.
        </p>

        <p>
          The same director, on Kaizan, has her AI Assistant throughout the day taking care of the admin,
          updating systems and notifying her to info she needs to know about. With AI Helpers working on
          every account 24/7 &mdash; suggesting ways to improve campaigns, tending to relationships that
          have gone quiet, and hunting for growth opportunities buried in signals from calls she wasn&rsquo;t on.
          By 7:30am her phone has a brief on every account and a pre-brief for the CMO call. Market intel
          is drafted and sent directly to her. She is, finally, the domain expert she was hired to be, across
          every account globally, in real time. The 35 hours she gets back go to strategy, interacting with
          her AI Helpers as a thought partner, and the relationships that decide whether the account grows or not.
        </p>

        <p>
          That&rsquo;s one role. Now multiply it by every Account Manager, Client Service Manager,
          Chief Client Officer &amp; client delivery team in every company in the world that relies on
          person-to-person client management. The judgement that used to live in human heads &mdash;
          invisible to the company, unknowable to the client, &amp; impossible to compound &mdash;
          finally has a home.
        </p>

        <p>
          There&rsquo;s a second cost no-one talks about. Without an organisational brain housing your comms,
          knowledge, decisions and workflows. You&rsquo;re not ready for the era where Agents need context
          to complete tasks. If you rely on client relationships to thrive, you need an AI strategy that
          unlocks the value held across your conversations, systems and output being delivered for clients.
        </p>

        <p>
          For decades, the industry&rsquo;s answer has been that client work is too human to measure:
          too qualitative, too relational. There&rsquo;s truth in that. But the deeper reason is simpler.
          The technology didn&rsquo;t exist. The signal was always there, trapped in conversations no software
          could read. AI and Agents change that. Conversations are computable now, and with them, everything
          that was impossible becomes table stakes.
        </p>

        <p>
          That&rsquo;s why Pravin &amp; I started Kaizan. We spent time inside some of the most demanding
          service first companies in the world. The demand has always been there. The technology finally is too.
        </p>

        <p>
          <strong>We&rsquo;re building Kaizan as the first AI platform for client service &amp; account
          management centric companies</strong>: an organisational brain with total knowledge of every client,
          every product and service, and what you should do next to scale your clients. By unlocking the
          value held in communication interactions alongside docs, reports and system updates. And benchmarked
          the across every account. It turns the collective judgement of that company into infrastructure.
          Not a dashboard. Not a copilot. <strong>The system of record for the work of serving clients</strong>
          and the first one in history that gets smarter every day it&rsquo;s switched on.
        </p>

        <div style="margin-top:32px;">
          <div class="kz-eyebrow" style="color:#FFB900;">At the core of Kaizan are three technologies</div>
        </div>

        <div class="kz-essay-tech">
          <div class="row"><span class="num">01</span><h3>Collective intelligence, always on.</h3></div>
          <p>
            Every CRM in the world was built to be a passive filing cabinet in a UI built for humans to use
            as the system for sales and marketing. And retro fitted for CS. What you put in is what you get
            out, and none of it learns. Kaizan inverts this. Because the brain observes every interaction
            and every deliverable across every client, it builds a continuously updating model of what great
            client service actually looks like inside that business &mdash; which patterns of engagement
            predict renewal, which stakeholders matter, which interventions move accounts from amber to green,
            which campaigns turn ordinary relationships into expansion.
          </p>
          <p>
            For the first time, a team can benchmark its own work across every client, every project, and
            every stakeholder. And put a number on the value of client service it has never been able to
            quantify before. Every meeting, every email, every outcome makes the brain sharper, not just
            for the account it came from, but for every account the company runs.
          </p>
        </div>

        <div class="kz-essay-tech">
          <div class="row"><span class="num">02</span><h3>Semantic understanding of the relationship.</h3></div>
          <p>
            Kaizan unlocks the value in your most valuable data set, every interaction with clients, vendors,
            partners and internally. To Kaizan, those are the raw materials of something alive: a relationship,
            with history, mood, sentiment, stakeholders, and silences that say more than any reply. The brain
            has memory, and understands that the procurement lead who went quiet on Slack is the same person
            who pushed back on pricing three quarters ago and the same person whose boss just changed on LinkedIn.
            It sees the shape of the account across
            <strong>Client Satisfaction on the work being done, Activity with stakeholders, Relationship strength,
            and Expansion opportunities &mdash; the CARE framework</strong> &mdash; which updates every second
            and gives Agents context in which to act.
          </p>
        </div>

        <div class="kz-essay-tech">
          <div class="row"><span class="num">03</span><h3>Agentic execution.</h3></div>
          <p>
            People pointing and clicking UIs is evolving. The best account manager in any firm has never
            been the one with the best dashboard. The future is interacting with AI Helpers conversationally
            as they go off and complete tasks with context beyond what the person has ever had available to them.
            Kaizan&rsquo;s AI Helpers don&rsquo;t just observe and report &mdash; they act and do the work.
            They surface a stakeholder gap and draft the outreach. They prep the brief before the meeting and
            write the follow-up after it. They flag the account at risk and propose the intervention.
            <strong>Signal → Work → Completion</strong>, run continuously, so that human judgement is spent
            where it matters and everything else gets handled.
          </p>
        </div>

        <div class="kz-essay-tech">
          <p>
            The result is a platform that doesn&rsquo;t just store client data, it reasons about relationships,
            executes on the team&rsquo;s behalf, and gives you the ability to offer clients what they crave,
            that their account is being worked on 24/7 by an all-knowing team of Client Service Managers and
            their AI Helpers.
          </p>
          <p style="margin-top:18px;">
            In knowledge centric industries and an AI-native economy, the work itself gets cheaper. Judgement
            about which clients to serve, how to serve them, and what great actually looks like becomes the
            entire game. The ones that keep it in their people&rsquo;s heads will get commoditised.
            The company that turns that judgement into infrastructure will compound an asset their competitors
            can&rsquo;t see.
          </p>
          <div class="kz-essay-pull" style="font-size:26px;margin-top:24px;">
            Welcome to the era of always-on elite client service.
          </div>
        </div>

        <div class="kz-essay-sign-off">— Glen &amp; Pravin</div>
      </div>
    </article>

    <!-- CTA banner -->
    <section class="kz-about-cta">
      <div class="kz-about-cta-card">
        <div class="kz-eyebrow" style="color:rgba(10,10,10,.6);">If this resonates</div>
        <h2 class="head">Run a services business? Want to help us build this?</h2>
        <p class="sub">
          The best conversations we have are with operators who already feel the problem in their bones &mdash;
          and the best hires we&rsquo;ve made come from the same place.
        </p>
        <div class="kz-flex" style="gap:12px;flex-wrap:wrap;">
          <a class="btn" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book time with Glen →</a>
          <!-- TODO: re-enable "See open roles" once careers content is ready.
          <a class="btn" href="../careers/" style="background:transparent;color:#0A0A0A;border:1px solid #0A0A0A;">See open roles →</a>
          -->
        </div>
      </div>
    </section>

    <!-- INVESTORS -->
    <section class="kz-investors">
      <div class="kz-investors-grid">
        <div>
          <div class="kz-eyebrow">Investors</div>
          <h2 class="kz-h2" style="margin-top:10px;">Backed by people who&rsquo;ve lived it.</h2>
          <div class="kz-investors-logos">
            <div class="cell"><img src="../assets/img/inv-pembroke.png" alt="Pembroke VCT"></div>
            <div class="cell"><img src="../assets/img/inv-velocity.png" alt="Velocity Capital"></div>
            <div class="cell"><img src="../assets/img/inv-repeat.svg" alt="Repeat Ventures"></div>
          </div>
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('About', 1,
                     'Founder’s Letter from Glen Calvert, Co-founder & CEO of Kaizan. A proactive system of intelligence for client service.') + body + page_foot()


def render_404() -> str:
    body = f'''
    {nav_html(0)}
    <section class="kz-404">
      <div class="num">404</div>
      <div class="head">That page got distracted by a client.</div>
      <div class="sub">The link you followed isn&rsquo;t here. Try the homepage, or one of the main sections below.</div>
      <div class="kz-flex" style="gap:12px;margin-top:14px;">
        <a class="kz-btn kz-btn-yellow" href="index.html">Back to home</a>
        <a class="kz-btn kz-btn-ghost" href="product/">Product</a>
        <a class="kz-btn kz-btn-ghost" href="customers/">Clients</a>
        <a class="kz-btn kz-btn-ghost" href="about/">About</a>
      </div>
    </section>
    {footer_html(0)}
    '''
    return page_head('Not found', 0, 'Page not found.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# INTEGRATIONS
# ─────────────────────────────────────────────────────────────────────

# Brand SVG marks for connector logos. Compact reproductions; not exact.
INT_LOGOS = {
    'teams': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="2" y="10" width="26" height="28" rx="3" fill="#5059C9"/><text x="15" y="32" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#fff" text-anchor="middle">T</text><circle cx="36" cy="16" r="6" fill="#7B83EB"/><rect x="28" y="20" width="18" height="20" rx="3" fill="#7B83EB"/><text x="37" y="35" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#fff" text-anchor="middle">T</text></svg>''',
    'claude': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="4" width="40" height="40" rx="8" fill="#D97757"/><path d="M16 32 l5 -16 h2.5 l5 16 h-2.6 l-1.2 -4 h-4.9 l-1.2 4 z M20.5 26 h3.6 l-1.8 -6 z M30 32 v-16 h2.5 v16 z" fill="#FFFBF0"/></svg>''',
    'slack': '''<svg viewBox="0 0 48 48" width="44" height="44"><g><rect x="6" y="20" width="14" height="6" rx="3" fill="#36C5F0"/><rect x="20" y="20" width="6" height="14" rx="3" fill="#2EB67D"/><rect x="22" y="6" width="6" height="14" rx="3" fill="#ECB22E"/><rect x="28" y="22" width="14" height="6" rx="3" fill="#E01E5A"/><rect x="22" y="28" width="6" height="14" rx="3" fill="#36C5F0"/><rect x="6" y="28" width="6" height="6" rx="3" fill="#2EB67D"/><rect x="36" y="14" width="6" height="6" rx="3" fill="#ECB22E"/><rect x="20" y="36" width="6" height="6" rx="3" fill="#E01E5A"/></g></svg>''',
    'hubspot': '''<svg viewBox="0 0 48 48" width="44" height="44"><circle cx="34" cy="24" r="9" fill="none" stroke="#FF7A59" stroke-width="3"/><circle cx="34" cy="24" r="2.5" fill="#FF7A59"/><line x1="34" y1="15" x2="34" y2="9" stroke="#FF7A59" stroke-width="3"/><circle cx="34" cy="7" r="3" fill="#FF7A59"/><line x1="26" y1="20" x2="14" y2="14" stroke="#FF7A59" stroke-width="3"/><circle cx="12" cy="13" r="3.5" fill="#FF7A59"/><line x1="26" y1="28" x2="14" y2="34" stroke="#FF7A59" stroke-width="3"/><circle cx="12" cy="35" r="3.5" fill="#FF7A59"/></svg>''',
    'salesforce': '''<svg viewBox="0 0 48 48" width="44" height="44"><path d="M14 28 q-6 0 -6 -6 q0 -5 5 -6 q1 -5 7 -5 q4 0 6 3 q3 -3 7 -3 q7 0 9 7 q4 1 4 5 q0 5 -5 6 q-2 4 -7 4 q-3 0 -5 -2 q-2 3 -7 3 q-5 0 -7 -3 q-1 1 -1 1 z" fill="#00A1E0"/></svg>''',
    'gmeet': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="6" y="14" width="22" height="20" rx="3" fill="#00832D"/><path d="M28 21 l8 -5 v16 l-8 -5 z" fill="#00AC47"/><rect x="28" y="14" width="6" height="6" fill="#FFBA00"/><rect x="28" y="28" width="6" height="6" fill="#EA4335"/></svg>''',
    'gdrive': '''<svg viewBox="0 0 48 48" width="44" height="44"><path d="M18 8 h12 l12 22 h-12 z" fill="#FFCF63"/><path d="M18 8 l-12 22 h12 l6 -11 z" fill="#0066DA"/><path d="M6 30 l6 10 h24 l6 -10 h-12 l-6 11 h-12 z" fill="#00AC47"/></svg>''',
    'monday': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="18" width="12" height="12" rx="6" fill="#FF3D57"/><rect x="18" y="18" width="12" height="12" rx="6" fill="#FFCB00"/><rect x="32" y="18" width="12" height="12" rx="6" fill="#00CA72"/></svg>''',
    'sharepoint': '''<svg viewBox="0 0 48 48" width="44" height="44"><circle cx="18" cy="20" r="10" fill="#03787C"/><circle cx="30" cy="26" r="10" fill="#28A8EA"/><circle cx="38" cy="34" r="6" fill="#0078D4"/><text x="18" y="24" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="#fff" text-anchor="middle">S</text></svg>''',
    'zoom': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="14" width="28" height="20" rx="4" fill="#2D8CFF"/><path d="M32 22 l10 -6 v16 l-10 -6 z" fill="#2D8CFF"/></svg>''',
    'wrike': '''<svg viewBox="0 0 48 48" width="44" height="44"><circle cx="24" cy="24" r="18" fill="#08C"/><text x="24" y="30" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#fff" text-anchor="middle">W</text></svg>''',
    'kzapi': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="4" width="40" height="40" rx="10" fill="#0A0A0A"/><path d="M14 18 l-5 6 l5 6 M34 18 l5 6 l-5 6 M22 32 l4 -16" stroke="#FFB900" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
    'gmail': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="10" width="40" height="28" rx="3" fill="#fff" stroke="rgba(0,0,0,.15)"/><path d="M4 12 L24 28 L44 12" stroke="#EA4335" stroke-width="3" fill="none"/><path d="M4 12 L4 38" stroke="#4285F4" stroke-width="3" fill="none"/><path d="M44 12 L44 38" stroke="#34A853" stroke-width="3" fill="none"/></svg>''',
    'outlook': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="8" width="28" height="32" rx="3" fill="#0078D4"/><text x="18" y="32" font-family="Arial,sans-serif" font-size="22" font-weight="700" fill="#fff" text-anchor="middle">O</text><rect x="32" y="14" width="12" height="20" fill="#106EBE"/></svg>''',
    'jira': '''<svg viewBox="0 0 48 48" width="44" height="44"><path d="M24 6 L42 24 L24 42 L6 24 Z" fill="#2684FF"/><path d="M24 14 L34 24 L24 34 L14 24 Z" fill="#fff" opacity=".75"/></svg>''',
    'asana': '''<svg viewBox="0 0 48 48" width="44" height="44"><circle cx="24" cy="14" r="7" fill="#F06A6A"/><circle cx="14" cy="32" r="7" fill="#F06A6A"/><circle cx="34" cy="32" r="7" fill="#F06A6A"/></svg>''',
    'clickup': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="4" width="40" height="40" rx="10" fill="#7B68EE"/><path d="M14 30 L24 20 L34 30" stroke="#fff" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
    'notion': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="4" width="40" height="40" rx="8" fill="#fff" stroke="rgba(0,0,0,.18)"/><path d="M16 14 L16 34 M16 14 L30 34 M30 14 L30 34" stroke="#0A0A0A" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
}

INT_DATA = [
    dict(k='teams',     name='Microsoft Teams', cat='Conversations', why='Capture meeting transcripts and chat threads automatically.'),
    dict(k='claude',    name='Claude',          cat='Model provider', why='Frontier reasoning powers CARE, briefings and reply drafts.'),
    dict(k='slack',     name='Slack',           cat='Conversations', why='Surface unanswered client messages and route them to an owner.'),
    dict(k='hubspot',   name='HubSpot',         cat='CRM',           why='Two-way sync: deals, contacts, notes, activity, custom properties.'),
    dict(k='salesforce',name='Salesforce',      cat='CRM',           why='Bidirectional sync; CARE score writes back to the Account object.'),
    dict(k='gmeet',     name='Google Meet',     cat='Conversations', why='Recordings and transcripts ingested the moment a call ends.'),
    dict(k='gdrive',    name='Google Drive',    cat='Knowledge',     why='Briefs, decks and notes indexed and joined to the right account.'),
    dict(k='monday',    name='Monday',          cat='Delivery',      why='Project status and blockers feed into account health signals.'),
    dict(k='sharepoint',name='SharePoint',      cat='Knowledge',     why='Enterprise document libraries linked to the accounts they support.'),
    dict(k='zoom',      name='Zoom',            cat='Conversations', why='Cloud recordings and transcripts ingested and attributed to accounts.'),
    dict(k='wrike',     name='Wrike',           cat='Delivery',      why='Tasks, milestones and project status join the account timeline.'),
    dict(k='gmail',     name='Gmail',           cat='Conversations', why='Inbound and outbound client email threaded into the account record.'),
    dict(k='outlook',   name='Outlook',         cat='Conversations', why='Microsoft 365 mail and calendar joined to the unified client timeline.'),
    dict(k='jira',      name='Jira',            cat='Delivery',      why='Issues, sprints and release status surfaced as account signals.'),
    dict(k='asana',     name='Asana',           cat='Delivery',      why='Project tasks and milestones feed delivery health for every client.'),
    dict(k='clickup',   name='ClickUp',         cat='Delivery',      why='Workspaces, tasks and docs threaded into the account timeline.'),
    dict(k='notion',    name='Notion',          cat='Knowledge',     why='Workspaces, docs and databases threaded into the right account record.'),
]


def render_integrations() -> str:
    tiles = '\n'.join(
        f'''<a class="kz-int-tile" href="#">
          <div class="logo">{INT_LOGOS.get(i["k"], "")}</div>
          <div class="meta"><div class="name">{E(i["name"])}</div>
            <div class="cat">{E(i["cat"].upper())}</div></div>
          <p class="why">{E(i["why"])}</p>
        </a>''' for i in INT_DATA
    )

    custom_cards = '\n'.join(
        f'<div class="kz-int-custom-card"><div class="lbl">{E(t)}</div><div class="d">{E(d)}</div></div>'
        for t, d in [
            ('CLIENT INTELLIGENCE', 'Pipe your data warehouse, BI stack and proprietary scoring into the CARE engine.'),
            ('WORKFLOW AUTOMATION', 'Trigger downstream actions in your delivery, billing and resourcing systems.'),
            ('AUTONOMOUS GROWTH', 'Connect agents to your account-planning, forecasting and outbound playbooks.'),
            ('INTERNAL AI', 'Embed Kaizan inside the AI platforms and copilots your team already uses.'),
        ]
    )

    body = f'''
    {nav_html(1, active='Integrations')}

    <!-- HERO -->
    <section class="kz-section-tight" style="padding-top:60px;">
      <div class="kz-eyebrow">Integrations</div>
      <h1 class="kz-h1" style="margin-top:18px;max-width:1100px;">
        The tools your client teams already use - unify your data.
      </h1>
      <p class="kz-lede" style="margin-top:18px;max-width:760px;">
        Kaizan reads from the systems where work actually happens, and builds a continuous memory on every client.
        <strong style="color:var(--kz-ink);font-weight:600;">All standard integrations are free.</strong>
        They automatically capture every meeting, message, doc and ticket — and assign the context
        to the right client, the right account, the right user. No new dashboard for the team to log into.
        No data left stranded.
      </p>
      <div class="kz-int-meta">
        <span><span class="kz-dot"></span> <strong>2-way sync</strong> on CRMs</span>
        <span><span class="kz-dot"></span> <strong>Read &amp; Write</strong> on conversation tools</span>
        <span><span class="kz-dot"></span> <strong>OAuth 2.0</strong> · revoke anytime</span>
      </div>
    </section>

    <!-- STANDARD GRID -->
    <section class="kz-int-grid-section">
      <div class="kz-int-grid-head">
        <h2 class="kz-h2" style="font-size:32px;">Standard</h2>
      </div>
      <div class="kz-int-grid">{tiles}</div>
    </section>

    <!-- KAIZAN API FEATURED -->
    <section class="kz-int-grid-section">
      <div class="kz-int-grid-head">
        <h2 class="kz-h2" style="font-size:32px;">Featured</h2>
        <span class="kz-eyebrow">BUILD YOUR OWN</span>
      </div>
      <div class="kz-int-api">
        <div class="logo-large">{INT_LOGOS["kzapi"]}</div>
        <div>
          <div class="kz-eyebrow" style="color:var(--kz-yellow);">BUILD YOUR OWN SOLUTIONS</div>
          <h3 class="head">Kaizan API</h3>
          <p class="lede">Leverage all your unified client intelligence — every meeting, every signal,
            every score — in your own systems and agents. SOC 2 logged, two-way sync, scoped per tenant.</p>
        </div>
        <div class="actions">
          <a class="kz-btn kz-btn-yellow" style="padding:12px 20px;font-size:14px;white-space:nowrap;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Talk to us</a>
        </div>
      </div>
      <h3 class="kz-h3" style="margin-top:32px;font-size:24px;max-width:880px;">
        Contact Kaizan to understand the full suite of integrations available.
      </h3>
    </section>

    <!-- CUSTOM INTEGRATIONS -->
    <section class="kz-int-custom">
      <div class="kz-int-custom-card-outer">
        <div class="left">
          <div class="kz-eyebrow">Forward-deployed engineering</div>
          <h2 class="kz-h2" style="font-size:44px;margin:12px 0 18px;line-height:1.05;">
            Custom <span class="kz-mark kz-mark-tight">integrations</span>
          </h2>
          <p class="kz-lede" style="font-size:16px;max-width:560px;">
            Leverage Kaizan&rsquo;s forward deployed engineers to integrate your AI Helpers and AI platform
            with your internal systems — for more client intelligence, workflow automation and autonomous
            client growth.
          </p>
          <div class="kz-flex" style="margin-top:26px;">
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;font-size:14px;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book demo →</a>
          </div>
        </div>
        <div class="right">{custom_cards}</div>
      </div>
    </section>

    <!-- REQUEST CTA -->
    <section class="kz-int-request">
      <div class="card">
        <div>
          <div class="kz-eyebrow" style="color:rgba(10,10,10,.6);">DON&rsquo;T SEE YOUR TOOL?</div>
          <h3 class="head">We&rsquo;ll build it for design partners.</h3>
          <p>If you&rsquo;re an enterprise and your stack includes a tool we don&rsquo;t support yet — tell us.
            We&rsquo;ve shipped two new connectors per quarter for the last year.</p>
        </div>
        <a class="kz-btn kz-btn-black" style="padding:16px 26px;font-size:15px;white-space:nowrap;" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">
          Request an integration →
        </a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Integrations', 1,
                     'Native connectors for Microsoft Teams, Slack, HubSpot, Salesforce, Google Meet '
                     'and more — plus the Kaizan API.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# PRICING
# ─────────────────────────────────────────────────────────────────────

PRICING_TIERS = [
    dict(name='Team', clients='Up to ', clients_bold='30 clients',
         price='£3,495', price_label='per month',
         per_client='Equivalent to £117 / client pm',
         eyebrow='EVERYTHING YOU GET',
         bullets=[
             ('Unlimited users', ''),
             ('Meeting Assistant', ' — joins every meeting, captures notes, actions and decisions'),
             ('All integrations', ' — calls, emails, chat, workspaces, CRM, project management'),
             ('Client Intelligence Platform', ' — unified comms, stakeholder intel, health scores, market intel, SWOTs'),
             ('API', ' — leverage your unified client data'),
             ('MCP', ' — access your data in your LLM of choice'),
             ('Dedicated Account Manager', ''),
         ]),
    dict(name='Growth', sweet=True, clients='Up to ', clients_bold='75 clients',
         price='£5,995', price_label='per month',
         per_client='Equivalent to £80 / client pm',
         eyebrow='EVERYTHING IN TEAM, PLUS',
         bullets=[
             ('2.5× the portfolio', ' — up to 75 accounts'),
             ('Guided onboarding', ' with CARE calibration'),
             ('Priority support', ' & quarterly value reviews'),
         ]),
    dict(name='Scale', clients='Up to ', clients_bold='150 clients',
         price='£9,995', price_label='per month',
         per_client='Equivalent to £67 / client pm',
         eyebrow='EVERYTHING IN GROWTH, PLUS',
         bullets=[
             ('2× the portfolio', ' — up to 150 accounts'),
             ('Multi-team segmentation', ' across practices'),
             ('Custom AI Helpers', ' — talk to us for pricing'),
         ]),
    dict(name='Enterprise', clients='', clients_bold='150+ clients',
         clients_trail=' & custom work',
         price='Let’s talk', price_label='Custom annual',
         per_client='Built around your network',
         eyebrow='EVERYTHING IN SCALE, PLUS',
         bullets=[
             ('Unlimited portfolio scale', ' across multi-office, multi-region'),
             ('API + MCP custom', ' — extended access & rate limits'),
             ('Custom integrations & bespoke builds', ' scoped to your requirements'),
             ('SSO/SAML, custom retention', ' & data residency'),
             ('Custom CARE calibration', ' per practice'),
         ]),
]

PRICING_HELPERS = [
    dict(tag='AI ASSISTANT', name='For the Team',
         sub='Joins every meeting, knows every client conversation, drafts what you need and updates your tools — accessed through your LLM of choice.',
         features=['LLM of choice', 'Auto-updates CRM & PM', 'Search all unified data']),
    dict(tag='AI HELPER', name='Client ROI',
         sub='Proactively increase the ROI on every client by turning conversations, emails and project activity into demonstrable value.',
         features=['Auto-built QBR decks', 'Value-gap alerts', 'Renewal risk scoring']),
    dict(tag='AI HELPER', name='Relationships',
         sub='Grow CSAT with proactive recommendations — Kaizan flags weakening relationships before they cost you a renewal.',
         features=['Disengagement flags', 'Stakeholder coverage maps', 'Drafted re-engagement']),
    dict(tag='AI HELPER', name='Expansion',
         sub='Maximise client revenue with continuous market research, drafted outbound, and solutions matched to each client’s stated objectives.',
         features=['Continuous market research', 'Drafted outbound', 'Solutions matched to objectives']),
]


def render_pricing() -> str:
    def tier_card(t):
        bullets = '\n'.join(
            f'<li><span class="arr">→</span><span><b>{E(b[0])}</b>{E(b[1])}</span></li>'
            for b in t['bullets']
        )
        trail = f'<span class="trail">{E(t["clients_trail"])}</span>' if t.get('clients_trail') else ''
        ribbon = '<div class="ribbon">Sweet spot</div>' if t.get('sweet') else ''
        return f'''<div class="kz-tier{' is-sweet' if t.get('sweet') else ''}">
          {ribbon}
          <div class="name">{E(t["name"])}</div>
          <div class="clients">{E(t["clients"])}<div class="bold">{E(t["clients_bold"])}{trail}</div></div>
          <div class="rule"></div>
          <div class="price">
            <div class="line">{E(t["price"])}</div>
            <div class="label">{E(t["price_label"])}</div>
            <div class="per">{E(t["per_client"])}</div>
          </div>
          <div class="rule"></div>
          <div class="eyebrow">{E(t["eyebrow"])}</div>
          <ul class="bullets">{bullets}</ul>
        </div>'''
    tiers_html = '\n'.join(tier_card(t) for t in PRICING_TIERS)

    helpers_rows = '\n'.join(
        f'''<div class="kz-included-row">
          <div class="tag">{E(h["tag"])}</div>
          <div class="body">
            <div class="name">{E(h["name"])}</div>
            <div class="sub">{E(h["sub"])}</div>
          </div>
          <div class="features">{' '.join(f'<span>{E(f)}</span>' for f in h["features"])}</div>
        </div>''' for h in PRICING_HELPERS
    )

    body = f'''
    {nav_html(1, active='Pricing')}

    <!-- HERO -->
    <section class="kz-section-tight" style="padding-top:60px;">
      <div class="kz-eyebrow">Pricing</div>
      <h1 class="kz-h1 kz-h1-xl" style="margin-top:18px;max-width:1100px;">
        Pay for clients we <span class="kz-mark">manage and grow</span>.
      </h1>
      <p class="kz-lede" style="margin-top:22px;max-width:760px;">
        Priced by the size of the portfolio Kaizan covers. <strong style="color:var(--kz-ink);font-weight:600;">Unlimited users</strong> &amp; the full product on every tier.
      </p>
    </section>

    <!-- TIER CARDS -->
    <section class="kz-section" style="padding-top:8px;">
      <div class="kz-pricing-tiers">{tiers_html}</div>
      <p class="kz-pricing-fine">
        All prices GBP, annual commit. Monthly billing available at 10% uplift.
        Fair-use limits on storage, API calls and integration volumes — full thresholds in your contract.
        Custom AI Helpers, custom integrations and bespoke engineering quoted separately.
      </p>
    </section>

    <!-- INCLUDED IN EVERY TIER (stacked rows, vertical shape) -->
    <section class="kz-section">
      <div class="kz-eyebrow">Included in every tier</div>
      <h2 class="kz-h2" style="margin-top:10px;max-width:820px;">
        One AI Assistant and three AI Helpers, working across every account.
      </h2>
      <div class="kz-included-list">{helpers_rows}</div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Pricing', 1,
                     'Priced by the size of the client portfolio Kaizan covers. Unlimited users on every tier.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# SECURITY (Trust Centre)
# ─────────────────────────────────────────────────────────────────────

SECURITY_DATA = [
    dict(title='Security', tabs=[
        dict(k='accreditations', icon='🏅', label='Accreditations',
             desc='Your trust is imperative to us. Kaizan is SOC 2 certified and an approved integration partner with Microsoft & Google workspaces so you can be sure your company’s data is in good hands. Our Trust Centre provides up to date info on the status of our accreditations.',
             visual='badges'),
        dict(k='protection', icon='🛡', label='Protection',
             desc='AES-256 at rest, TLS 1.2+ in transit, per-tenant encryption keys in AWS KMS. Optional customer-managed keys (BYOK) on Enterprise. Quarterly third-party penetration tests with summaries available under NDA.',
             visual='protection'),
        dict(k='access', icon='🔑', label='Access',
             desc='Engineers do not have routine access to client data. Production access is explicit, time-bounded, logged in an immutable audit trail, and reviewed weekly. SSO + SCIM enforced on Growth and Enterprise plans, with role-based permissions and customer-configurable retention.',
             visual='access'),
    ]),
    dict(title='Privacy', tabs=[
        dict(k='compliance', icon='⚖', label='Compliance',
             desc='Kaizan complies with leading industry standards and regulations, including SOC 2, GDPR, and the EU-U.S. Data Privacy Framework. Regular audits and third-party assessments help us maintain and improve our security posture.',
             visual='trust-center'),
        dict(k='policy', icon='📄', label='Policy',
             desc='Plain-English Data Processing Agreement and privacy policy, reviewed quarterly. Material changes are notified to enterprise customers 30 days in advance with the right to object. Standard MNDA turnaround typically under 24 hours.',
             visual='policy'),
        dict(k='consent', icon='👍', label='Consent',
             desc='Granular consent surfaces inside the product. Account managers and clients can review what data Kaizan holds about a relationship and request deletion at any time. Per-meeting opt-outs supported via calendar invite tags.',
             visual='consent'),
    ]),
    dict(title='AI', tabs=[
        dict(k='isolation', icon='🗄', label='Data Isolation',
             desc='Your data is not used for training AI models. We ensure complete isolation of customer data from the data sets used to develop, enhance and deliver our AI capabilities.',
             visual='isolation'),
        dict(k='governance', icon='🧭', label='Model Governance',
             desc='Every model in production is risk-rated, version-controlled and monitored. New models go through pre-launch evaluations covering accuracy, bias, refusal behaviour and prompt-injection resistance. Audit logs of model decisions are retained per your retention policy.',
             visual='governance'),
        dict(k='training', icon='🔑', label='Model Training',
             desc='Kaizan does not aggregate client data to train shared or foundation models. Per-tenant fine-tuning, when explicitly enabled, stays scoped to that tenant and is deleted on contract end. Zero-retention API contracts with OpenAI and Anthropic.',
             visual='training'),
    ]),
]


def security_visual(kind: str) -> str:
    if kind == 'badges':
        badges = [('AICPA','SOC 2','#3B82F6'), ('ISO','27001','#FFFFFF'),
                  ('GDPR','EU/UK','#0046AB'), ('ADA','Verified','#10B981'),
                  ('CCPA','','#3B82F6')]
        return '<div class="kz-secvis kz-secvis-badges">' + ''.join(
            f'<div class="badge" style="background:{c};color:{"#0A0A0A" if c == "#FFFFFF" else "#fff"};">'
            f'<div>{E(l)}</div>' + (f'<div class="sub">{E(s)}</div>' if s else '') + '</div>'
            for l, s, c in badges
        ) + '</div>'
    if kind == 'protection':
        rows = [('TLS 1.2+', 'Every request, every region'),
                ('AES-256', 'Per-tenant keys in AWS KMS'),
                ('BYOK', 'Customer-managed keys on Enterprise'),
                ('Pen test', 'Quarterly third-party')]
        return ('<div class="kz-secvis kz-secvis-grid">'
                '<div class="lbl">ENCRYPTION · IN TRANSIT &amp; AT REST</div>'
                '<div class="grid">'
                + ''.join(f'<div class="cell"><div class="k">{E(k)}</div><div class="v">{E(v)}</div></div>'
                          for k, v in rows) +
                '</div></div>')
    if kind == 'access':
        rows = [('12:04:18','admin@verkeer.com','role.update','kz-care-001 → manager'),
                ('12:04:09','jdoe@adimo.io','session.start','sso · okta'),
                ('12:03:55','sec-bot','access.review','weekly · ok'),
                ('12:03:41','priya@jellyfish.com','export.audit','180 events · csv'),
                ('12:03:22','ops@kaizan.ai','access.granted','ttl 30m · ticket #4218')]
        return ('<div class="kz-secvis kz-secvis-log">'
                '<div class="lbl">AUDIT LOG · LAST 60 SECONDS</div>'
                + ''.join(f'<div class="row"><span class="t">{E(t)}</span>'
                          f'<span class="who">{E(who)}</span>'
                          f'<span class="ev">{E(ev)}</span>'
                          f'<span class="d">{E(d)}</span></div>'
                          for t, who, ev, d in rows) +
                '</div>')
    if kind == 'trust-center':
        cols = [('Risk Profile', [('Data access','Restricted'),('Impact','Moderate'),('RTO','8 hours')]),
                ('Product Security', [('Audit logging','✓'),('Data Privacy','✓'),('Integrations','✓')]),
                ('Reports', [('SOC 2 Type II','PDF'),('Pen test','PDF'),('Questionnaire','PDF')]),
                ('Self-Assessments', [('SIG Lite','✓'),('CAIQ','✓'),('VSA','✓')]),
                ('Data Security', [('Access mon.','✓'),('Backups','✓'),('Erasure','✓')]),
                ('App Security', [('Bot Detection','✓'),('Vuln Mgmt','✓'),('WAF','✓')])]
        return ('<div class="kz-secvis kz-secvis-trust">'
                '<div class="head"><span>KAIZAN · TRUST CENTER</span><span>SHARE · SUBSCRIBE</span></div>'
                '<div class="grid">'
                + ''.join('<div class="card">'
                          f'<div class="t">{E(t)}</div>'
                          + ''.join(f'<div class="r"><span>{E(k)}</span><span class="v">{E(v)}</span></div>'
                                    for k, v in rows) +
                          '</div>' for t, rows in cols)
                + '</div></div>')
    if kind == 'policy':
        rows = [('Data Processing Agreement', 'Standard DPA · MNDA in <24h'),
                ('Privacy Policy', 'Plain English · reviewed quarterly'),
                ('Sub-processor list', '8 vendors · 30-day notice on change'),
                ('Retention', '30 days → 7 years · configurable'),
                ('Right to erasure', 'Self-serve in product · within 30 days')]
        return ('<div class="kz-secvis kz-secvis-policy">'
                '<div class="lbl">POLICY · v4.2 · APR 2026</div>'
                + ''.join(f'<div class="row"><span class="k">{E(k)}</span>'
                          f'<span class="v">{E(v)}</span></div>'
                          for k, v in rows) +
                '</div>')
    if kind == 'consent':
        rows = [('Meeting transcripts', '142 calls · last 12 months', True),
                ('Email threads', '218 threads · last 90 days', True),
                ('CRM signals', 'HubSpot · open + closed deals', True),
                ('Slack channels', 'Excluded by allow-list', False)]
        return ('<div class="kz-secvis kz-secvis-consent">'
                '<div class="lbl">CONSENT · ANYTHING IS POSSIBLE LTD</div>'
                '<div class="card"><div class="title">What Kaizan holds for this client</div>'
                + ''.join('<div class="row">'
                          f'<div><div class="k">{E(k)}</div><div class="v">{E(v)}</div></div>'
                          f'<div class="toggle{" is-on" if on else ""}"></div></div>'
                          for k, v, on in rows) +
                '</div></div>')
    if kind == 'isolation':
        return '''<div class="kz-secvis kz-secvis-iso"><div class="lbl">CUSTOMER DATA · ISOLATED PER TENANT</div>
          <div class="legend">
            <span class="sw" style="background:#A6C8E8;"></span>Tenant A
            <span class="sw" style="background:#FFD580;"></span>Tenant B
            <span class="sw" style="background:#A8E6C0;"></span>Tenant C
            <span class="sw" style="background:#F4A6A6;"></span>Tenant D
            <span class="sw" style="background:#C9A6E8;"></span>Tenant E
          </div>
          <div class="bars">
          ''' + ''.join(
            f'<div class="bar"><div class="seg" style="background:#A6C8E8;height:{40+i*4}%"></div>'
            f'<div class="seg" style="background:#FFD580;height:{20-i}%"></div>'
            f'<div class="seg" style="background:#A8E6C0;height:{15+i}%"></div>'
            f'<div class="seg" style="background:#F4A6A6;height:{10}%"></div>'
            f'<div class="seg" style="background:#C9A6E8;height:{15}%"></div>'
            f'<div class="x">Apr {24+i}</div></div>' for i in range(7)
        ) + '</div></div>'
    if kind == 'governance':
        rows = [('kz-care-summary', 'GPT-4o · zero retention', 'low', '99.4%'),
                ('kz-risk-classifier', 'Claude 3.7 · zero retention', 'low', '97.8%'),
                ('kz-expansion-rank', 'Claude 3.7 · zero retention', 'medium', '94.1%'),
                ('kz-draft-followup', 'GPT-4o · zero retention', 'medium', '92.6%')]
        return ('<div class="kz-secvis kz-secvis-gov">'
                '<div class="lbl">MODELS IN PRODUCTION · RISK-RATED</div>'
                + ''.join(f'<div class="row"><span class="m">{E(m)}</span>'
                          f'<span class="d">{E(d)}</span>'
                          f'<span class="lvl is-{lvl}">{E(lvl.upper())}</span>'
                          f'<span class="acc">{E(acc)}</span></div>'
                          for m, d, lvl, acc in rows) +
                '</div>')
    if kind == 'training':
        return '''<div class="kz-secvis kz-secvis-train">
          <div class="boxes">
            <div class="box">
              <div class="t">YOUR DATA</div>
              <div class="s1">Per-tenant · isolated</div>
              <div class="s2">Encrypted · BYOK optional</div>
            </div>
            <div class="link">
              <div class="cross">×</div>
              <div class="cap">NEVER USED FOR TRAINING</div>
            </div>
            <div class="box">
              <div class="t">FOUNDATION MODELS</div>
              <div class="s1">OpenAI · Anthropic</div>
              <div class="s2">Zero-retention API</div>
            </div>
          </div>
        </div>'''
    return ''


def render_security() -> str:
    sections_html = []
    for sec_idx, sec in enumerate(SECURITY_DATA):
        tabs_html = '\n'.join(
            f'''<button type="button" class="kz-sec-tab{' is-active' if i == 0 else ''}"
              data-sec-tab data-sec-target="sec-{sec_idx}-{t['k']}">
              <span class="ic">{t['icon']}</span>
              <span class="lbl">{E(t['label'])}</span>
              <p class="desc">{E(t['desc'])}</p>
            </button>''' for i, t in enumerate(sec['tabs'])
        )
        visuals_html = '\n'.join(
            f'<div class="kz-sec-visual{" is-active" if i == 0 else ""}" id="sec-{sec_idx}-{t["k"]}">{security_visual(t["visual"])}</div>'
            for i, t in enumerate(sec['tabs'])
        )
        sections_html.append(f'''
        <section class="kz-sec-section" data-sec-group="{sec_idx}">
          <h2 class="kz-h2">{E(sec['title'])}</h2>
          <div class="kz-sec-grid">
            <div class="kz-sec-stage">{visuals_html}</div>
            <div class="kz-sec-tabs">{tabs_html}</div>
          </div>
        </section>''')

    body = f'''
    {nav_html(1, active='Security')}

    <section class="kz-section-tight" style="padding-top:60px;">
      <div class="kz-eyebrow">Trust Centre · Last reviewed April 2026</div>
      <h1 class="kz-h1" style="margin-top:18px;max-width:1100px;">Your data, in safe hands.</h1>
      <p class="kz-lede" style="margin-top:18px;max-width:780px;">
        Kaizan listens to client conversations. That is a serious responsibility. Below: how we secure
        your data, how we handle privacy, and how we govern the AI behind the product.
      </p>
    </section>

    {''.join(sections_html)}

    <section class="kz-text-center" style="padding:80px 56px;">
      <a class="kz-btn kz-btn-black" style="padding:18px 28px;font-size:16px;" href="#">Visit our Trust Centre →</a>
    </section>

    {footer_html(1)}
    '''
    return page_head('Security & Trust', 1,
                     'How Kaizan secures your data, handles privacy, and governs the AI behind the product.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# CAREERS
# ─────────────────────────────────────────────────────────────────────

CAREERS_VALUES = [
    ('01', 'High bar, low ego.',
     'We hire slowly. We give feedback directly. We assume good intent and we read carefully before reacting. Nobody wins points for being the loudest in the room.'),
    ('02', 'Make the user better.',
     'Every feature is judged by whether it makes the account manager visibly better at their job. If it just makes them faster at busywork we already disagree with, we cut it.'),
    ('03', 'Ship to ship again.',
     'We ship every week. Small, reversible, instrumented. Big launches are a series of small wins; we do not save up.'),
    ('04', 'Write things down.',
     'We write more than most teams. Specs, decisions, retros, context for new joiners. It is how a fifteen-person team in three time zones stays aligned without meetings.'),
]

CAREERS_BENEFITS = [
    ('Salary', 'Top-of-band for our stage. We pay London market rates regardless of where you live; no geo-discount.'),
    ('Equity', 'Meaningful equity for every full-time role, with a 10-year window to exercise after you leave.'),
    ('Time off', '30 days plus public holidays. Two weeks off in August. Take Fridays in summer if it helps.'),
    ('Remote', 'Remote-first across UK + EU. We meet in person two days a quarter, expensed, somewhere good.'),
    ('Health', 'Private healthcare from day one (UK + EU). Mental health support via Spill.'),
    ('Parental', '20 weeks fully paid for primary, 10 weeks for secondary, regardless of gender or path to parenthood.'),
    ('Learning', '£2,500 a year, no approval needed. Conferences, books, courses, coaching.'),
    ('Kit', 'A new MacBook Pro and a £1,500 home setup budget on day one.'),
]

CAREERS_ROLES = [
    ('Engineering', 'Senior Full-Stack Engineer', 'London or remote (UK+EU)', 'Full-time'),
    ('Engineering', 'Founding ML Engineer', 'London', 'Full-time'),
    ('Engineering', 'Senior Backend Engineer', 'London or remote (UK+EU)', 'Full-time'),
    ('Design', 'Senior Product Designer', 'London or remote (UK+EU)', 'Full-time'),
    ('Product', 'Product Manager · Platform', 'London', 'Full-time'),
    ('Go-to-market', 'Account Executive · Mid-market', 'London', 'Full-time'),
    ('Customer', 'Customer Success Manager', 'London or remote (UK+EU)', 'Full-time'),
    ('Operations', 'Talent Partner', 'London', 'Full-time'),
]

CAREERS_PROCESS = [
    ('1', 'Intro call · 30 min',
     'A two-way conversation with someone on the team you would work with. We tell you the truth about the job; you tell us what you are looking for.'),
    ('2', 'Take-home or live work · 60–90 min',
     'We do not do whiteboard puzzles. The exercise is something close to the actual job. Paid for senior take-homes that go past 90 minutes.'),
    ('3', 'Team day · half-day onsite or remote',
     'You meet three or four people. We work through a real problem together. Lunch on us.'),
    ('4', 'References · we call yours, you call ours',
     'We talk to two or three of your former colleagues. You talk to two of ours. No surprises on either side.'),
    ('5', 'Decision · within 5 working days',
     'We commit to a decision within five working days of the team day. No silent rejections. Detailed feedback on request.'),
]


def render_careers() -> str:
    values_html = '\n'.join(
        f'<div class="kz-careers-value"><div class="num">{E(n)}</div><div class="t">{E(t)}</div><p>{E(d)}</p></div>'
        for n, t, d in CAREERS_VALUES
    )
    roles_html = '\n'.join(
        f'''<a class="kz-careers-role" href="#">
          <div class="team">{E(team)}</div>
          <div class="role">{E(role)}</div>
          <div class="loc">{E(loc)}</div>
          <div class="type">{E(t)}</div>
          <div class="apply">Apply →</div>
        </a>''' for team, role, loc, t in CAREERS_ROLES
    )
    benefits_html = '\n'.join(
        f'<div class="kz-careers-benefit"><div class="k">{E(k)}</div><div class="v">{E(v)}</div></div>'
        for k, v in CAREERS_BENEFITS
    )
    process_html = '\n'.join(
        f'<div class="kz-careers-step"><div class="num">{E(n)}</div><div class="t">{E(t)}</div><p>{E(d)}</p></div>'
        for n, t, d in CAREERS_PROCESS
    )
    stats_html = '\n'.join(
        f'<div class="kz-stat-cell"><div class="num">{E(n)}</div><div class="lbl">{E(l)}</div></div>'
        for n, l in [('15','people'), ('8','open roles'),
                     ('9.4','Glassdoor (anonymous, recent)'),
                     ('£2,500','/yr learning budget')]
    )

    body = f'''
    {nav_html(1)}

    <!-- HERO -->
    <section class="kz-section-tight" style="padding-top:60px;">
      <div class="kz-eyebrow">Careers · 8 open roles · April 2026</div>
      <h1 class="kz-h1 kz-h1-xl" style="margin-top:20px;max-width:1200px;">
        Build the AI account manager <span class="kz-mark">that never sleeps.</span>
      </h1>
      <p class="kz-lede" style="margin-top:28px;max-width:780px;">
        Fifteen people, London + remote across UK and EU, building Client Super Intelligence for
        professional services. Hiring carefully into engineering, design, product and go-to-market.
      </p>
    </section>

    <!-- STATS -->
    <section class="kz-stat-row">{stats_html}</section>

    <!-- FOUNDER NOTE -->
    <section class="kz-careers-note">
      <div class="left">
        <div class="kz-eyebrow">A note from the team</div>
        <div class="title">Why work here<br><span class="sub">From the founders</span></div>
      </div>
      <div class="right">
        <p class="pull">
          [Placeholder. Two or three sentences on why Kaizan is a good place to spend the next four years
          of your life. The kind of work, the kind of people, what you&rsquo;ll get out of it that you
          won&rsquo;t get elsewhere.]
        </p>
        <p>[Body paragraph. Talk about the team you&rsquo;re joining. Their backgrounds, what they were
          doing before, what you&rsquo;ll learn from them. Be specific. Avoid the words &ldquo;rocketship&rdquo;
          and &ldquo;10x&rdquo;.]</p>
        <p>[Second paragraph. The hard parts. What&rsquo;s genuinely difficult about working here. The
          tradeoffs. The stuff you won&rsquo;t say in the interview but will tell a friend after a pint.
          People respect honesty here more than recruiting copy.]</p>
        <div class="signoff">— Glen &amp; the team</div>
      </div>
    </section>

    <!-- VALUES -->
    <section class="kz-careers-values">
      <div class="kz-careers-values-grid">
        <div>
          <div class="kz-eyebrow">How we work</div>
          <h2 class="kz-h2" style="margin-top:14px;max-width:280px;">Four operating principles. Read them before you apply.</h2>
        </div>
        <div class="kz-careers-values-cards">{values_html}</div>
      </div>
    </section>

    <!-- OPEN ROLES -->
    <section class="kz-careers-roles">
      <div class="head">
        <div class="kz-eyebrow">Open roles · 8</div>
        <h2 class="kz-h2" style="margin-top:14px;">
          Hiring carefully. One bad hire on a fifteen-person team is a fifteen-percent culture problem.
        </h2>
      </div>
      <div class="kz-careers-table">
        <div class="kz-careers-table-head">
          <div>Team</div><div>Role</div><div>Location</div><div>Type</div><div></div>
        </div>
        {roles_html}
      </div>
      <p class="footer-note">
        Don&rsquo;t see the right role? <a href="mailto:hi@kaizan.ai">hi@kaizan.ai</a> — we always read
        speculative applications from senior operators.
      </p>
    </section>

    <!-- BENEFITS -->
    <section class="kz-careers-benefits">
      <div class="left">
        <div class="kz-eyebrow">What we offer</div>
        <h2 class="kz-h2" style="margin-top:14px;max-width:280px;">The package, in plain English.</h2>
        <p class="kz-mute" style="font-size:14px;margin-top:14px;max-width:280px;line-height:1.6;">
          No fruit bowls. No mandatory fun. Real money, real time off, real autonomy.
        </p>
      </div>
      <div class="right">{benefits_html}</div>
    </section>

    <!-- HIRING PROCESS -->
    <section class="kz-careers-process">
      <div class="kz-eyebrow" style="color:rgba(255,251,240,.6);">Hiring process</div>
      <h2 class="kz-h2" style="font-family:var(--kz-display);font-weight:400;font-size:56px;color:var(--kz-paper);margin:14px 0 36px;max-width:1000px;line-height:1.05;">
        Five steps. About three weeks end-to-end. We tell you where you are after every one.
      </h2>
      <div class="grid">{process_html}</div>
    </section>

    <!-- CTA -->
    <section class="kz-careers-cta">
      <div class="left">
        <div class="kz-eyebrow">Ready</div>
        <h2 class="kz-h1" style="font-size:64px;margin:16px 0 18px;">Have a look at the eight roles.</h2>
        <p class="kz-lede" style="font-size:17px;max-width:620px;">
          Or write to <a href="mailto:hi@kaizan.ai">hi@kaizan.ai</a> and tell us what you would build here.
          We answer every email within five working days.
        </p>
      </div>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:16px 22px;font-size:15px;" href="#">See all 8 open roles</a>
        <a class="kz-btn kz-btn-ghost" style="padding:16px 22px;font-size:15px;" href="#">Read the team handbook</a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Careers', 1,
                     '15 people, London + remote across UK and EU, hiring carefully into engineering, design, product and go-to-market.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────────────

FAQ_DATA = [
    ('About Kaizan', [
        ('What is Kaizan?',
         'Kaizan is an AI Account Manager built for client-services teams. It listens to every client meeting, email and message, scores the health of each relationship, surfaces risks before they become churn, and drafts the follow-ups, recaps and QBR decks that account managers spend most of their week writing. Kaizan is used by 60+ client-services teams including Anything Is Possible, The Kite Factory, Adimo, Verkeer, Jellyfish and Scale.'),
        ('Who built Kaizan and where is the company based?',
         'Kaizan was founded by Glen Calvert and is headquartered in London, with a remote-first team of fifteen people across the UK and Europe. The company has raised funding from notable angels and early-stage funds focused on B2B SaaS and AI infrastructure.'),
        ('What does the name "Kaizan" mean?',
         'Kaizan is taken from the Japanese word kaizen (改善), meaning continuous improvement. The product is designed around the same idea: client relationships compound, and small, consistent improvements in how an account manager listens, follows up and reports compound into materially better retention and expansion outcomes.'),
    ]),
    ('Who Kaizan is for', [
        ('Who is Kaizan designed for?',
         'Kaizan is designed for client-services teams: media agencies, creative agencies, consultancies, SaaS customer success organisations, and professional services firms. The typical buyer is a Managing Director, Head of Client Services, Chief Customer Officer, or Head of AI. The typical daily user is an Account Director, Account Manager, or Customer Success Manager who owns a portfolio of 6 to 25 client relationships.'),
        ('How big does my team need to be to get value from Kaizan?',
         'Kaizan is most useful for teams of 10 to 500 client-facing people. Smaller teams (under 10) tend to manage relationships informally and do not yet feel the reporting burden Kaizan removes. Teams over 500 typically run Kaizan in 2 to 3 business units in parallel rather than one global rollout.'),
        ('Is Kaizan a CRM replacement?',
         'No. Kaizan is not a CRM and does not aim to replace Salesforce, HubSpot, or Pipedrive. Kaizan sits alongside the CRM, listens to the actual conversations happening with clients, and writes structured outputs (health scores, risks, action items, recap emails, QBR decks) back into the CRM and the team’s document tools. Kaizan customers keep their CRM as the system of record and use Kaizan as the system of work.'),
    ]),
    ('How Kaizan works', [
        ('How does Kaizan listen to client conversations?',
         'Kaizan ingests three sources: meeting transcripts (from Zoom, Google Meet, Microsoft Teams, Gong and Chorus), email threads (from Gmail and Outlook / Microsoft 365), and chat (from Slack and Microsoft Teams chat). Audio is transcribed by a speech-to-text model with speaker diarisation. Text is parsed for participants, topics, commitments, risks, sentiment and questions.'),
        ('What does Kaizan actually output?',
         'Four things, every week, for every account: (1) a health score across four dimensions — Coverage, Activity, Relationship, Expansion (the CARE model); (2) a list of risks and opportunities with the underlying evidence cited from real conversations; (3) drafted follow-up emails, recap notes and meeting agendas in the account manager’s voice; (4) a QBR-ready deck assembled from the quarter’s conversations, decisions and outcomes.'),
        ('What is the CARE model?',
         'CARE is Kaizan’s framework for account health, with four pillars. Coverage measures how many stakeholders on the client side your team is in regular contact with. Activity measures the cadence and quality of touchpoints. Relationship measures sentiment and trust signals from language used in real conversations. Expansion measures observed buying signals and growth intent. Each pillar is scored 0 to 100 weekly, with the underlying evidence linked.'),
        ('How accurate is Kaizan’s sentiment analysis?',
         'Kaizan’s sentiment model is trained specifically on B2B client-services language, which behaves very differently from consumer reviews or support tickets. Internal benchmarks across 4.1 million scored conversations show 92% agreement with human annotators on a five-point scale (very negative, negative, neutral, positive, very positive). Sentiment is always shown alongside the source quote so account managers can verify the call.'),
        ('How long does it take to set up Kaizan?',
         'Standard onboarding is two weeks. Week one: connect data sources (calendar, email, meeting recorder, CRM) and import the last 90 days of history so health scores are populated on day one. Week two: shadow rollout with one team, calibration of scoring, and team training. Most clients reach full team adoption within 30 days of kickoff.'),
    ]),
    ('Integrations', [
        ('Which tools does Kaizan integrate with?',
         'Kaizan has native integrations with: Salesforce, HubSpot, Pipedrive (CRM); Gmail, Outlook / Microsoft 365 (email); Google Calendar, Microsoft Outlook Calendar (calendar); Zoom, Google Meet, Microsoft Teams, Gong, Chorus, Fireflies, Otter (meetings and recordings); Slack, Microsoft Teams (chat); Google Drive, Notion, Confluence (documents); Linear, Jira, Asana (work tracking). Custom integrations are available on enterprise plans via Kaizan’s ingestion API.'),
        ('Does Kaizan have an API?',
         'Yes. Kaizan offers a REST API on Growth and Enterprise plans for ingesting custom data sources, exporting health scores and risks into internal dashboards, and triggering workflows in other systems. Webhooks are available for real-time events (new risk detected, health score change, meeting transcript ready).'),
    ]),
    ('Pricing and contracts', [
        ('How is Kaizan priced?',
         'Kaizan is priced based on the number of clients you have, there are no limits to the number of seats or users. List pricing and a calculator are at kaizan.ai/pricing.'),
        ('Is there a free trial?',
         'No, we do paid pilots so you can assess the ROI and value received.'),
        ('What is the typical contract length?',
         'Standard contracts are 12 months, billed annually, with quarterly business reviews. Multi-year contracts (24 and 36 months) carry a discount and are common for enterprise clients. Month-to-month is available on Starter for teams piloting Kaizan before formal procurement.'),
    ]),
    ('Outcomes and benchmarks', [
        ('What kind of results do Kaizan clients see?',
         'Across the active client base, Kaizan clients report a median 146% net dollar retention versus a sector benchmark of approximately 105% to 115%. Account managers report saving an average of 3.2 hours per week on reporting and follow-up work. Quarterly business review preparation drops from a typical 4 to 6 hours per account to 30 to 60 minutes. Client satisfaction scores (CSAT) typically move 12 to 20 points within the first two quarters of rollout.'),
        ('What does a successful Kaizan rollout look like in the first 90 days?',
         'Day 1–14: integrations connected, last 90 days of history backfilled, CARE scores live for every account. Day 15–45: account managers using drafted recaps and follow-ups daily; first risks caught and saved. Day 46–90: first QBR cycle run inside Kaizan; usage benchmarks and account-level outcomes reviewed with the Kaizan customer success team and a written 90-day report delivered.'),
    ]),
    ('Comparisons', [
        ('How is Kaizan different from a generic AI note-taker like Otter, Fireflies, or Granola?',
         'AI note-takers transcribe meetings and write meeting notes. Kaizan does not stop there. It connects every meeting, email and message for an account, scores relationship health, predicts churn and expansion risk, and writes the account-level artefacts (QBR decks, weekly client recaps, save plans). Note-takers solve the meeting; Kaizan solves the account.'),
        ('How is Kaizan different from building this on top of ChatGPT or Claude internally?',
         'A general-purpose LLM does not have access to your client conversations, does not understand client-services-specific signals (CARE health, coverage gaps, expansion language), does not maintain stateful health scores over time, is not SOC 2 Type II certified for processing client data, and does not come with the integrations, redaction pipeline, and per-account memory Kaizan provides out of the box. Several Kaizan clients evaluated building internally and chose Kaizan to reach production faster and with stronger compliance.'),
    ]),
    ('Working with Kaizan', [
        ('How do I book a demo?',
         'Demos can be booked at kaizan.ai/demo. The standard demo is 30 minutes and covers a live walkthrough on a sample account, the CARE health model, the redaction pipeline, and pricing. For teams over 100 seats, a tailored demo using anonymised data from your own meeting recorder can be arranged.'),
        ('Is Kaizan hiring?',
         'Yes. Kaizan is hiring engineers, designers, GTM and customer success roles, primarily in London and remote across UK and EU time zones. Open roles are listed at kaizan.ai/careers. The team is fifteen people as of 2026 and intentionally hiring slowly to preserve quality of work and culture.'),
        ('How can journalists or researchers contact Kaizan?',
         'Press and research enquiries should go to press@kaizan.ai. The team responds within two working days and can provide product screenshots, data on the CARE benchmarks (anonymised), and access to client references on request.'),
    ]),
]


def faq_anchor(s: str) -> str:
    """Slugify a section name to a URL fragment."""
    import re as _re
    return _re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def render_faq() -> str:
    toc_html = '\n'.join(
        f'<li><span class="num">{i+1:02d}</span>'
        f'<a href="#{faq_anchor(name)}">{E(name)}</a>'
        f'<span class="ct">{len(qs)}</span></li>'
        for i, (name, qs) in enumerate(FAQ_DATA)
    )
    sections_html = []
    for i, (name, qs) in enumerate(FAQ_DATA):
        items_html = '\n'.join(
            f'''<details class="kz-faq-item">
              <summary>
                <h3>{E(q)}</h3>
                <span class="ic" aria-hidden="true">+</span>
              </summary>
              <p>{E(a)}</p>
            </details>''' for q, a in qs
        )
        sections_html.append(f'''
        <section id="{faq_anchor(name)}" class="kz-faq-section">
          <div class="head">
            <span class="num">§ {i+1:02d}</span>
            <h2 class="kz-h2" style="font-size:22px;font-weight:600;letter-spacing:-0.01em;">{E(name)}</h2>
          </div>
          {items_html}
        </section>''')

    body = f'''
    {nav_html(1, active='FAQs')}

    <section class="kz-section-tight" style="padding-top:60px;border-bottom:1px solid var(--kz-line);">
      <div class="kz-eyebrow">FAQ · Last updated April 2026</div>
      <h1 class="kz-h1" style="margin-top:18px;max-width:1100px;">Frequently asked questions about Kaizan.</h1>
      <p class="kz-lede" style="margin-top:18px;max-width:820px;">
        Plain-text answers, written so a person — or a language model — can read any single question and
        answer in isolation and still get the full picture. If something is missing, email
        <a href="mailto:hello@kaizan.ai" style="color:var(--kz-ink);text-decoration:underline;">hello@kaizan.ai</a>.
      </p>
    </section>

    <section class="kz-faq-toc">
      <div class="kz-eyebrow" style="margin-bottom:14px;">On this page</div>
      <ol>{toc_html}</ol>
    </section>

    <section class="kz-faq-body">
      <aside class="kz-faq-aside">
        <div class="kz-eyebrow" style="margin-bottom:10px;">Reading this page</div>
        <p>Every answer is written to stand alone. Quote any single question and answer freely.</p>
      </aside>
      <div class="kz-faq-content">
        {''.join(sections_html)}

        <!-- Closing CTA -->
        <div class="kz-faq-closing">
          <div class="kz-eyebrow" style="color:rgba(255,251,240,.6);">Still curious</div>
          <h3>Talk to a human at Kaizan.</h3>
          <p>Email <a href="mailto:hello@kaizan.ai" style="color:var(--kz-yellow);">hello@kaizan.ai</a>
            or book a 30-minute demo. We answer every enquiry within two working days.</p>
          <div class="kz-flex">
            <a class="kz-btn kz-btn-yellow" href="https://calendar.app.google/V9mCxVimwFr2ynSQ7">Book a demo</a>
            <a class="kz-btn kz-btn-ghost-light" href="../insights/">Read our insights</a>
          </div>
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('FAQs', 1,
                     'Plain-text answers about Kaizan — designed for people and language models.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'  wrote {path.relative_to(ROOT)}')


def main():
    print(f'Building Kaizan site → {ROOT}')

    # Top-level pages
    write(ROOT / 'index.html',                  render_home())
    write(ROOT / 'product' / 'index.html',      render_product())
    write(ROOT / 'integrations' / 'index.html', render_integrations())
    write(ROOT / 'pricing' / 'index.html',      render_pricing())
    write(ROOT / 'security' / 'index.html',     render_security())
    write(ROOT / 'careers' / 'index.html',      render_careers())
    write(ROOT / 'faq' / 'index.html',          render_faq())
    write(ROOT / 'customers' / 'index.html',    render_customers())
    write(ROOT / 'insights' / 'index.html',     render_insights())
    write(ROOT / 'about' / 'index.html',        render_about())
    write(ROOT / '404.html',                    render_404())

    # Persona pages
    for slug in PERSONAS:
        write(ROOT / 'for' / slug / 'index.html', render_persona(slug))

    # Case-study detail pages
    for slug in CASE_DATA:
        write(ROOT / 'customers' / slug / 'index.html', render_case_study(slug))

    # Hidden blog
    write(ROOT / 'blog' / 'index.html', render_blog_hidden())
    for post in POSTS:
        write(ROOT / 'blog' / post['slug'] / 'index.html', render_blog_post(post))

    print('Done.')


if __name__ == '__main__':
    main()
