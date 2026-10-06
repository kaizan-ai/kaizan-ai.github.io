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
import json
import os
import re
import sys
from html import escape
from pathlib import Path
from textwrap import dedent
from urllib.parse import quote

import blog  # tools/blog.py — Markdown blog pipeline (loads content/blog/*/index.md)


# ─────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]

# Top-nav. The "Blog" item points to /insights/ (matches the design canvas
# behaviour where the "Blog" nav target was the Insights page). The hidden
# /blog/ landing is NOT in the nav by design.
NAV = [
    ('Home',         '/'),
    # nav_html renders "Product" as a hover dropdown listing PRODUCT_MENU
    # (Integrations lives under it, so it has no top-level nav item).
    ('Product',      'product/'),
    # Sentinel: nav_html renders this as a hover dropdown listing PERSONA_LIST.
    ('Personas',     '__personas_dropdown__'),
    ('Pricing',      'pricing/'),
    # TODO: re-enable "Clients" nav item once the customer-stories content is ready.
    # ('Clients',      'customers/'),
    # Sentinel-ish: nav_html renders "Resources" as a hover dropdown listing
    # RESOURCES_MENU. The trigger itself points at the first item (Our Research).
    ('Resources',    'research/'),
    ('About',        'about/'),
    # Plain text nav link (relative, so it resolves to /referral-partners/ on UK
    # and /us/referral-partners/ on US via normal relative paths).
    ('Become a partner', 'referral-partners/'),
]

# ─────────────────────────────────────────────────────────────────────
# DEMO BOOKING — anti-bot interstitial.
# "Book a demo" buttons across the site point at /demo/ (see render_demo)
# rather than the raw booking link, so crawlers can't harvest the booking
# URL and hammer the calendar. /demo/ shows a Cloudflare Turnstile
# human-check; only after it passes does the page reveal the (base64-obfuscated)
# calendar URL and redirect. CALENDAR_URL never appears as a plain href in the
# generated HTML.
#
# UK and /us/ each book via their own Calendly link (rep-specific — UK is
# Glen, US is Ray); /us/'s is US_CALENDAR_URL, substituted in by
# build_us_locale().
#
# TURNSTILE_SITE_KEY: public, safe to commit. Create a Turnstile widget in the
# Cloudflare dashboard (scoped to kaizan.ai) and paste its Site Key here. Until
# a real key is set, /demo/ will not render the widget.
CALENDAR_URL = 'https://calendly.com/glen-kaizan/30min'
TURNSTILE_SITE_KEY = '0x4AAAAAADx9Zptj_zGxAWBm'

# Sub-links shown in the "Product" nav dropdown. The "Product" trigger itself
# opens the dropdown (no direct link); "Overview" is the /product/ page.
PRODUCT_MENU = [
    ('Overview',     'product/'),
    ('Integrations', 'integrations/'),
]

# Sub-links shown in the "Resources" nav dropdown. The "Resources" trigger
# itself points at the Our Research page (research/, set in NAV above); the
# dropdown lists the other resources. FAQ maps to /faq/; Security is the
# Trust & Security page. Third column class (is-yellow / is-mute) is reserved
# for an optional glyph treatment.
RESOURCES_MENU = [
    ('Blog',          'blog/',           'is-mute'),
    ('Knowledge Hub', 'knowledge-hub/',  'is-mute'),
    ('FAQs',          'faq/',            'is-mute'),
    ('Security',      'security/',       'is-mute'),
]

# Client-logo marquee. Each entry is a dict with name + filename in
# assets/img/clients/. Add or remove entries here to update the homepage
# marquee — the build picks them up automatically.
CLIENT_LOGOS = [
    # A few clients lead in, then the US clients (US market push) land around the
    # middle — so US prospects catch familiar logos once they've scrolled to the
    # band, rather than the US set scrolling past before they get there.
    dict(name='The Kite Factory',         file='the-kite-factory.png'),
    dict(name='Scale Digital',            file='scale-digital.png'),
    dict(name='Tradedoubler',             file='tradedoubler.png', h=38),
    dict(name='Open Partners',            file='open-partners.svg'),
    dict(name='Verkeer',                  file='verkeer.png'),
    # US clients — order as supplied.
    dict(name='Gravity Global',           file='gravity-global.svg'),
    dict(name='Transmission',             file='transmission.png'),
    dict(name='Acceleration Partners',    file='acceleration-partners.png', h=58),
    dict(name='Marketing Architects',     file='marketing-architects.png'),
    dict(name='Searchlab',                file='searchlab.png'),
    dict(name='NP Digital',               file='np-digital.png', big=True),
    dict(name='Other.',                   file='other.png', big=True),
    dict(name='The Gap Partnership',      file='the-gap-partnership.svg', big=True),
    # Remaining clients.
    dict(name='AMS',                      file='ams.png', treat='detail', h=74),
    dict(name='Assembly Global',          file='assembly-global.svg', h=40),
    dict(name='Click Through Marketing',  file='click-through-marketing.png'),
    dict(name='Collective Content',       file='collective-content.svg'),
    dict(name='Gifta',                    file='gifta.png', treat='soft', big=True),
    dict(name='Kohort',                   file='kohort.png'),
    dict(name='Medialab',                 file='medialab.png'),
    dict(name='PASHN Media Agency',       file='pashn-media-agency.svg', treat='light', h=40),
    dict(name='Viola',                    file='viola.png'),
    dict(name='Webtopia',                 file='webtopia.png', h=58),
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
    dict(q='We’ve seen the sentiment of every client go up.',
         name='Hannah Carthy', role='MD', co='Verkeer', tone='olive'),
    dict(q='Kaizan is now fundamental to the team and managing client relationships.',
         name='Stephen Kerin', role='Director', co='Scale Digital', tone='gold'),
    dict(q='30% fewer client escalations since we rolled out Kaizan across the team.',
         name='Gravity Team', role='Client Services', co='Gravity Advertising', tone='clay'),
]

# Personas - one template, eight personas.
# Section structure per page: Hero -> Why X love Kaizan -> Product surface ->
# FAQs -> Other personas -> Closing CTA.
#
# h1 is split into (head, highlighted, tail). Either head or tail can be ''.
# love is a list of (title, description) tuples; if 4 items, rendered as a
# 2x2 grid; if 3 items, rendered as a 3-col grid.
# quote_* fields drive the hero quote card (circular photo + pull quote +
# attribution + "Read more" pill linking to quote_cta_href).
PERSONAS = {
    'account-manager': dict(
        eyebrow='FOR · CLIENT SERVICE / ACCOUNT MANAGER',
        role='account managers',
        role_cap='Account Managers',
        h1=('Get your', 'day back.', ''),
        sub=("Kaizan removes the admin and surfaces the next best action on every client - "
             "so you spend your time on the work only you can do."),
        quote_bg='radial-gradient(circle at 35% 30%, #D8A056, #6E3E10)',
        quote_pull=('The Client 360 gives us an at-a-glance view of what’s going on in our clients’ '
                    'worlds. We can then come up with ideas off the back of that. Previously, we were '
                    'having to do lots of desk research, and that took an awfully long time.'),
        quote_name='Fiona Skilton',
        quote_role='Client Services Director',
        quote_co='Collective Content',
        quote_nudge=False,
        quote_cta='Read the Collective Content case study →',
        quote_cta_href='https://blog.kaizan.ai/from-reactive-to-proactive-how-great-client-teams-stay-ahead-3404dd582591',
        love=[
            ('Admin disappears.',
             "Notes, action capture, follow-up chasing, status updates - Kaizan handles the work "
             "that fills your day but never moves a client forward. Your time goes back to thinking "
             "and client conversations."),
            ('Next best action, surfaced.',
             "After every meeting and across every client, Kaizan tells you the move that matters "
             "most - the email to send, the stakeholder to nurture, the risk to address - so you're "
             "never wondering what to do next."),
            ('Stay on top of every commitment.',
             "Every promise, every action, every deadline - tracked across every client and "
             "surfaced before it slips."),
            ('An AI Helper working alongside you.',
             "Drafting follow-ups before you've left the meeting, prepping your next conversation "
             "while you're in another, watching for client signals overnight - your always-on "
             "associate."),
        ],
        product_h2='The product surface an account manager actually touches.',
        products=[
            ('Meetings & commitments',
             'Every call auto-captured. Notes, actions, decisions, owners and deadlines tracked '
             'across every client - so the admin disappears and nothing slips.'),
            ('Next-best-action briefing',
             'Your portfolio ranked overnight. Each morning, the three moves that matter most - '
             'the email to send, the stakeholder to nurture, the risk to address.'),
            ('AI Helper',
             'Your always-on associate. Drafts follow-ups before you’ve left the meeting, preps '
             'the next conversation while you’re in another, watches for client signals overnight.'),
        ],
        faqs=[
            ('Does it work with Zoom, Teams, and Google Meet?',
             "Kaizan joins meetings across Zoom, Teams and Google Meet automatically - "
             "calendar-based, so you don't add it manually each time. Notes, actions and decisions "
             "land in the same place no matter where the conversation happened."),
            ("Will my client know it's listening - what do I tell them?",
             "You stay in control of disclosure. Kaizan supports the consent flows your clients "
             "expect, and we share language teams use in the first conversation so it lands "
             "professionally rather than as a surprise."),
            ('I run 15 clients. Can I see what needs my attention without checking each one?',
             "That's the default view. Kaizan ranks the whole portfolio by what's changed "
             "overnight and surfaces the next best action per client, so you start the day with "
             "the handful of things that actually matter - not fifteen tabs."),
            ('Does it sync with HubSpot / Salesforce so I’m not double-entering?',
             "Kaizan reads from and writes back into HubSpot and Salesforce, so contacts, "
             "activity, notes and next-step fields stay current without manual data entry. If "
             "your CRM isn't on the list, the API covers anything not natively integrated."),
        ],
        cta='See Kaizan for account managers.',
    ),

    'client-service-director': dict(
        eyebrow='FOR · CLIENT SERVICE DIRECTOR',
        role='client service directors',
        role_cap='Client Service Directors',
        h1=('Run your portfolio with', 'eyes open.', ''),
        sub=("Onboard new team members in days. Catch dissatisfaction before the renewal call. "
             "See the patterns across your portfolio that no individual AM can spot alone."),
        quote_bg='radial-gradient(circle at 30% 30%, #B58A4F, #4A2A0E)',
        quote_pull=('We have a target of achieving 20% better efficiency across the business. 20% '
                    'less time spent on administration. Kaizan has significantly helped us achieve '
                    'that target.'),
        quote_name='Derek Grant',
        quote_role='VP Operations & General Manager UK / US',
        quote_co='Tradedoubler',
        quote_nudge=False,
        quote_cta='Read the Tradedoubler case study →',
        quote_cta_href='https://blog.kaizan.ai/how-tradedoubler-is-driving-20-greater-operational-efficiency-across-3-500-clients-5f99fd11d1a6',
        love=[
            ('Onboard new team members in days, not months.',
             "Every client's history - meetings, decisions, stakeholders, context - searchable "
             "from day one. New joiners are useful immediately instead of spending a quarter "
             "getting up to speed."),
            ('Proactive risk alerts.',
             "Kaizan flags client dissatisfaction, slipping sentiment, and emerging issues across "
             "the portfolio - so you intervene before the conversation where they tell you it's "
             "over."),
            ('Patterns across the portfolio.',
             "Pricing pushback on three clients, scope creep on four, the same stakeholder "
             "concern in two - themes your team can't see one account at a time."),
            ('AI Helpers watching the portfolio while you sleep.',
             "Risk signals collected overnight, the morning briefing ready before standup, the "
             "team primed on what needs attention - without you having to assemble the meeting "
             "yourself."),
        ],
        product_h2=('The whole portfolio on one page - ready for the conversation with your team, '
                    'not over their shoulder.'),
        products=[
            ('Portfolio dashboard',
             "Every account in the team’s book, scored across CARE. Click any row for the "
             "conversations, contacts and signals underneath."),
            ('Risk and coverage',
             "Accounts where coverage has thinned, sentiment has shifted or expansion threads "
             "have gone cold - flagged before the QBR."),
            ('Shared client view',
             "You and your AMs see the same picture of every account - same scores, same signals, "
             "same evidence. Standups stop being status theatre and start being decisions."),
        ],
        faqs=[
            ('How quickly can a new starter get up to speed on a client they’ve never worked on?',
             "From day one. Every meeting, decision, stakeholder and commitment on the account is "
             "searchable, with summaries on demand. Most directors tell us a new joiner "
             "contributes meaningfully inside their first week instead of the usual quarter."),
            ('How does Kaizan know when a client is unhappy - what signals does it use?',
             "Kaizan reads across the full conversational record - meetings, email and chat - for "
             "sentiment shifts, escalation language, stakeholder withdrawal and slipping commitment "
             "cadence. Risk signals surface on each client with the underlying evidence, so you "
             "act on context rather than a score in isolation."),
            ('Can we tune what counts as a risk for our business?',
             "Risk thresholds, signals and weightings are configurable to your portfolio. We "
             "calibrate during rollout so alerts match how your team actually thinks about account "
             "health - not a generic model."),
            ('How does it handle sensitive conversations - an AM venting, an internal disagreement?',
             "Internal conversations stay internal. Permissions, redaction rules and workspace "
             "boundaries are configurable so sensitive content doesn't surface outside the people "
             "it's meant for, and there are explicit controls for excluding 1:1s and team-only "
             "meetings."),
        ],
        cta='See Kaizan for client service directors.',
    ),

    'leadership': dict(
        eyebrow='FOR · SENIOR LEADERSHIP / DIRECTOR',
        role='senior leaders',
        role_cap='Senior Leaders',
        h1=('See the path to', 'doubling revenue', ' on every client.'),
        sub=("Kaizan turns every meeting, signal, and stakeholder into the intelligence you need "
             "to grow each client deliberately - and catch the risks that could cost you the "
             "relationship."),
        quote_bg='radial-gradient(circle at 30% 30%, #C99A66, #5A2E14)',
        quote_pull=('We’ve had numerous occasions where we’ve been able to spot and identify '
                    'high-risk clients that potentially were going to leave.'),
        quote_name='Brandon Smith',
        quote_role='Managing Director',
        quote_co='NP Digital',
        quote_nudge=False,
        quote_cta='Read the NP Digital case study →',
        quote_cta_href='https://blog.kaizan.ai/how-np-digital-uses-ai-to-strengthen-client-relationships-and-drive-retention-45f04f7fd0bc',
        love=[
            ('The path to doubling revenue on every client.',
             "Kaizan surfaces where each relationship could grow - unmet needs, adjacent scope, "
             "stakeholders you don't yet know - so growth becomes a deliberate plan, not a hope."),
            ('Catch dissatisfaction before it costs you.',
             "Every client risk surfaced early, with the context to act on it - so renewal "
             "conversations are negotiations, not autopsies."),
            ('Decisions on data, not anecdotes.',
             "Which clients are profitable, where the hours go, what's actually working across "
             "the portfolio - finally legible."),
            ('AI Helpers running in the background.',
             "Weekly intelligence on every client delivered before Monday's exec meeting, "
             "board-ready insights compiled automatically - the analysis layer working while you "
             "focus on the decisions."),
        ],
        product_h2='The forward view of the business - built from the team’s actual conversations.',
        products=[
            ('Executive briefing',
             'Monday morning: one page on revenue at risk, expansion in flight, and which Heads '
             'need air cover this week.'),
            ('Renewal forecast',
             'Probability-weighted forecast for the next four quarters. Click any account to see '
             'the evidence underneath the score.'),
            ('Board view',
             'Export-ready slides for the quarterly board pack: retention, coverage, '
             'time-to-resolve, expansion pipeline.'),
        ],
        faqs=[
            ('How does Kaizan identify growth opportunities on existing clients?',
             "Kaizan reads every conversation across the relationship and surfaces three things: "
             "unmet needs the client has voiced but you haven't quoted, adjacent scope the work "
             "is already touching, and stakeholders you don't yet know who influence the next "
             "decision. Each one comes with the evidence underneath."),
            ('How quickly do we see commercial impact?',
             "Portfolio-level signal usually lands inside the first month. Material impact on "
             "retained and expansion revenue typically shows up across two quarters, as the "
             "renewal and growth conversations Kaizan flagged early start closing differently."),
            ('Do we own our data, and can we get it all out if we leave?',
             "Your client data is yours. Full export is available at any time in standard formats, "
             "and contract terms make that explicit rather than buried."),
            ('What does rollout look like - weeks, months, what’s the lift on our side?',
             "Weeks, not months. Your team's existing meetings, email, chat and tools connect "
             "into Kaizan; there's no data migration project, no per-seat rollout, no quarter of "
             "change management. Pricing is by portfolio size, so you don't ration access while "
             "you scale."),
        ],
        cta='See Kaizan for senior leadership.',
    ),

    'head-of-ai': dict(
        eyebrow='FOR · HEAD OF AI / CTO',
        role='AI and technology leaders',
        role_cap='AI and Technology Leaders',
        h1=('Your', 'client brain.', ' In the AI tools you already use.'),
        sub=("Turn every meeting, email, and decision into a unified client brain your AI tools "
             "can query - and a foundation for the custom products, services, and workflows your "
             "business wants to build."),
        quote_bg='radial-gradient(circle at 30% 30%, #5F7E94, #1A2D3D)',
        quote_pull=('We have this huge dataset now… we can start making not just client decisions, '
                    'but product decisions.'),
        quote_name='Corin Ward',
        quote_role='Director of AI',
        quote_co='Tradedoubler',
        quote_nudge=False,
        quote_cta='Read the engineering architecture →',
        quote_cta_href='https://blog.kaizan.ai/how-tradedoubler-is-quantifying-client-conversations-to-power-ai-and-product-decisions-5669edac12c8',
        love=[
            ('Your client brain, in the AI tools you already use.',
             "Every meeting, email, decision, and signal - unified and queryable via MCP from "
             "Claude, ChatGPT, or whatever model your org has standardised on."),
            ('Build your own products, services, and workflows on top.',
             "The API gives you a full data layer to build custom client-facing products and "
             "internal workflows - without rebuilding the ingestion and unification work yourselves."),
            ('Enterprise-grade controls.',
             "SSO/SAML, custom retention, data residency - the controls procurement asks about, "
             "available from day one."),
        ],
        product_h2='The platform layer your team would have to build - already built.',
        products=[
            ('Kaizan API',
             'RESTful and MCP endpoints for every primitive: clients, conversations, signals, '
             'drafts, scores. Drop into your existing internal tools.'),
            ('MCP server',
             'Native MCP - any LLM your org has standardised on can query the unified client data '
             'layer without bespoke glue.'),
            ('Governance console',
             'Eval runs, prompt versions, redaction rules, access logs. Everything your security '
             'review will ask for, in one place.'),
        ],
        faqs=[
            ('Can I connect my own LLM via MCP, and what does the schema look like?',
             "Kaizan supports MCP natively - any LLM that speaks the protocol can query the "
             "unified client data layer, regardless of which model your org has standardised on. "
             "We share the schema and example queries in a technical session so your team can "
             "scope what they'd build first."),
            ('What can teams actually build on top of the API - any examples?',
             "The API is on every tier from Team upwards. Customers use it for internal copilots "
             "that answer questions about a specific client, client-facing portals that pull live "
             "status, custom reporting into the BI tools they already run, and workflow "
             "automation across CRM, comms and project tools - anywhere the unified client data "
             "layer is useful."),
            ('Where is data stored, and what data residency options do you offer?',
             "Data residency is available at Enterprise tier. We support deployments in the "
             "regions our customers operate in; specifics depend on your tier and where your "
             "clients sit, and are confirmed in contract."),
            ('What’s your SOC 2 / ISO 27001 / GDPR posture?',
             "Kaizan is built for enterprise procurement and the controls security and "
             "compliance teams expect - SSO/SAML, custom retention, and data residency at "
             "Enterprise tier. We share the full posture, certifications and reports under NDA so "
             "your security review has what it needs."),
        ],
        cta='See Kaizan for heads of AI.',
    ),

    'project-manager': dict(
        eyebrow='FOR · PROJECT MANAGER',
        role='project managers',
        role_cap='Project Managers',
        h1=('Run the work.', "Don't chase it.", ''),
        sub=("Every project, every status, every commitment - in one always-current place, with "
             "an AI Helper watching it all 24/7."),
        quote_bg='radial-gradient(circle at 30% 30%, #6F8474, #1F3025)',
        quote_pull=('A lot of CS teams try to run without too many processes as they put the human '
                    'connection first. The processes are what help consistency across the client '
                    'set - a balance where people get to be people, but they’re protected by checks '
                    'that take out the guesswork.'),
        quote_name='Hannah Carthy',
        quote_role='Managing Partner',
        quote_co='Verkeer',
        quote_nudge=True,
        quote_cta='Read the Verkeer case study →',
        quote_cta_href='https://blog.kaizan.ai/cs-leader-quick-fire-q-a-hannah-carthy-verkeer-5c7cd3eb6b75',
        love=[
            ('One unified place for every project.',
             "Meetings, actions, decisions, commitments, status - across every client and every "
             "team - in one always-current view. No more hunting through Slack, email, and three "
             "project tools to find out what's actually going on."),
            ('Status reports write themselves.',
             "Every meeting's actions, decisions, and owners captured automatically - so Friday "
             "afternoons stop being eaten by retrospective documentation."),
            ('An AI Helper working on your projects 24/7.',
             "Watching for slippage, drafting status updates before the standup, chasing actions "
             "while you're in another meeting - your always-on associate."),
        ],
        product_h2='The PM’s leverage: less chasing, more steering.',
        products=[
            ('Status drafter',
             'A draft client update built from the week’s actual conversations, ready to edit - '
             'every Friday, or every Monday.'),
            ('Scope sentinel',
             'Flag the moment client language drifts beyond the SOW. Optional auto-tag in the '
             'project tracker.'),
            ('Live risk register',
             'A risk register fed from conversations across the team. No more "we should’ve seen '
             'that coming".'),
        ],
        faqs=[
            ('Does it sync into Asana / Monday / ClickUp / Jira?',
             "Kaizan integrates with Asana, Monday, ClickUp and Jira, so actions, owners and "
             "status flow both ways without manual re-entry. Anything not natively integrated is "
             "reachable via the API."),
            ('Can it tell the difference between an action item and general discussion?',
             "Kaizan separates actions, decisions and commitments from general discussion, "
             "attributes each one to the right owner, and links it back to the moment in the "
             "meeting it came from. You review and confirm - nothing routes downstream until you do."),
            ('What if a meeting happened offline - can I add decisions and actions manually?',
             "Manual entry sits alongside automatic capture. Add or edit actions, decisions and "
             "notes directly, and they're treated as first-class items - owned, tracked and "
             "followed up like anything Kaizan captured itself."),
            ('Can captured actions be assigned automatically based on who said what?',
             "Kaizan attributes actions to the person who took them on in the conversation, and "
             "routes them into your project tool of choice - with optional human review before "
             "anything is auto-assigned, so the system never overrides judgement."),
        ],
        cta='See Kaizan for project managers.',
    ),

    'new-business': dict(
        eyebrow='FOR · NEW BUSINESS / SALES',
        role='new business leaders',
        role_cap='New Business Leaders',
        h1=('', 'Pitch warmer.', ' Grow existing clients deliberately.'),
        sub=("Spend your prep time on the conversation, not the research - Kaizan surfaces the "
             "intel, the moments, and the people that matter."),
        quote_bg='radial-gradient(circle at 35% 30%, #8AAEAE, #1F4040)',
        quote_pull=('The biggest impact of Kaizan is the time it gives us back. In meetings to be '
                    'more present and engaged - and afterwards, a resource we can drop back into '
                    'to make sure we’re doing the things we said we’d do.'),
        quote_name='Adam Hopkinson',
        quote_role='Agency Owner',
        quote_co='PASHN',
        quote_nudge=False,
        quote_cta='Read the PASHN case study →',
        quote_cta_href='https://blog.kaizan.ai/how-pashn-uses-ai-to-strengthen-client-relationships-protect-revenue-and-save-time-ebda9f8128b7',
        love=[
            ('Walk into every pitch already prepared.',
             "Stakeholder intel, market context, competitor positioning, the prospect's recent "
             "moves - all surfaced before you walk in, so prep time goes on the pitch, not the "
             "research."),
            ('See where existing clients are ready for more.',
             "New initiatives, leadership changes, unmet needs, frustrations with current scope - "
             "Kaizan surfaces the moments worth a growth conversation, so you stop relying on AMs "
             "to remember."),
            ('Know who actually decides.',
             "Stakeholder maps surface the real influencers - not just the people in the meeting "
             "- so you spend your influence where it counts."),
            ('An AI Helper prospecting while you sleep.',
             "Watching target accounts for leadership changes, funding rounds, and buying signals "
             "- so you wake up to a tee'd-up day, not a cold start."),
        ],
        product_h2='Pitch from a position of knowing - not guessing.',
        products=[
            ('Prospect dossier',
             'Every chemistry meeting and call distilled into a one-page brief: priorities, '
             'language, decision criteria, internal politics.'),
            ('Shortlist intel',
             'When prospects mention competitors, you see it - with the rebuttal slide ready '
             'before they ask the question.'),
            ('Pitch tailoring',
             "Pre-pitch checklist: have we addressed what they actually said matters? What’s "
             "missing from this deck?"),
        ],
        faqs=[
            ('Can I use it on prospects, or only on existing clients?',
             "Both. Kaizan runs on prospects and on the existing portfolio, which is the point - "
             "your pitch motion and your growth motion run off the same intelligence layer, not "
             "two disconnected stacks."),
            ('Where does market and competitor intel come from, and how current is it?',
             "Intel is pulled from the conversations Kaizan captures across your accounts and "
             "target list, plus the external sources it monitors - and refreshed automatically so "
             "what you walk into a pitch with is current, not a stale dossier."),
            ('Can I export a briefing pack for a pitch in one click?',
             "One click. Kaizan compiles a pitch-ready briefing on demand: stakeholders, decision "
             "criteria, recent activity, competitor positioning and the talking points worth "
             "opening with - exported in the format your team uses for pre-reads."),
            ('Does it work alongside our prospecting tools (LinkedIn Sales Nav, Apollo, etc.)?',
             "Kaizan sits alongside your prospecting stack, not on top of it. It reads from the "
             "same activity layer your team already works in and feeds the intelligence your "
             "sellers use to prepare, pitch and follow up."),
        ],
        cta='See Kaizan for new business.',
    ),

    'performance': dict(
        eyebrow='FOR · PERFORMANCE / OPERATIONS',
        role='performance and operations leaders',
        role_cap='Performance and Operations Leaders',
        h1=('Turn every client interaction into', 'operational data.', ''),
        sub=("See where the hours go, which processes are landing, and how sentiment is trending "
             "- all flowing into the BI tools you already use."),
        quote_bg='radial-gradient(circle at 35% 30%, #708FAA, #1F3A50)',
        quote_pull=('The level of information and the frequency of information is on a scale that '
                    'we’ve never been able to achieve before.'),
        quote_name='Gabriella Krite',
        quote_role='Managing Partner of Operations',
        quote_co='The Kite Factory',
        quote_nudge=False,
        quote_cta='Read The Kite Factory case study →',
        quote_cta_href='https://blog.kaizan.ai/how-the-kite-factory-uses-ai-to-unify-client-data-and-improve-operational-visibility-5f18d0642db6',
        love=[
            ('See where the hours actually go.',
             "Time across calls, comms, and meetings - per client, per team, per discipline - so "
             "profitability conversations happen on data, not feel."),
            ('Process compliance, finally visible.',
             "Are weekly status meetings happening? QBRs on cadence? Senior reviews on the right "
             "clients? Stop asking, start seeing."),
            ('Client sentiment trended over time.',
             "Not a snapshot - a trajectory you can correlate with the levers your team is pulling."),
            ('AI Helpers running the reports overnight.',
             "Anomalies, outliers, and exceptions surfaced before the day starts - so you act on "
             "what happened yesterday, not what surfaces a week later."),
        ],
        product_h2='Operational reporting that finally maps to what the client is actually thinking.',
        products=[
            ('Expectation map',
             'For every client, what they say they care about, ranked by how often they raise it '
             'in conversation. Updated weekly.'),
            ('Drift alerts',
             "When the client’s language about success changes - different metrics, different "
             "timeframes, different competitors - you get the alert."),
            ('Auto-drafted weekly',
             'The Friday client update, drafted in your voice, around the metrics this client '
             'actually grades you on.'),
        ],
        faqs=[
            ('Can I export raw data into our warehouse / BI tool?',
             "Raw data exports into the warehouse and BI tools your team already runs, so client "
             "interaction data sits next to your other operational metrics rather than in a "
             "separate silo. The API is on every tier from Team upwards if your stack needs "
             "something native."),
            ('What does Kaizan track out of the box vs. what we’d need to configure?',
             "Out of the box: time across calls, comms and meetings; sentiment and stakeholder "
             "coverage; process adherence (QBR cadence, senior reviews, status meetings); "
             "commitments and slippage. Custom metrics, thresholds and definitions are configured "
             "to your operating model during rollout."),
            ('Can we build custom reports, or are we tied to your dashboards?',
             "Both. Kaizan ships dashboards out of the box and exposes the underlying data "
             "through the API, so your team builds whatever custom reporting your operation "
             "actually runs on."),
            ('How does sentiment tracking work, and how reliable is it?',
             "Sentiment is derived from the language and behaviour across client conversations "
             "and calibrated to your portfolio during rollout. It's a trajectory signal - most "
             "useful as a trend correlated against the levers your team is pulling, not a single "
             "number lifted out of context."),
        ],
        cta='See Kaizan for performance and operations.',
    ),

    'strategy-creative-marketing': dict(
        eyebrow='FOR · STRATEGY, CREATIVE, MARKETING',
        role='strategy, creative and marketing leaders',
        role_cap='Strategy, Creative and Marketing Leaders',
        h1=('Spend your hours', 'on the work.', ' Not catching up to it.'),
        sub=("Every conversation, decision, and signal on every client - ready the moment the "
             "brief lands."),
        quote_bg='radial-gradient(circle at 35% 30%, #B5A06D, #4A3D1A)',
        quote_pull=('Being across so many clients, I really struggled to make sure I had a good '
                    'understanding across all of our different client interactions and touch '
                    'points. Now I have much greater visibility into what’s going on day-to-day - '
                    'without the subjectivity of what my teams or even our clients are telling me.'),
        quote_name='Alex Beddoe',
        quote_role='Head of Biddable Media',
        quote_co='Transmission',
        quote_co_url='https://transmissionagency.com/',
        quote_nudge=True,
        quote_cta='Read the Transmission case study →',
        quote_cta_href='https://blog.kaizan.ai/agency-leaders-who-dont-move-now-will-be-managing-the-fallout-later-9f792fe49686',
        love=[
            ('Walk into every brief with full context.',
             "Every meeting, every decision, every conversation - searchable and summarisable "
             "before the brief even lands on your desk."),
            ('Market and competitor intel as a creative input.',
             "Where the client is winning, where they're losing, what their audience is saying - "
             "feeding the work, not buried in an account team's CRM."),
            ('The "get me up to speed" hours, gone.',
             "New brief on a client you've not worked on? Joining a pitch team mid-flight? Ask "
             "Kaizan. Stop billing context-gathering as if it were the work."),
            ('AI Helpers monitoring market and competitors 24/7.',
             "Competitor moves, audience shifts, cultural signals - all current the moment a "
             "brief lands, so you skip the scramble to catch up."),
        ],
        product_h2='Strategy, creative and marketing - all running off the same live signal.',
        products=[
            ('Theme synthesis',
             "Cluster the language across 50+ meetings into the three themes that matter for "
             "next quarter’s strategy."),
            ('Brief enrichment',
             'Every brief auto-augmented with the last 30 days of client context: meetings, '
             'references, language patterns, hot buttons.'),
            ('Quote miner',
             'Every flattering thing a client said about working with you - surfaced, attributed, '
             'ready for sign-off and the next case study.'),
        ],
        faqs=[
            ('Can I search across every meeting, brief, and document for a given client?',
             "Every meeting, brief, email and chat on a client is searchable in one place. You "
             "ask the question - Kaizan returns the answer with the source underneath, not just a "
             "list of links to wade through."),
            ('Will it summarise long client histories on demand?',
             "Long client histories summarise on demand, scoped to the question you're actually "
             "asking - the whole relationship, a single campaign, one stakeholder, a specific "
             "competitor mention. You stop billing context-gathering as if it were the work."),
            ('Can I pull insights straight into a creative brief or strategy doc?',
             "Insights, quotes and source-linked references pull directly into the tools your "
             "team writes briefs and strategy in, so the live signal lands inside the document "
             "rather than in a separate window your strategist has to flip to."),
            ('How fresh is the market and competitor intel?',
             "Market and competitor intel is monitored continuously and refreshed automatically. "
             "The moment a brief lands, you're working from current signal - not a deck someone "
             "updated three quarters ago."),
        ],
        cta='See Kaizan for strategy, creative and marketing.',
    ),
}

PERSONA_LIST = [
    ('account-manager',            'Client Service / Account Manager'),
    ('client-service-director',    'Head of Client Services'),
    ('leadership',                 'Senior Leadership'),
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
             "writing a brief from scratch. The work was real but it was repeatable, which made "
             "it doubly painful."),
            ('What changed',
             "Kaizan's Insights agent now drafts the QBR brief automatically the week before each "
             "review. Health, sentiment, expansion signals and risk flags are all there in a "
             "single doc. Hannah edits, she doesn't write."),
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
             "Mid-tier accounts at TKF were churning quietly, sentiment dropped on calls a few "
             "weeks before any explicit signal. By the time the AM noticed, the client had already "
             "had the internal conversation."),
            ('What changed',
             "The Risk agent surfaces sentiment delta, response-time slippage and stakeholder "
             "change in a single weekly digest. Three accounts in Q2 were flagged early enough for "
             "the client partner to step in personally."),
            ('What it unlocked',
             "£480k of revenue retained that would otherwise have been a churn line item. More "
             "importantly, AMs trust the signal: adoption hit 100% within six weeks."),
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
             "and stakeholder shifts, flagging the partner the same day."),
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
         d='Patterns we found across the highest-NPS teams, from briefing rituals to how they handle silence.',
         meta='9 min read', author='Glen Calvert', date='2 May 2026',
         img=cover('#FFB900', '#FFD86B', '01')),
    dict(cat='PRODUCT', t='Want to see Kaizan in action?',
         d='A 6-minute walk-through of the AI Assistant capturing a real client call and shipping the work behind it.',
         meta='6 min watch', author='Kaizan team', date='28 Apr 2026',
         img=cover('#0A0A0A', '#3A3A3A', '02')),
    dict(cat='WHITE PAPER', t='The 146% paradox',
         d='Why headline numbers hide risk, and the four leading indicators that actually predict the next year.',
         meta='18 min · gated', author='Pravin Paratey', date='21 Apr 2026',
         img=cover('#F1ECDD', '#E0D6BB', '03')),
    dict(cat='FIELD NOTES', t='The Monday briefing, decoded',
         d='What a good weekly client-health ritual looks like, from the firms running Kaizan in production.',
         meta='9 min read', author='Hannah Bowes', date='14 Apr 2026',
         img=cover('#D9E5DA', '#A8C4AE', '04')),
    dict(cat='INTERVIEW', t='A conversation with Waseem Ali',
         d='Why we call it Client Super Intelligence, and what changes when judgement becomes infrastructure.',
         meta='22 min listen', author='Glen Calvert', date='7 Apr 2026',
         img=cover('#FFB900', '#0A0A0A', '05')),
    dict(cat='BENCHMARK', t='The 2026 client-services benchmarks',
         d='Industry baselines for sentiment, coverage, account activity and engagement growth, with sources.',
         meta='12 min read', author='Kaizan Labs', date='30 Mar 2026',
         img=cover('#E8DFCB', '#FFB900', '06')),
]

# Blog posts now live as Markdown at content/blog/<slug>/index.md and are loaded
# by tools/blog.py (blog.load_posts()) in main() — no inline POSTS list.


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
    """Cache-busting query string based on the asset's content hash.

    Returns "?v=<hash8>" if the file exists, or "" otherwise. Content-based
    (not mtime) so the value is identical across rebuilds and CI checkouts,
    and changes exactly when the asset itself changes — browsers and the CDN
    refetch only then.
    """
    import hashlib
    f = ROOT / rel
    try:
        return f'?v={hashlib.md5(f.read_bytes()).hexdigest()[:8]}'
    except OSError:
        return ''


def gtm_head_snippet() -> str:
    """Google Consent Mode v2 default state, and the GTM loader itself.

    Per Google's Consent Mode setup guide, the default 'denied' command must
    run before any Google tag's script executes (GTM included), and it should
    always be present (not conditionally injected) so it can receive consent
    updates. What actually fires past that point is decided per-tag:
      - Google's own tags (GA4/Ads tags configured inside the GTM container)
        read these signals automatically.
      - Third-party tags in this container (HubSpot, LinkedIn, ads pixels)
        only respect it if "Additional Consent Checks" is turned on for each
        tag inside the GTM container itself — that's GTM-admin configuration,
        not something this repo controls. See content/RUNBOOK or ask Claude
        for the setup checklist.
    consent.js calls gtag('consent', 'update', …) once a visitor chooses, and
    on every subsequent page view for a returning visitor.
    """
    return dedent('''\
        <!-- Google Consent Mode v2: deny non-essential storage until
             consent.js reads the visitor's saved choice (or they make one). -->
        <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('consent', 'default', {
          'analytics_storage': 'denied',
          'ad_storage': 'denied',
          'ad_user_data': 'denied',
          'ad_personalization': 'denied',
          'functionality_storage': 'denied',
          'personalization_storage': 'denied',
          'security_storage': 'granted'
        });
        </script>
        <!-- Google Tag Manager -->
        <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
        new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        })(window,document,'script','dataLayer','GTM-NCXT2FLQ');</script>
        <!-- End Google Tag Manager -->
        ''')


def page_head(title: str, depth: int, description: str = '', extra_head: str = '') -> str:
    p = relpath(depth)
    desc = description or 'Kaizan: client super intelligence for professional services firms.'
    # Content-hash cache busting: the query changes only when the file does,
    # so caches stay warm between deploys but refresh immediately on change.
    # (Previously disabled, which left visitors on stale CSS/JS after deploys.)
    tokens_v = asset_v('assets/css/tokens.css')
    site_css_v = asset_v('assets/css/site.css')
    site_js_v = asset_v('assets/js/site.js')
    consent_js_v = asset_v('assets/js/consent.js')
    calendly_utm_v = asset_v('assets/js/calendly-utm.js')
    return dedent(f'''\
        <!doctype html>
        <html lang="en">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        {gtm_head_snippet()}
        <title>{E(title)} · Kaizan</title>
        <meta name="description" content="{E(desc)}">
        <link rel="icon" type="image/png" sizes="32x32" href="{p}assets/img/favicon-32x32.png{asset_v('assets/img/favicon-32x32.png')}">
        <link rel="icon" type="image/png" sizes="16x16" href="{p}assets/img/favicon-16x16.png{asset_v('assets/img/favicon-16x16.png')}">
        <link rel="apple-touch-icon" sizes="180x180" href="{p}assets/img/apple-touch-icon.png{asset_v('assets/img/apple-touch-icon.png')}">
        <link rel="mask-icon" href="{p}assets/img/safari-pinned-tab.svg" color="#FFB900">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&display=swap">
        <link rel="stylesheet" href="{p}assets/css/tokens.css{tokens_v}">
        <link rel="stylesheet" href="{p}assets/css/site.css{site_css_v}">
        <script defer src="{p}assets/js/site.js{site_js_v}"></script>
        {extra_head}
        <!-- Calendly attribution: both UK and /us/ book via Calendly. -->
        <script defer src="{p}assets/js/calendly-utm.js{calendly_utm_v}"></script>
        <!-- HubSpot's own direct tracking script loads only after cookie
             consent for Marketing (see assets/js/consent.js), which also
             sends Consent Mode updates for GTM's own tags. -->
        <script defer src="{p}assets/js/consent.js{consent_js_v}"></script>
        </head>
        <body>
        <div class="kz-page">
        <main class="kz-main">
        ''')


def cookie_consent_html() -> str:
    """Cookie consent dialog markup (Consent / Details / About tabs, per-
    category toggles). Behavior lives in assets/js/consent.js, styles in
    assets/css/site.css (.cb-* rules) — both loaded by page_head() on every
    page, so this only needs to emit the dialog itself."""
    return '''
<div class="cb-overlay" id="cb-overlay" hidden>
  <div class="cb-dialog" id="cb-dialog" role="dialog" aria-modal="true" aria-labelledby="cb-title" tabindex="-1">
    <div class="cb-head">
      <span class="cb-logo-lockup"><img class="cb-logo-icon" src="https://kaizan.ai/assets/img/kaizan-icon.png" alt="" width="36" height="36"><img class="cb-logo-img" src="https://kaizan.ai/assets/img/kaizan-logo.png" alt="Kaizan" width="135" height="24"></span>
    </div>

    <div class="cb-tabs" role="tablist" aria-label="Cookie preferences">
      <button class="cb-tab" role="tab" data-tab="consent" aria-selected="true">Consent</button>
      <button class="cb-tab" role="tab" data-tab="details" aria-selected="false" tabindex="-1">Details</button>
      <button class="cb-tab" role="tab" data-tab="about" aria-selected="false" tabindex="-1">About</button>
    </div>

    <div class="cb-body">
      <section data-panel="consent" role="tabpanel">
        <h2 id="cb-title">This website uses cookies</h2>
        <p>We use cookies to keep the site working, to remember your preferences and to understand which pages are useful so we can improve them. You choose which types to allow. <a href="https://kaizan.ai/privacy-policy/" target="_blank" rel="noopener">Read our privacy policy.</a></p>
      </section>

      <section data-panel="details" role="tabpanel" hidden>
        <div class="cb-cat">
          <div class="cb-cat-top">
            <button class="cb-cat-toggle" aria-expanded="true" aria-controls="cd-necessary"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 4.5 7 9.5l5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>Necessary <span class="cb-count">12</span></button>
            <label class="cb-switch"><input type="checkbox" checked disabled aria-label="Necessary cookies, always on"><span></span></label>
          </div>
          <p class="cb-cat-desc" id="cd-necessary">These cookies keep the site working, for example by remembering your consent choice and keeping forms secure. The site can't work properly without them.</p>
        </div>
        <div class="cb-cat">
          <div class="cb-cat-top">
            <button class="cb-cat-toggle" aria-expanded="true" aria-controls="cd-preferences"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 4.5 7 9.5l5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>Preferences <span class="cb-count">3</span></button>
            <label class="cb-switch"><input type="checkbox" data-cat="preferences" aria-label="Preferences cookies"><span></span></label>
          </div>
          <p class="cb-cat-desc" id="cd-preferences">These remember choices you make, like your language or region, so the site feels familiar next time you visit.</p>
        </div>
        <div class="cb-cat">
          <div class="cb-cat-top">
            <button class="cb-cat-toggle" aria-expanded="true" aria-controls="cd-statistics"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 4.5 7 9.5l5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>Statistics <span class="cb-count">5</span></button>
            <label class="cb-switch"><input type="checkbox" data-cat="statistics" aria-label="Statistics cookies"><span></span></label>
          </div>
          <p class="cb-cat-desc" id="cd-statistics">These collect anonymous information about how visitors use the site, so we can see what works and fix what doesn't.</p>
        </div>
        <div class="cb-cat">
          <div class="cb-cat-top">
            <button class="cb-cat-toggle" aria-expanded="true" aria-controls="cd-marketing"><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M2 4.5 7 9.5l5-5" fill="none" stroke="currentColor" stroke-width="2"/></svg>Marketing <span class="cb-count">8</span></button>
            <label class="cb-switch"><input type="checkbox" data-cat="marketing" aria-label="Marketing cookies"><span></span></label>
          </div>
          <p class="cb-cat-desc" id="cd-marketing">These measure how well our campaigns perform and show you relevant ads on other websites.</p>
        </div>
      </section>

      <section data-panel="about" role="tabpanel" hidden>
        <p>Cookies are small text files that websites store on your device. Some are essential; others help us remember your settings or understand how the site is used.</p>
        <p>Your choice is remembered for this browser. You can change or withdraw it at any time using <strong>Cookie settings</strong> in the page footer.</p>
        <p>For details on who we share data with and how long we keep it, see our <a href="https://kaizan.ai/privacy-policy/" target="_blank" rel="noopener">privacy policy</a>.</p>
      </section>
    </div>

    <div class="cb-foot" data-foot="consent">
      <button class="cb-btn fill" data-act="reject">Reject all</button>
      <button class="cb-btn line" data-act="manage">Manage cookies &rsaquo;</button>
      <button class="cb-btn fill" data-act="accept">Allow all cookies</button>
    </div>
    <div class="cb-foot" data-foot="details" hidden>
      <button class="cb-btn fill" data-act="reject">Reject all</button>
      <button class="cb-btn line" data-act="selection">Allow selection</button>
      <button class="cb-btn fill" data-act="accept">Allow all cookies</button>
    </div>
  </div>
</div>
'''


def page_foot() -> str:
    # No GTM <noscript> iframe: its pageview pixel can't be gated by
    # Consent Mode the way the tag-level checks in the container can.
    return ('</main>\n</div>\n' +
            cookie_consent_html() +
            '</body>\n</html>\n')


def nav_html(depth: int, active: str | None = None, with_mega: bool = True) -> str:
    p = relpath(depth)
    items_html = []
    for label, target in NAV:
        # Personas dropdown: hover-triggered, single column, absolute URLs.
        if target == '__personas_dropdown__':
            persona_links = '\n'.join(
                f'<a class="kz-mega-link" href="/for/{slug}/">{E(name)}</a>'
                for slug, name in PERSONA_LIST
            )
            items_html.append(
                '<span class="kz-mega-wrap" data-mega-menu '
                'style="position:relative;display:inline-block;">'
                '<a class="kz-mega-trigger" aria-expanded="false">'
                'Personas <span class="kz-mega-caret">▾</span></a>'
                '<div class="kz-mega-panel kz-mega-panel--simple" role="menu">'
                f'{persona_links}'
                '</div></span>'
            )
            continue
        # Absolute paths (starting with /) bypass the depth prefix so e.g.
        # the Home link stays as "/" on every page.
        href = target if target.startswith('/') else p + target
        cls = ' class="is-active"' if active == label else ''
        if label == 'Product' and with_mega:
            # Simple hover dropdown listing PRODUCT_MENU (Overview, Integrations).
            # The full mega-menu below stays disabled until the other sub-pages
            # exist; to re-enable it, restore the block in the triple-quoted
            # comment and drop this branch.
            links = '\n'.join(
                f'<a class="kz-drop-link" href="{p}{tgt}">{E(lbl)}</a>'
                for lbl, tgt in PRODUCT_MENU
            )
            trigger_cls = ('kz-mega-trigger is-active'
                           if active in ('Product', 'Integrations')
                           else 'kz-mega-trigger')
            # Keeps its href to /product/ so the trigger is still a real link
            # (and works on mobile, where the panel renders inline).
            items_html.append(f'''
              <span class="kz-mega-wrap" data-mega-menu style="position:relative;display:inline-block;">
                <a class="{trigger_cls}" href="{E(href)}" aria-expanded="false" aria-haspopup="true">
                  Product <span class="kz-mega-caret">▾</span>
                </a>
                <div class="kz-mega-panel kz-drop-panel" role="menu">
                  {links}
                </div>
              </span>''')
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
        elif label == 'Resources' and with_mega:
            links = '\n'.join(
                f'<a class="kz-drop-link" href="{p}{tgt}">{E(lbl)}</a>'
                for lbl, tgt, gl in RESOURCES_MENU
            )
            trigger_cls = 'kz-mega-trigger is-active' if active == label else 'kz-mega-trigger'
            # No href: the trigger only opens the dropdown (matches Personas).
            items_html.append(f'''
              <span class="kz-mega-wrap" data-mega-menu style="position:relative;display:inline-block;">
                <a class="{trigger_cls}" aria-expanded="false" tabindex="0" role="button" aria-haspopup="true">
                  Resources <span class="kz-mega-caret">▾</span>
                </a>
                <div class="kz-mega-panel kz-drop-panel" role="menu">
                  {links}
                </div>
              </span>''')
        else:
            items_html.append(f'<a href="{E(href)}"{cls}>{E(label)}</a>')

    return f'''<header class="kz-nav" role="banner">
      <a class="kz-nav-logo" href="/">
        <img class="icon" src="{p}assets/img/kaizan-icon.png{asset_v('assets/img/kaizan-icon.png')}" alt="">
        <img class="word" src="{p}assets/img/kaizan-logo.png" alt="Kaizan">
      </a>
      <nav class="kz-nav-links" aria-label="Primary">
        {''.join(items_html)}
      </nav>
      <div class="kz-nav-cta">
        <a class="kz-btn kz-btn-ghost" href="https://app.kaizan.ai/">Client log in</a>
        <a class="kz-btn kz-btn-yellow" href="/demo/">Book a demo</a>
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
        ('For', [('Account Manager', f'{p}for/account-manager/'),
                 ('Project Manager', f'{p}for/project-manager/'),
                 ('Leadership', f'{p}for/leadership/'),
                 ('New Business', f'{p}for/new-business/')]),
        ('Company', [('About', f'{p}about/'),
                     # TODO: re-enable "Careers", "Insights", "Clients" once that content is ready.
                     # ('Careers', f'{p}careers/'),
                     ('Security', f'{p}security/'),
                     # ('Insights', f'{p}insights/'),
                     # ('Clients', f'{p}customers/'),
                     ('FAQ', f'{p}faq/')]),
        ('Get in touch', [('Book a demo', '/demo/'), ('Contact', 'mailto:hello@kaizan.ai'),
                          ('LinkedIn', 'https://www.linkedin.com/company/kaizan')]),
    ]
    cols_html = []
    for title, links in cols:
        anchors = '\n'.join(f'<a href="{E(href)}">{E(label)}</a>' for label, href in links)
        cols_html.append(f'<div class="col"><h4>{E(title)}</h4>{anchors}</div>')

    return f'''<footer class="kz-footer">
      <div class="kz-footer-grid">
        <div class="kz-footer-brand logo-light">
          <a class="kz-nav-logo" href="/">
            <img class="icon" src="{p}assets/img/kaizan-icon.png{asset_v('assets/img/kaizan-icon.png')}" alt="">
            <img class="word" src="{p}assets/img/kaizan-logo.png" alt="Kaizan">
          </a>
          <p class="blurb">Client super intelligence for professional services firms.</p>
          <p class="footer-address">Covent Garden, London · Madison Avenue, New York</p>
        </div>
        {''.join(cols_html)}
      </div>
      <div class="kz-footer-bot">
        <span>© 2026 Kaizan Ltd. · <a class="kz-locale-switch" data-locale-switch href="#" hidden></a></span>
        <span>
          <a href="{p}privacy-policy/">Privacy</a> ·
          <a href="{p}license-agreement/">Terms</a> ·
          <a href="{p}cookie-policy/">Cookies</a> ·
          <a href="{p}data-processing-agreement/">DPA</a> ·
          <a href="#" data-cookie-settings>Cookie settings</a>
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
            # `detail` logos keep their grey shades (skip the black silhouette)
            # because they're layered marks that read as a blob when flattened;
            # they also render a touch larger so the detail is readable.
            treat = x.get('treat')  # 'detail' (AMS mark) | 'soft' (Gifta badge) | 'light' (heavy wordmarks)
            img_cls = f' is-{treat}' if treat else ''
            span_cls = ' kz-marquee-logo--lg' if x.get('big') else ''
            # Optional per-logo height (px) and vertical nudge (dy px) for fine
            # optical balancing/alignment.
            rules = []
            if x.get('h'):  rules.append(f'height:{int(x["h"])}px')
            if x.get('dy'): rules.append(f'transform:translateY({int(x["dy"])}px)')
            style = f' style="{";".join(rules)}"' if rules else ''
            return (f'<span class="kz-marquee-logo{span_cls}"{style}>'
                    f'<img class="kz-marquee-img{img_cls}" src="{E(src)}" alt="{E(name)}" loading="lazy">'
                    f'</span>')
        return f'<span class="kz-marquee-text">{E(name)}</span>'

    one_run = ''.join(
        f'<span class="kz-marquee-item">{render_one(x)}<span class="sep">✺</span></span>'
        for x in items
    )
    # Two identical runs + a -50% translate = a seamless loop that scrolls
    # through every logo before repeating. When motion is reduced the animation
    # is off, so we hide run 2 and let run 1 wrap into a static grid — every
    # logo stays visible without scrolling (see site.css).
    run = f'<div class="kz-mq-run">{one_run}</div>'
    return f'''<div class="kz-marquee" aria-hidden="true">
      <div class="kz-marquee-track">{run}{run}</div>
    </div>'''


# Real headshots, keyed by full name. Drop a file in assets/img/people/
# and add an entry here to swap the gradient-initials avatar for a photo.
PEOPLE_PHOTOS = {
    'Mark Raymond':      'mark-raymond.png',
    'Gabriella Krite':   'gabriella-krite.png',
    'Hannah Carthy':     'hannah-carthy.png',
    'Samantha Bessant':  'samantha-bessant.png',
    'Stephen Kerin':     'stephen-kerin.png',
    'Fiona Skilton':     'fiona-skilton.png',
    'Derek Grant':       'derek-grant.png',
    'Brandon Smith':     'brandon-smith.png',
    'Corin Ward':        'corin-ward.png',
    'Adam Hopkinson':    'adam-hopkinson.png',
    'Alex Beddoe':       'alex-beddoe.png',
    'Ada Cavalmoretti':  'ada-cavalmoretti.png',
    'Greg Gifford':      'greg-gifford.png',
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
        ('K', 'Reply drafter',     'Drafted QBR follow-up to Sarah, adds three outcomes from yesterday\'s call.', '2 min ago'),
        ('K', 'Risk watcher',      'Mike has been quiet 21 days. Re-intro draft ready, CC\'d James.',                '14 min ago'),
        ('K', 'Expansion scout',   '"Do you do analytics?" picked up on Tue\'s call. Scoped pitch ready.',         '1 hr ago'),
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

# ── 14-day free trial form (home hero) ───────────────────────────────
# Mailchimp embedded form "Header — trial" (audience 1ea9163949). The inputs use
# the audience's merge-field names; assets/js/trial-form.js submits via JSONP so
# the visitor stays on the page, and fills the hidden UTM fields from the URL.
TRIAL_MC_F_ID = '001aefe5f0'
TRIAL_MC_POST = ('https://kaizan.us6.list-manage.com/subscribe/post'
                 f'?u=b61e5cb1cebf0c30b44ebb455&id=1ea9163949&f_id={TRIAL_MC_F_ID}')
TRIAL_MC_JSON = TRIAL_MC_POST.replace('/subscribe/post?', '/subscribe/post-json?')
TRIAL_MC_HONEYPOT = 'b_b61e5cb1cebf0c30b44ebb455_1ea9163949'
# Tag IDs Mailchimp should apply to every UK trial-form signup (audience 1ea9163949).
# /us/ overrides this to its own tag IDs — see US_TRIAL_TAGS in build_us_locale().
TRIAL_MC_TAGS = '3789537,3789536'

# Hidden attribution fields: (merge tag, URL query parameter that fills it).
TRIAL_UTM_FIELDS = [
    ('UTMSRC', 'utm_source'), ('UTMMED', 'utm_medium'), ('UTMTRM', 'utm_term'),
    ('UTMQRPLC', 'qr_placement'), ('UTMCTA', 'utm_cta'),
    ('UTMCAMP', 'utm_campaign'), ('UTMCONT', 'utm_content'),
    ('UTMCOUNTRY', 'utm_country'),
    ('UTMUSP', 'utm_usp'), ('UTMANGL', 'utm_angle'), ('UTMHOOK', 'utm_hook'),
    ('GCLID', 'gclid'), ('UTMID', 'utm_id'), ('UTMADGRP', 'utm_adgroup'),
]

# Values must match the Mailchimp MMERGE12 dropdown choices exactly.
TRIAL_HEARD_OPTIONS = [
    'Google Search', 'LinkedIn', 'Social Media (Facebook/Instagram/TikTok/YouTube)',
    'AI Tool (Chat GPT/Claude/Gemini)', 'Referral (Friend/Colleague/Word of Mouth)',
    'Email Newsletter', 'Event/Conference', 'Other',
]

CHECK_SVG = ('<svg width="11" height="9" viewBox="0 0 12 10" fill="none">'
             '<path d="M1 5L4.5 8.5L11 1.5" stroke="#000" stroke-width="1.8" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>')

# Signal-map motif in the form's top-right corner (decorative).
TRIAL_SIGNAL_SVG = '''<svg class="kz-trial-art" viewBox="0 0 280 150" aria-hidden="true">
  <circle cx="140" cy="78" r="62" fill="none" stroke="currentColor" stroke-width="0.6" opacity="0.10"/>
  <circle cx="140" cy="78" r="40" fill="none" stroke="currentColor" stroke-width="0.6" opacity="0.18"/>
  <circle cx="140" cy="78" r="22" fill="none" stroke="currentColor" stroke-width="0.6" opacity="0.28"/>
  <g stroke="currentColor" stroke-linecap="round">
    <line x1="140" y1="78" x2="82" y2="38" stroke-width="0.8" opacity="0.32"/>
    <line x1="140" y1="78" x2="58" y2="92" stroke-width="1.6" opacity="0.62"/>
    <line x1="140" y1="78" x2="198" y2="30" stroke-width="1" opacity="0.42"/>
    <line x1="140" y1="78" x2="224" y2="82" stroke-width="1.6" opacity="0.58"/>
    <line x1="140" y1="78" x2="170" y2="128" stroke-width="0.9" opacity="0.36"/>
    <line x1="140" y1="78" x2="98" y2="122" stroke-width="1.1" opacity="0.46"/>
    <line x1="140" y1="78" x2="246" y2="42" stroke-width="0.6" opacity="0.22" stroke-dasharray="2 3"/>
  </g>
  <g fill="currentColor">
    <circle cx="82" cy="38" r="3.5"/><circle cx="198" cy="30" r="2.5"/><circle cx="224" cy="82" r="5"/>
    <circle cx="170" cy="128" r="2.5"/><circle cx="98" cy="122" r="4"/><circle cx="246" cy="42" r="2"/>
  </g>
  <circle cx="58" cy="92" r="6" fill="#FFB900" stroke="currentColor" stroke-width="1.5"/>
  <circle cx="58" cy="92" r="2" fill="currentColor"/>
  <circle cx="198" cy="30" r="9" fill="none" stroke="#FFB900" stroke-width="1.4" opacity="0.7"/>
  <circle cx="140" cy="78" r="9" fill="currentColor"/>
  <circle cx="140" cy="78" r="3.5" fill="#FFB900"/>
  <g fill="#FFB900">
    <circle cx="32" cy="22" r="2"/><circle cx="258" cy="118" r="2.2"/>
    <circle cx="22" cy="108" r="1.4" opacity="0.6"/><circle cx="262" cy="62" r="1.6" opacity="0.65"/>
    <circle cx="48" cy="138" r="1.4" opacity="0.55"/>
  </g>
  <path d="M 14 56 L 18 60 L 14 64 L 10 60 Z" fill="#FFB900" stroke="currentColor" stroke-width="0.8"/>
  <path d="M 268 18 L 272 22 L 268 26 L 264 22 Z" fill="#FFB900" stroke="currentColor" stroke-width="0.8"/>
</svg>'''


def trial_done_inner_html() -> str:
    """The "you're in" confirmation copy shown on the standalone /confirmation/
    page (render_confirmation) that the trial form redirects to on success."""
    return '''<div class="kz-trial-badge"><span class="dot"></span>You&rsquo;re in</div>
          <h2 class="kz-trial-title">Thanks, your free trial is on its way.</h2>
          <p class="kz-trial-sub">Check your inbox, we&rsquo;ll email you the next steps to get your
            14-day trial set up.</p>'''


def trial_hero_copy_html(depth: int) -> str:
    """The hero headline/lede/checks/CTA-stack that sits beside the trial card
    on the home hero. Shared with render_confirmation() so the /confirmation/
    page matches the homepage hero exactly."""
    p = relpath(depth)
    return f'''<div class="kz-hero-copy kz-hero-copy--v2">
        <div class="kz-hero-deco" aria-hidden="true">
          <div class="kz-hero-bubble kz-hero-bubble--blue"><span></span><span></span></div>
          <div class="kz-hero-bubble kz-hero-bubble--teal"><span></span><span></span></div>
          <div class="kz-hero-bubble kz-hero-bubble--gold"><span></span><span></span></div>
          <span class="kz-hero-dot kz-hero-dot--blue"></span>
          <span class="kz-hero-dot kz-hero-dot--teal"></span>
          <span class="kz-hero-dot kz-hero-dot--gold"></span>
          <span class="kz-hero-dot kz-hero-dot--red"></span>
          <span class="kz-hero-dot kz-hero-dot--purple"></span>
          <span class="kz-hero-dot kz-hero-dot--sage"></span>
        </div>
        <div class="kz-hero-copy-inner">
          <h1 class="kz-hero-v2-h1">Turn client conversations into revenue</h1>
          <p class="kz-hero-v2-lede">Kaizan turns every call, email and signal into the next
            best action so you keep every client and grow every account.</p>
          <div class="kz-hero-v2-cta">
            <a class="kz-hero-pill" href="{p}demo/">Book a demo</a>
          </div>
        </div>
      </div>'''


def trial_form_html(depth: int) -> str:
    """The dark "Start your 14-day free trial" card. Company, job title and source
    are revealed once name, email and phone are filled in. Required fields (red
    asterisk) match the Mailchimp audience settings."""
    p = relpath(depth)
    heard = '\n'.join(f'<option value="{E(o)}">{E(o)}</option>' for o in TRIAL_HEARD_OPTIONS)
    utm = '\n'.join(f'<input type="hidden" name="{tag}" id="mce-{tag}" value="" data-utm="{param}">'
                    for tag, param in TRIAL_UTM_FIELDS)
    arrow = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>')
    return f'''<div class="kz-trial" data-trial>
        <form class="kz-trial-form" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form"
              action="{E(TRIAL_MC_POST)}" data-mc-json="{E(TRIAL_MC_JSON)}" method="post" target="_blank">
          <h2 class="kz-trial-title">Start your 14-day free trial</h2>
          <p class="kz-trial-sub">Discover the risks and growth opportunities in your own client
            conversations, benchmarked against best-in-class.</p>
          <div class="kz-trial-fields">
            <div class="kz-trial-row">
              <div class="kz-trial-field">
                <label for="mce-FNAME">First name <span class="req" aria-hidden="true">*</span></label>
                <input id="mce-FNAME" name="FNAME" type="text" placeholder="Jamie" autocomplete="given-name" required>
              </div>
              <div class="kz-trial-field">
                <label for="mce-LNAME">Last name <span class="req" aria-hidden="true">*</span></label>
                <input id="mce-LNAME" name="LNAME" type="text" placeholder="Rivera" autocomplete="family-name" required>
              </div>
            </div>
            <div class="kz-trial-row">
              <div class="kz-trial-field">
                <label for="mce-EMAIL">Work email <span class="req" aria-hidden="true">*</span></label>
                <input id="mce-EMAIL" name="EMAIL" type="email" placeholder="you@company.com" autocomplete="email" required>
              </div>
              <div class="kz-trial-field">
                <label for="mce-PHONE">Phone number <span class="req" aria-hidden="true">*</span></label>
                <input id="mce-PHONE" name="PHONE" type="tel" placeholder="07700 900000" autocomplete="tel" required>
              </div>
            </div>
            <div class="kz-trial-more" data-trial-more>
              <div class="kz-trial-more-inner">
                <div class="kz-trial-row">
                  <div class="kz-trial-field">
                    <label for="mce-COMPNAME">Company name <span class="req" aria-hidden="true">*</span></label>
                    <input id="mce-COMPNAME" name="COMPNAME" type="text" placeholder="Acme &amp; Co." autocomplete="organization" required>
                  </div>
                  <div class="kz-trial-field">
                    <label for="mce-JOBT">Job title <span class="req" aria-hidden="true">*</span></label>
                    <input id="mce-JOBT" name="JOBT" type="text" placeholder="Head of Client Services" autocomplete="organization-title" required>
                  </div>
                </div>
                <div class="kz-trial-field">
                  <label for="mce-MMERGE12">How did you hear about us?</label>
                  <select id="mce-MMERGE12" name="MMERGE12">
                    <option value="">Select an option</option>
                    {heard}
                  </select>
                </div>
              </div>
            </div>
          </div>
          <!-- Attribution: filled from the page URL's UTM parameters by trial-form.js -->
          {utm}
          <!-- Tags Mailchimp applies automatically to every signup from this form -->
          <div hidden><input type="hidden" name="tags" value="{TRIAL_MC_TAGS}"></div>
          <!-- Mailchimp bot-prevention field, keep, do not remove -->
          <div style="position:absolute;left:-5000px;" aria-hidden="true">
            <input type="text" name="{TRIAL_MC_HONEYPOT}" tabindex="-1" value="">
          </div>
          <button type="submit" name="subscribe" class="kz-trial-submit">Start my free trial {arrow}</button>
          <p class="kz-trial-msg" data-trial-msg role="status" aria-live="polite"></p>
          <p class="kz-trial-legal" data-trial-legal>
            By submitting your details to Kaizan you are showing interest in our product and so we may
            contact you from time to time about our product and services. You may unsubscribe from these
            communications at any time. Please review our <a href="{p}privacy-policy/">Privacy Policy</a>
            for information on how to unsubscribe and our privacy practices.
          </p>
        </form>
      </div>'''


def playbooks_sections_html() -> str:
    """Ported 'Playbooks / risk / actions / growth' section. Site font; scroll-synced
    bubble-traveler connectors (assets/js/site.js: initPbConnectors)."""
    return '''<div class="kz-pb" id="sceneRoot">
  <!-- connector A travelers: Playbooks illustration -> One source of truth (left side) -->
  <div class="bubbleTraveler connA" style="background: #2F5FE0; z-index: 1; box-shadow: 0 10px 26px rgba(47,95,224,.4);">
    <span class="travelerLine" style="top: 10px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 18px; right: 16px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connA" style="background: #1FA591; width: 40px; height: 30px; z-index: 1; box-shadow: 0 10px 24px rgba(31,165,145,.4);">
    <span class="travelerLine" style="top: 9px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 16px; right: 14px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connA" style="background: #FFB900; width: 36px; height: 27px; z-index: 1; box-shadow: 0 10px 22px #FFB90066;">
    <span class="travelerLine" style="top: 8px; background: rgba(23,21,17,.55);"></span>
    <span class="travelerLine" style="top: 14px; right: 13px; background: rgba(23,21,17,.4);"></span>
  </div>

  <!-- connector B travelers: One source of truth (left side) -> Every action stays inside Kaizan (right side) -->
  <div class="bubbleTraveler connB" style="background: #1FA591; z-index: 1; box-shadow: 0 10px 24px rgba(31,165,145,.4);">
    <span class="travelerLine" style="top: 10px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 18px; right: 16px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connB" style="background: #7C5CFC; width: 40px; height: 30px; z-index: 1; box-shadow: 0 10px 24px rgba(124,92,252,.4);">
    <span class="travelerLine" style="top: 9px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 16px; right: 14px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connB" style="background: #E8432B; width: 36px; height: 27px; z-index: 1; box-shadow: 0 10px 22px rgba(232,67,43,.4);">
    <span class="travelerLine" style="top: 8px; background: rgba(255,255,255,.75);"></span>
    <span class="travelerLine" style="top: 14px; right: 13px; background: rgba(255,255,255,.55);"></span>
  </div>

  <!-- connector C travelers: Every action stays inside Kaizan -> One view of every client relationship -->
  <div class="bubbleTraveler connC" style="background: #2F5FE0; z-index: 1; box-shadow: 0 10px 26px rgba(47,95,224,.4);">
    <span class="travelerLine" style="top: 10px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 18px; right: 16px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connC" style="background: #E8432B; width: 40px; height: 30px; z-index: 1; box-shadow: 0 10px 24px rgba(232,67,43,.4);">
    <span class="travelerLine" style="top: 9px; background: rgba(255,255,255,.9);"></span>
    <span class="travelerLine" style="top: 16px; right: 14px; background: rgba(255,255,255,.65);"></span>
  </div>
  <div class="bubbleTraveler connC" style="background: #FFB900; width: 36px; height: 27px; z-index: 1; box-shadow: 0 10px 22px #FFB90066;">
    <span class="travelerLine" style="top: 8px; background: rgba(23,21,17,.55);"></span>
    <span class="travelerLine" style="top: 14px; right: 13px; background: rgba(23,21,17,.4);"></span>
  </div>
  <!-- ================= Playbooks that run themselves ================= -->
  <section style="padding: 72px var(--kz-gutter) 96px; overflow: hidden; position: relative; z-index: 2;">
    <div style="max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; gap: 72px;">

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; flex-direction: column; gap: 24px;">
        <h2 style="margin: 0; font-size: 40px; line-height: 1.15; font-weight: 400; color: #000000; letter-spacing: -0.01em;">The work gets done, without your team doing it</h2>
        <p style="margin: 0; font-size: 17px; line-height: 1.6; color: #4A4639; max-width: 46ch;">Kaizan's AI Helpers sit on every client account, handling the admin that used to eat your week:</p>
        <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 4px;">
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Every call, email and chat captured and summarised</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Follow-ups and replies drafted for your approval</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">CRM and project tools updated automatically</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">QBRs and account briefs ready before you ask</span></div>
        </div>
        <a href="/demo/" style="display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 16px; font-weight: 600; color: #171511; border-bottom: 2px solid #FFB900; width: fit-content; padding-bottom: 2px;">Book a demo<svg width="16" height="12" viewBox="0 0 16 12" fill="none"><path d="M1 6H15M15 6L10 1M15 6L10 11" stroke="#171511" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path></svg></a>
      </div>

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; justify-content: center;">
        <div id="launchZoneA" style="position: relative; width: 100%; max-width: 540px; height: 460px;">

          <!-- BOLD themed decorative: glow behind the playbook bubble cluster -->
          <div style="position: absolute; left: -40px; top: -10px; width: 300px; height: 240px; background: radial-gradient(circle, #2F5FE0 0%, transparent 70%); opacity: .2; z-index: 0;"></div>

          <div style="position: absolute; left: -10px; top: 10px; width: 170px; height: 120px; background: #2F5FE0; opacity: 0.88; border-radius: 26px 26px 6px 26px; box-shadow: 0 24px 40px rgba(47,95,224,.4); animation: cardFloat 5.5s ease-in-out infinite; z-index: 0; padding: 20px 22px;">
            <span style="display: block; height: 8px; width: 70%; border-radius: 999px; background: rgba(255,255,255,.85); margin-bottom: 12px;"></span>
            <span style="display: block; height: 8px; width: 45%; border-radius: 999px; background: rgba(255,255,255,.6);"></span>
          </div>
          <div style="position: absolute; right: 10px; bottom: -10px; width: 130px; height: 95px; background: #E8432B; opacity: 0.88; border-radius: 24px 24px 24px 6px; box-shadow: 0 20px 34px rgba(232,67,43,.38); animation: cardFloat 4.8s ease-in-out infinite; animation-delay: .5s; z-index: 0; padding: 16px 18px;">
            <span style="display: block; height: 7px; width: 65%; border-radius: 999px; background: rgba(255,255,255,.85); margin-bottom: 10px;"></span>
            <span style="display: block; height: 7px; width: 40%; border-radius: 999px; background: rgba(255,255,255,.6);"></span>
          </div>

          <div style="position: absolute; left: 0; top: 60px; width: 440px; max-width: 100%; background: #FFFFFF; border-radius: 16px; box-shadow: 0 24px 48px rgba(23,21,17,0.12); padding: 28px; z-index: 2; animation: cardFloat 5.5s ease-in-out infinite;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
              <h3 style="margin: 0; font-size: 22px; font-weight: 600; color: #000000;">Renewal playbook</h3>
              <span style="font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #8C8878; background: #EDE8DA; padding: 6px 10px; border-radius: 999px;">Stage 3 of 5</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 10px;">
              <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px;">
                <span style="flex: none; width: 18px; height: 18px; border-radius: 6px; background: #FFB900; display: flex; align-items: center; justify-content: center;"><svg width="10" height="8" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span>
                <span style="font-size: 14px; color: #171511; text-decoration: line-through; opacity: .6;">Usage review sent</span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px;">
                <span style="flex: none; width: 18px; height: 18px; border-radius: 6px; background: #FFB900; display: flex; align-items: center; justify-content: center;"><svg width="10" height="8" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span>
                <span style="font-size: 14px; color: #171511; text-decoration: line-through; opacity: .6;">Stakeholder map confirmed</span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1.5px solid #FFB900; border-radius: 12px; background: rgba(255,185,0,0.08);">
                <span style="flex: none; width: 18px; height: 18px; border-radius: 6px; border: 2px solid #171511;"></span>
                <span style="font-size: 14px; color: #171511; font-weight: 500;">Draft renewal proposal</span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px; opacity: .5;">
                <span style="flex: none; width: 18px; height: 18px; border-radius: 6px; border: 2px solid #C9C4B4;"></span>
                <span style="font-size: 14px; color: #171511;">Exec sign-off</span>
              </div>
            </div>
          </div>

          <div id="bubbleOriginA" style="position: absolute; right: 36px; top: 0px; width: 1px; height: 1px;"></div>
          <div style="position: absolute; right: 0px; top: 0px; width: 150px; background: #FFFFFF; border-radius: 14px; box-shadow: 0 16px 32px rgba(23,21,17,0.14); padding: 16px 16px 20px; text-align: center; z-index: 3;">
            <div style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); width: 28px; height: 28px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(23,21,17,0.18);"><svg width="14" height="12" viewBox="0 0 14 12" fill="none"><path d="M1.5 6.2L5 9.7L12.5 1.5" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></div>
            <div style="font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase; color: #8C8878; margin: 6px 0 6px;">Owner</div>
            <div style="font-size: 14px; font-weight: 600; color: #000000; margin-bottom: 12px;">Jordan Lee</div>
            <div style="width: 56px; height: 56px; margin: 0 auto; border-radius: 999px; background: #7FB59E; color: #171511; font-size: 18px; font-weight: 700; display: flex; align-items: center; justify-content: center;">JL</div>
          </div>

        </div>
      </div>
    </div>
  </section>

  <!-- ================= One source of truth for every account ================= -->
  <section style="padding: 96px var(--kz-gutter); overflow: hidden; position: relative; z-index: 2;">
    <div style="max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap-reverse; align-items: center; gap: 72px;">

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; justify-content: center;">
        <div id="launchZoneB" style="position: relative; width: 100%; max-width: 540px; height: 340px;">

          <!-- BOLD themed decorative: glow behind the source-of-truth bubble cluster -->
          <div style="position: absolute; left: -40px; top: -30px; width: 280px; height: 220px; background: radial-gradient(circle, #1FA591 0%, transparent 70%); opacity: .2; z-index: 0;"></div>

          <div style="position: absolute; left: -10px; top: -40px; width: 160px; height: 115px; background: #1FA591; opacity: 0.88; border-radius: 26px 26px 26px 6px; box-shadow: 0 20px 36px rgba(31,165,145,.38); animation: bubbleFloat 5.2s ease-in-out infinite; z-index: 0; padding: 18px 20px;">
            <span style="display: block; height: 7px; width: 65%; border-radius: 999px; background: rgba(255,255,255,.88); margin-bottom: 10px;"></span>
            <span style="display: block; height: 7px; width: 42%; border-radius: 999px; background: rgba(255,255,255,.6);"></span>
          </div>
          <div style="position: absolute; left: 200px; top: -10px; width: 64px; height: 48px; background: #FFB900; opacity: 0.92; border-radius: 16px 16px 6px 16px; box-shadow: 0 16px 28px #FFB90066; animation: bubbleFloat 4.3s ease-in-out infinite; animation-delay: .4s; z-index: 0; padding: 8px 10px;">
            <span style="display: block; height: 5px; width: 70%; border-radius: 999px; background: rgba(23,21,17,.45); margin-bottom: 6px;"></span>
            <span style="display: block; height: 5px; width: 45%; border-radius: 999px; background: rgba(23,21,17,.3);"></span>
          </div>

          <div id="bubbleDestA" style="position: absolute; left: 10px; top: 10px; width: 1px; height: 1px;"></div>
          <div style="position: absolute; left: 0px; top: 10px; display: flex; align-items: center; gap: 10px; background: #FFFFFF; border-radius: 999px; padding: 10px 16px; box-shadow: 0 10px 22px rgba(23,21,17,0.1); z-index: 3;">
            <div style="display: flex; height: 10px; width: 64px; border-radius: 999px; overflow: hidden;"><span style="flex: 1; background: #171511;"></span><span style="flex: 1.3; background: #E8432B;"></span><span style="flex: 0.7; background: #EADFB8;"></span></div>
            <span style="font-size: 13px; font-weight: 500; color: #171511; white-space: nowrap;">Risk indicators</span>
          </div>

          <div id="bubbleOriginB" style="position: absolute; left: 20px; top: 90px; width: 1px; height: 1px;"></div>
          <div style="position: absolute; left: 0px; top: 80px; width: 270px; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 40px rgba(23,21,17,0.12); padding: 24px; z-index: 2;">
            <div style="display: flex; align-items: flex-end; gap: 14px; height: 140px; margin-bottom: 16px;">
              <div style="width: 28px; height: 85%; background: #E8432B; border-radius: 6px 6px 0 0; transform-origin: bottom; animation: barGrow .9s ease-out both;"></div>
              <div style="width: 28px; height: 55%; background: #FFB900; border-radius: 6px 6px 0 0; transform-origin: bottom; animation: barGrow .9s ease-out both; animation-delay: .1s;"></div>
              <div style="width: 28px; height: 70%; background: #E8432B; border-radius: 6px 6px 0 0; transform-origin: bottom; animation: barGrow .9s ease-out both; animation-delay: .2s;"></div>
              <div style="width: 28px; height: 35%; background: #FFB900; border-radius: 6px 6px 0 0; transform-origin: bottom; animation: barGrow .9s ease-out both; animation-delay: .3s;"></div>
            </div>
            <div style="font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #8C8878; text-align: center;">Risk distribution</div>
          </div>

          <div style="position: absolute; right: 10px; top: 56px; width: 170px; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 40px rgba(23,21,17,0.12); padding: 22px; z-index: 2; text-align: center;">
            <div style="width: 110px; height: 110px; margin: 0 auto 14px; border-radius: 999px; background: conic-gradient(#7FB59E 0% 82%, #EDE4C6 82% 100%); display: flex; align-items: center; justify-content: center;"><div style="width: 78px; height: 78px; border-radius: 999px; background: #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #000000;">82%</div></div>
            <div style="font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #8C8878;">Renewal confidence</div>
          </div>

        </div>
      </div>

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; flex-direction: column; gap: 24px;">
        <h2 style="margin: 0; font-size: 40px; line-height: 1.15; font-weight: 400; color: #000000; letter-spacing: -0.01em;">Spot risk before your client says a word</h2>
        <p style="margin: 0; font-size: 17px; line-height: 1.6; color: #4A4639; max-width: 46ch;">Kaizan scores every relationship and flags the warning signs early, so you can step in before a renewal is on the line:</p>
        <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 4px;">
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">A best-in-class health score on every account, tracked over time</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Alerts for quiet stakeholders, dipping sentiment and single-threaded relationships</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Recommended next steps for each at-risk client</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">A clear view of revenue at risk across your whole portfolio</span></div>
        </div>
        <a href="/demo/" style="display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 16px; font-weight: 600; color: #171511; border-bottom: 2px solid #FFB900; width: fit-content; padding-bottom: 2px;">Book a demo<svg width="16" height="12" viewBox="0 0 16 12" fill="none"><path d="M1 6H15M15 6L10 1M15 6L10 11" stroke="#171511" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path></svg></a>
      </div>

    </div>
  </section>

  <!-- ================= Every action stays inside Kaizan ================= -->
  <section style="padding: 96px var(--kz-gutter); position: relative; z-index: 2;">
    <div style="max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; gap: 72px;">

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; flex-direction: column; gap: 24px;">
        <h2 style="margin: 0; font-size: 40px; line-height: 1.15; font-weight: 400; color: #000000; letter-spacing: -0.01em;">Recommendations built on 11M+ signal data</h2>
        <p style="margin: 0; font-size: 17px; line-height: 1.6; color: #4A4639; max-width: 46ch;">Kaizan learns from over 11+ million signals of client service data, so every suggestion is grounded in what actually works:</p>
        <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 4px;">
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Forecast-based recommendations for every account</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Every client benchmarked against best-in-class teams</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Insight from every meeting, email and chat in one place</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">No spreadsheets, no guesswork, no relying on memory</span></div>
        </div>
        <a href="/demo/" style="display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 16px; font-weight: 600; color: #171511; border-bottom: 2px solid #FFB900; width: fit-content; padding-bottom: 2px;">Book a demo<svg width="16" height="12" viewBox="0 0 16 12" fill="none"><path d="M1 6H15M15 6L10 1M15 6L10 11" stroke="#171511" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path></svg></a>
      </div>

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; justify-content: center;">
        <div id="launchZone" style="position: relative; width: 100%; max-width: 600px; height: 540px;">

          <!-- BOLD themed decorative: oversized chat bubbles -->
          <div style="position: absolute; right: -30px; top: -20px; width: 320px; height: 260px; background: radial-gradient(circle, #2F5FE0 0%, transparent 70%); opacity: .22; z-index: 0;"></div>

          <div id="bubbleOrigin" style="position: absolute; right: 150px; top: 40px; width: 1px; height: 1px;"></div>
          <div id="bubbleDestB" style="position: absolute; right: 190px; top: 70px; width: 1px; height: 1px;"></div>

          <div style="position: absolute; right: 120px; top: -10px; width: 190px; height: 118px; background: #2F5FE0; border-radius: 30px 30px 30px 8px; box-shadow: 0 26px 44px rgba(47,95,224,.35); animation: bigBob 4.2s ease-in-out infinite; --r: -6deg; z-index: 1; padding: 22px 26px;">
            <span style="display: block; height: 11px; border-radius: 6px; background: rgba(255,255,255,.92); width: 100%;"></span>
            <span style="display: block; height: 11px; border-radius: 6px; background: rgba(255,255,255,.72); width: 76%; margin-top: 10px;"></span>
            <span style="display: block; height: 11px; border-radius: 6px; background: rgba(255,255,255,.55); width: 54%; margin-top: 10px;"></span>
          </div>
          <!-- next to the AI Actions card (right-hand gutter), not stacked on top of it or the assigned-to card -->
          <div style="position: absolute; right: 14px; top: 240px; width: 110px; height: 128px; background: #E8432B; border-radius: 26px 26px 8px 26px; box-shadow: 0 22px 38px rgba(232,67,43,.32); animation: bigBob 4.2s ease-in-out infinite; animation-delay: .5s; --r: 7deg; z-index: 2; padding: 18px 16px;">
            <span style="display: block; height: 10px; border-radius: 6px; background: rgba(255,255,255,.92); width: 100%;"></span>
            <span style="display: block; height: 10px; border-radius: 6px; background: rgba(255,255,255,.65); width: 62%; margin-top: 9px;"></span>
          </div>

          <div style="position: absolute; right: 70px; top: 150px; width: 170px; height: 44px; background: radial-gradient(circle, #FFB900 0%, transparent 72%); opacity: .55; animation: glowPulse 2.2s ease-in-out infinite; z-index: 0;"></div>
          <div style="position: absolute; right: 95px; top: 148px; width: 120px; height: 84px; background: #FFB900; border-radius: 30px 30px 30px 8px; box-shadow: 0 22px 38px rgba(23,21,17,.22); display: flex; align-items: center; justify-content: center; gap: 8px; z-index: 2;">
            <span style="width: 12px; height: 12px; border-radius: 999px; background: #171511; animation: typeDot 1.1s infinite; animation-delay: 0s;"></span>
            <span style="width: 12px; height: 12px; border-radius: 999px; background: #171511; animation: typeDot 1.1s infinite; animation-delay: .15s;"></span>
            <span style="width: 12px; height: 12px; border-radius: 999px; background: #171511; animation: typeDot 1.1s infinite; animation-delay: .3s;"></span>
          </div>


          <div style="position: absolute; left: 10px; bottom: 10px; width: 136px; height: 92px; background: #7C5CFC; border-radius: 8px 30px 30px 30px; box-shadow: 0 20px 34px rgba(124,92,252,.3); animation: bigBob 4.2s ease-in-out infinite; animation-delay: .9s; --r: -4deg; z-index: 0; padding: 16px 20px;">
            <span style="display: block; height: 9px; border-radius: 5px; background: rgba(255,255,255,.9); width: 100%;"></span>
            <span style="display: block; height: 9px; border-radius: 5px; background: rgba(255,255,255,.6); width: 58%; margin-top: 8px;"></span>
          </div>

          <div style="position: absolute; left: 0; top: 130px; width: 460px; max-width: 100%; background: #FFFFFF; border-radius: 16px; box-shadow: 0 24px 48px rgba(23,21,17,0.12); padding: 28px; z-index: 3;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
              <h3 style="margin: 0; font-size: 24px; font-weight: 600; color: #000000;">AI Actions</h3>
              <button style="border: none; background: #FFB900; color: #171511; font-size: 14px; font-weight: 600; padding: 10px 16px; border-radius: 999px; display: flex; align-items: center; gap: 6px; cursor: default;"><svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1V11M1 6H11" stroke="#171511" stroke-width="1.8" stroke-linecap="round"></path></svg>New action</button>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px;"><svg width="12" height="16" viewBox="0 0 12 16" fill="none" style="flex: none;"><circle cx="2" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="14" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="14" r="1.4" fill="#C9C4B4"></circle></svg><div style="flex: 1; min-width: 0;"><div style="font-size: 14px; font-weight: 500; color: #171511; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Draft renewal proposal — Acme Creative</div><div style="height: 6px; border-radius: 999px; background: #EDE8DA; overflow: hidden;"><div style="width: 70%; height: 100%; background: #FFB900;"></div></div></div><div style="flex: none; width: 28px; height: 28px; border-radius: 999px; background: #D8A678; color: #171511; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center;">AC</div></div>
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px;"><svg width="12" height="16" viewBox="0 0 12 16" fill="none" style="flex: none;"><circle cx="2" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="14" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="14" r="1.4" fill="#C9C4B4"></circle></svg><div style="flex: 1; min-width: 0;"><div style="font-size: 14px; font-weight: 500; color: #171511; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Escalate CARE risk — Northwind</div><div style="height: 6px; border-radius: 999px; background: #EDE8DA; overflow: hidden;"><div style="width: 30%; height: 100%; background: #E8432B;"></div></div></div><div style="flex: none; width: 28px; height: 28px; border-radius: 999px; background: #2F5FE0; color: #FFFBF0; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center;">N</div></div>
              <div style="display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid rgba(23,21,17,0.08); border-radius: 12px;"><svg width="12" height="16" viewBox="0 0 12 16" fill="none" style="flex: none;"><circle cx="2" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="2" cy="14" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="2" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="8" r="1.4" fill="#C9C4B4"></circle><circle cx="8" cy="14" r="1.4" fill="#C9C4B4"></circle></svg><div style="flex: 1; min-width: 0;"><div style="font-size: 14px; font-weight: 500; color: #171511; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Prep QBR deck — Stark Industries</div><div style="height: 6px; border-radius: 999px; background: #EDE8DA; overflow: hidden;"><div style="width: 45%; height: 100%; background: #FFB900;"></div></div></div><div style="flex: none; width: 28px; height: 28px; border-radius: 999px; background: #7FB59E; color: #171511; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center;">SI</div></div>
            </div>
          </div>

          <div style="position: absolute; right: 12px; top: 60px; width: 148px; background: #FFFFFF; border-radius: 14px; box-shadow: 0 16px 32px rgba(23,21,17,0.14); padding: 16px 16px 20px; text-align: center; z-index: 4;">
            <div style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); width: 28px; height: 28px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(23,21,17,0.18);"><svg width="14" height="12" viewBox="0 0 14 12" fill="none"><path d="M1.5 6.2L5 9.7L12.5 1.5" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></div>
            <div style="font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase; color: #8C8878; margin: 6px 0 6px;">Assigned to</div>
            <div style="font-size: 14px; font-weight: 600; color: #000000; margin-bottom: 12px;">Priya Shah</div>
            <div style="width: 56px; height: 56px; margin: 0 auto; border-radius: 999px; background: #FFB900; color: #171511; font-size: 18px; font-weight: 700; display: flex; align-items: center; justify-content: center;">PS</div>
          </div>

        </div>
      </div>
    </div>
  </section>

  <!-- ================= One view of every client relationship ================= -->
  <section style="padding: 96px var(--kz-gutter); position: relative; z-index: 2;">
    <div style="max-width: 1240px; margin: 0 auto; display: flex; flex-wrap: wrap-reverse; align-items: center; gap: 72px;">

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; justify-content: center;">
        <div id="revealZone" style="position: relative; width: 100%; max-width: 600px; height: 604px;">

          <div id="bubbleDest" style="position: absolute; left: 110px; top: 60px; width: 1px; height: 1px;"></div>

          <!-- BOLD themed decorative: arrival burst, confetti bubbles -->
          <div style="position: absolute; left: -30px; top: -10px; width: 300px; height: 240px; background: radial-gradient(circle, #E8432B 0%, transparent 70%); opacity: .18; z-index: 0;"></div>

          <div style="position: absolute; left: 10px; top: 0px; width: 210px; height: 128px; background: #2F5FE0; border-radius: 30px 30px 30px 8px; box-shadow: 0 26px 44px rgba(47,95,224,.35); z-index: 2; display: flex; align-items: center; justify-content: center;">
            <svg width="54" height="40" viewBox="0 0 54 40" fill="none"><path d="M2 20L14 31L26 10" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path><path d="M22 20L34 31L52 4" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"></path></svg>
          </div>

          <span style="animation: confetti1 1.8s ease-out infinite; animation-delay: .3s; position: absolute; left: 230px; top: 50px; width: 20px; height: 20px; border-radius: 999px; background: #E8432B; z-index: 2;"></span>
          <span style="animation: confetti2 1.8s ease-out infinite; animation-delay: .6s; position: absolute; left: 240px; top: 100px; width: 16px; height: 16px; border-radius: 999px; background: #FFB900; z-index: 2;"></span>
          <span style="animation: confetti3 1.8s ease-out infinite; animation-delay: .9s; position: absolute; left: 150px; top: 110px; width: 14px; height: 14px; border-radius: 999px; background: #2F5FE0; z-index: 2;"></span>

          <div style="position: absolute; left: 330px; top: 60px; width: 92px; height: 58px; background: #1FA591; border-radius: 22px 22px 22px 6px; box-shadow: 0 14px 24px rgba(31,165,145,.3); display: flex; flex-direction: column; justify-content: center; gap: 6px; padding: 0 14px; z-index: 1;">
            <span style="display: block; height: 7px; border-radius: 4px; background: rgba(255,255,255,.9); width: 100%;"></span>
            <span style="display: block; height: 7px; border-radius: 4px; background: rgba(255,255,255,.6); width: 60%;"></span>
          </div>

          <div style="position: absolute; left: 16px; top: 140px; display: flex; align-items: center; gap: 10px; background: #FFFFFF; border-radius: 999px; padding: 10px 16px; box-shadow: 0 10px 22px rgba(23,21,17,0.1); z-index: 3;">
            <svg width="18" height="14" viewBox="0 0 18 14" fill="none"><path d="M1 7L4.5 10.5L9 3" stroke="#2F5FE0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path><path d="M8 7L11.5 10.5L16 3" stroke="#2F5FE0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg>
            <span style="font-size: 13px; font-weight: 500; color: #171511; white-space: nowrap;">Signal received</span>
          </div>

          <div style="position: absolute; left: 10px; top: 184px; width: 270px; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 40px rgba(23,21,17,0.12); padding: 24px; z-index: 2;">
            <div style="display: flex; align-items: flex-end; gap: 14px; height: 150px; margin-bottom: 16px;">
              <div style="width: 28px; height: 70%; background: #171511; border-radius: 6px 6px 0 0;"></div>
              <div style="width: 28px; height: 100%; background: #FFB900; border-radius: 6px 6px 0 0;"></div>
              <div style="width: 28px; height: 55%; background: #171511; border-radius: 6px 6px 0 0;"></div>
              <div style="width: 28px; height: 40%; background: #FFB900; border-radius: 6px 6px 0 0;"></div>
            </div>
            <div style="font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #8C8878; text-align: center;">CARE score by client</div>
          </div>

          <div style="position: absolute; right: -10px; top: 164px; width: 170px; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 40px rgba(23,21,17,0.12); padding: 22px; z-index: 2; text-align: center;">
            <div style="width: 110px; height: 110px; margin: 0 auto 14px; border-radius: 999px; background: conic-gradient(#2F5FE0 0% 64%, #EDE4C6 64% 100%); display: flex; align-items: center; justify-content: center;"><div style="width: 78px; height: 78px; border-radius: 999px; background: #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #000000;">64%</div></div>
            <div style="font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: #8C8878;">Expansion rate</div>
          </div>

          <div style="position: absolute; left: 10px; top: 394px; width: 430px; max-width: 100%; background: #FFFFFF; border-radius: 16px; box-shadow: 0 20px 40px rgba(23,21,17,0.12); padding: 26px 26px 20px; z-index: 2;">
            <div style="position: relative; height: 24px; margin-bottom: 10px;">
              <div style="position: absolute; left: 0; right: 0; top: 11px; height: 2px; background: #EADFB8;"></div>
              <div style="position: absolute; left: 50%; top: 2px; width: 2px; height: 20px; background: #171511; opacity: 0.4;"></div>
              <span style="position: absolute; left: 4%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
              <span style="position: absolute; left: 12%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 18%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 30%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
              <span style="position: absolute; left: 36%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 47%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
              <span style="position: absolute; left: 50%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
              <span style="position: absolute; left: 53%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 64%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 70%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
              <span style="position: absolute; left: 80%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #FFB900;"></span>
              <span style="position: absolute; left: 95%; top: 2px; width: 9px; height: 9px; border-radius: 999px; background: #171511;"></span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #171511;"><div><div style="font-weight: 600;">0</div><div style="color: #8C8878; font-size: 11px;">Minimum</div></div><div style="text-align: center;"><div style="font-weight: 600;">6.8</div><div style="color: #8C8878; font-size: 11px;">Peer average</div></div><div style="text-align: right;"><div style="font-weight: 600;">10</div><div style="color: #8C8878; font-size: 11px;">Maximum</div></div></div>
          </div>

        </div>
      </div>

      <div style="flex: 1 1 440px; min-width: 320px; display: flex; flex-direction: column; gap: 24px;">
        <h2 style="margin: 0; font-size: 40px; line-height: 1.15; font-weight: 400; color: #000000; letter-spacing: -0.01em;">Turn existing clients into your best growth channel</h2>
        <p style="margin: 0; font-size: 17px; line-height: 1.6; color: #4A4639; max-width: 46ch;">Your clients are already telling you what they want next. Kaizan makes sure you hear it:</p>
        <div style="display: flex; flex-direction: column; gap: 14px; margin-top: 4px;">
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Upsell and cross-sell opportunities flagged the moment they're raised</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Scoped pitches and proposals drafted for you</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Warm re-introductions to dormant contacts</span></div>
          <div style="display: flex; align-items: flex-start; gap: 12px;"><span style="flex: none; width: 22px; height: 22px; border-radius: 999px; background: #FFB900; display: flex; align-items: center; justify-content: center; margin-top: 1px;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path></svg></span><span style="font-size: 16px; line-height: 1.5; color: #171511;">Expansion tracked against each client's goals</span></div>
        </div>
        <a href="/demo/" style="display: inline-flex; align-items: center; gap: 8px; margin-top: 8px; font-size: 16px; font-weight: 600; color: #171511; border-bottom: 2px solid #FFB900; width: fit-content; padding-bottom: 2px;">Book a demo<svg width="16" height="12" viewBox="0 0 16 12" fill="none"><path d="M1 6H15M15 6L10 1M15 6L10 11" stroke="#171511" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path></svg></a>
      </div>
    </div>
  </section>
    </div>'''


def stats_band_html() -> str:
    """Ported black stats band (6 metrics) — no icons/'avg.', bold yellow
    numbers, original-weight title. Inherits the site font."""
    return '''<div class="kz-statsband" style="width: 100%; background: #000000; color: #FFFFFF; position: relative; overflow: hidden;">
  <section style="padding: 60px var(--kz-gutter); position: relative; z-index: 1;">
    <div style="max-width: 1300px; margin: 0 auto; text-align: center;">
      <h2 style="margin: 0 0 56px; font-size: 32px; font-weight: 400; letter-spacing: -0.01em; color: #FFFFFF;">Client teams using Kaizan see significant, measurable results:</h2>

      <div class="kz-statsband-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 44px 40px;">

        <div>
          <div>
            <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px;"><div style="font-size: 62px; font-weight: 800; color: #FFB900;">21%</div></div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Average revenue increase per client</div>
          </div>
        </div>

        <div>
          <div>
            <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px;"><div style="font-size: 62px; font-weight: 800; color: #FFB900;">5.4 hrs</div></div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Admin saved per person, every week</div>
          </div>
        </div>

        <div>
          <div>
            <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px;"><div style="font-size: 62px; font-weight: 800; color: #FFB900;">45%</div></div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Of revenue at risk protected through early signals</div>
          </div>
        </div>

        <div>
          <div>
            <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px;"><div style="font-size: 62px; font-weight: 800; color: #FFB900;">4.8%</div></div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Increase in the addressable upsell pool for existing clients</div>
          </div>
        </div>

        <div>
          <div>
            <div style="display: flex; align-items: baseline; justify-content: center; gap: 6px;"><div style="font-size: 62px; font-weight: 800; color: #FFB900;">23%</div></div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Lower cost to serve each client</div>
          </div>
        </div>

        <div>
          <div>
            <div style="font-size: 62px; font-weight: 800; color: #FFB900;">11M+</div>
            <div style="font-size: 18px; color: #ffffff; margin-top: 8px">Client service data points behind every recommendation</div>
          </div>
        </div>

      </div>
    </div>
  </section>
</div>'''


def render_home() -> str:
    scenes = [
        ('AI Assistant for the team',
         'Joins every call, understands every email, updates your systems. A unified system of intelligence housing what you need to know about every client relationship.'),
        ('AI Helpers on every client',
         "Specialist agents on every account, working 24/7: drafting replies, prepping QBRs, watching for risk, surfacing expansion the moment it lands."),
        ('CARE Model · Relationship health',
         "The four-pillar framework: Client satisfaction, Activity with stakeholders, Relationship strength, Expansion opportunities, scored and tracked on every account."),
        ('Chatbot and MCP',
         "Ask anything in natural language. Connect Kaizan to Claude, ChatGPT or any MCP-aware tool, answers with citations from the source conversations."),
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
         "Sentiment on every stakeholder and thread. Not RAG guesses: evidence pulled from the source conversations."),
        ('A', 'Activity with stakeholders',
         'Every meeting, email and call summarised against the people who matter; CRM kept honest automatically.'),
        ('R', 'Relationship strength',
         'Coverage gaps, dormant contacts, single-threaded risk and warm re-intros, handled before you ask.'),
        ('E', 'Expansion opportunities',
         'Upsell and cross-sell signals surfaced the moment a client raises them, not next quarter.'),
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

    # Carousel quotes: lead with the US case studies (Gravity Global, Searchlab,
    # NP Digital) for the US market push, then the strongest case-study quote
    # from each remaining persona page (same people/photos as the persona heroes).
    carousel_quotes = [
        dict(q='Kaizan is helping us reduce the manual tasks, the ones that take a '
               'long time but are less valuable, so we can focus on our clients.',
             name='Ada Cavalmoretti', role='Group Account Director', co='Gravity Global',
             blog='how-gravity-global-uses-ai-to-see-a-client-relationship-slipping-before-it-is-too-late'),
        dict(q='This tool is an absolute game-changer. Don’t even question it. '
               'It’s money very well spent. An invaluable customer tool.',
             name='Greg Gifford', role='Chief Operating Officer', co='Searchlab',
             blog='lean-mean-and-client-obsessed-what-ai-is-really-changing-inside-agencies'),
        dict(q='We’ve had numerous occasions where we’ve been able to spot and '
               'identify high-risk clients that potentially were going to leave.',
             name='Brandon Smith', role='Managing Director', co='NP Digital',
             blog='how-np-digital-uses-ai-to-strengthen-client-relationships-and-drive'),
    ]
    # Blog post each persona is featured in — powers the card's "Read more" link.
    _persona_blog = {
        'Derek Grant': 'how-tradedoubler-is-driving-20-greater-operational-efficiency-across',
        'Fiona Skilton': 'from-reactive-to-proactive-how-great-client-teams-stay-ahead',
        'Corin Ward': 'how-tradedoubler-is-quantifying-client-conversations-to-power-ai-and',
        'Hannah Carthy': 'cs-leader-quick-fire-q-a-hannah-carthy-verkeer',
        'Adam Hopkinson': 'how-pashn-uses-ai-to-strengthen-client-relationships-protect-revenue',
        'Gabriella Krite': 'how-the-kite-factory-uses-ai-to-unify-client-data-and-improve',
        'Alex Beddoe': 'agency-leaders-who-don-t-move-now-will-be-managing-the-fallout-later',
    }
    _by_quote_name = {pp['quote_name']: pp for pp in PERSONAS.values()}
    for _n in ['Derek Grant', 'Fiona Skilton', 'Corin Ward', 'Hannah Carthy',
               'Adam Hopkinson', 'Gabriella Krite', 'Alex Beddoe']:
        _pp = _by_quote_name[_n]
        carousel_quotes.append(dict(q=_pp['quote_pull'], name=_n,
                                    role=_pp['quote_role'], co=_pp['quote_co'],
                                    blog=_persona_blog.get(_n)))
    # Company logo per quote — shown on the card for credibility.
    company_logo = {
        'Gravity Global': 'gravity-global.svg', 'Searchlab': 'searchlab.png',
        'NP Digital': 'np-digital.png', 'Tradedoubler': 'tradedoubler.png',
        'Collective Content': 'collective-content.svg', 'Verkeer': 'verkeer.png',
        'PASHN': 'pashn-media-agency.svg', 'The Kite Factory': 'the-kite-factory.png',
        'Transmission': 'transmission.png',
    }

    # Per-company logo height (px) so every mark reads at a proportionate size.
    logo_h = {
        'Gravity Global': 52, 'Searchlab': 44, 'NP Digital': 52, 'Tradedoubler': 42,
        'Collective Content': 46, 'Verkeer': 52, 'PASHN': 35,
        'The Kite Factory': 84, 'Transmission': 42,
    }

    def _qcard(cq):
        logo = company_logo.get(cq['co'], '')
        h = logo_h.get(cq['co'], 52)
        inner = (f'<img class="kz-qcard-logo" '
                 f'src="assets/img/clients/{logo}" alt="{E(cq["co"])}">') if logo \
            else f'<span class="kz-qcard-co">{E(cq["co"])}</span>'
        logo_html = f'<span class="kz-qcard-logobox">{inner}</span>'
        more = (f'<a class="kz-qcard-more" href="blog/{cq["blog"]}/">Read more →</a>'
                if cq.get('blog') else '')
        return (f'<figure class="kz-qcard">'
                f'{logo_html}'
                f'<div class="kz-qcard-body"><q>{E(cq["q"])}</q></div>'
                f'<figcaption>{portrait(cq["name"], cq["role"], depth=0)}</figcaption>'
                f'{more}'
                f'</figure>')

    carousel_cards = '\n'.join(_qcard(cq) for cq in carousel_quotes)
    carousel_dots = '\n'.join(
        f'<button class="kz-carousel-dot" type="button" aria-label="Show quote {i + 1}"></button>'
        for i in range(len(carousel_quotes))
    )

    # Headline outcome stats — bold cards above the quote carousel.
    home_stats = [
        ('23%',  'Efficiency', 'Reduce the cost-to-serve each client'),
        ('2×',   'Capability', 'Create unique products, services & insights'),
        ('21%+', 'Revenue',    'Proactive personalised actions for each client'),
    ]
    stats_cards = '\n'.join(
        f'<div class="kz-statcard">'
        f'<div class="kz-statcard-num">{E(num)}</div>'
        f'<div class="kz-statcard-cat">{E(cat)}</div>'
        f'<div class="kz-statcard-desc">{E(desc)}</div>'
        f'</div>'
        for num, cat, desc in home_stats)

    body = f'''
    {nav_html(0, active='Home')}

    <!-- HERO -->
    <section class="kz-hero kz-hero--trial">
      {trial_hero_copy_html(0)}
      <div class="kz-trial-col">
        <span class="kz-trial-bubble" aria-hidden="true"><span></span><span></span></span>
        {trial_form_html(0)}
      </div>
    </section>

    {marquee_html(CLIENT_LOGOS, depth=0)}

    <!-- HERO REEL -->
    <section class="kz-reel-section">
      <div class="kz-reel">
        <video class="kz-reel-video" muted loop playsinline preload="metadata"
               data-play-inview aria-label="Kaizan product overview">
          <source src="assets/video/hero-intro.mp4{asset_v('assets/video/hero-intro.mp4')}" type="video/mp4">
        </video>
      </div>
    </section>

    <!-- WHY KAIZAN -->
    <section class="kz-why">
      <div class="kz-why-inner">
        <h2 class="kz-why-title">Why choose Kaizan&rsquo;s client intelligence?</h2>
        <div class="kz-why-grid">
          <div class="kz-why-card">
            <div class="kz-why-icon kz-why-icon--gold">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="3" stroke="#171511" stroke-width="2"></circle><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" stroke="#171511" stroke-width="2" stroke-linecap="round"></path></svg>
            </div>
            <h3 class="kz-why-card-title">Keep the clients you&rsquo;ve won</h3>
            <p class="kz-why-card-desc">Early warning signals flag at-risk accounts while there&rsquo;s still time to act.</p>
          </div>
          <div class="kz-why-card">
            <div class="kz-why-icon kz-why-icon--blue">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="#FFFFFF" stroke-width="2"></circle><path d="M12 7v5l4 2" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
            </div>
            <h3 class="kz-why-card-title">Get hours back every week</h3>
            <p class="kz-why-card-desc">AI Helpers draft the follow-ups, update your systems and prep the QBRs for you.</p>
          </div>
          <div class="kz-why-card">
            <div class="kz-why-icon kz-why-icon--teal">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" stroke="#FFFFFF" stroke-width="2"></rect><circle cx="12" cy="12" r="3" stroke="#FFFFFF" stroke-width="2"></circle><path d="M6 9.5v5M18 9.5v5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"></path></svg>
            </div>
            <h3 class="kz-why-card-title">Unlock revenue hidden in your accounts</h3>
            <p class="kz-why-card-desc">Upsell and cross-sell signals surface the moment a client mentions them.</p>
          </div>
          <div class="kz-why-card">
            <div class="kz-why-icon kz-why-icon--red">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9.5 3.5c-1.7 0-3 1.3-3 3 0 .3 0 .6.1.9A3 3 0 005 12.5c0 1.2.7 2.2 1.7 2.7-.1.3-.2.6-.2 1 0 1.7 1.3 3 3 3 .5 0 1-.1 1.4-.4" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path><path d="M14.5 3.5c1.7 0 3 1.3 3 3 0 .3 0 .6-.1.9A3 3 0 0119 12.5c0 1.2-.7 2.2-1.7 2.7.1.3.2.6.2 1 0 1.7-1.3 3-3 3-.5 0-1-.1-1.4-.4" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"></path><path d="M11 4v15M13 4v15" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"></path></svg>
            </div>
            <h3 class="kz-why-card-title">11M+ points of client service signals</h3>
            <p class="kz-why-card-desc">Actions suggested are based on 11M+ industry signals.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- PLAYBOOKS / RISK / ACTIONS / GROWTH (replaces product tour) -->
    {playbooks_sections_html()}

    <!-- CARE -->
    <section class="kz-section">
      <div class="kz-eyebrow">The CARE framework · the source of truth for your client relationships</div>
      <h2 class="kz-h2" style="margin-top:12px;max-width:880px;">
        AI Helpers working 24/7 to grow every client relationship.
      </h2>
      <div class="kz-care">{care_html}</div>
    </section>

    <!-- PERSONAS -->
    <section class="kz-personas">
      <h2 class="kz-h2" style="margin-bottom:8px;">I am a…</h2>
      <p class="kz-lede" style="margin-bottom:28px;max-width:640px;font-size:16px;">
        Pick your role to see how Kaizan fits into your week - personalised guidance, real use cases and daily workflows.
      </p>
      <div class="kz-personas-grid">{persona_pills}</div>
    </section>

    <!-- IMPACT STATS (ported black band) -->
    {stats_band_html()}

    <!-- PROOF -->
    <!-- QUOTE CAROUSEL -->
    <section class="kz-quotes">
      <div class="kz-quotes-head">
        <div class="kz-eyebrow">In their words</div>
        <h2 class="kz-quotes-title">What our clients say</h2>
      </div>
      <div class="kz-carousel" data-carousel>
        <button class="kz-carousel-arrow is-prev" type="button" data-carousel-prev aria-label="Previous quote">&lsaquo;</button>
        <div class="kz-carousel-viewport" data-carousel-viewport>
          {carousel_cards}
        </div>
        <button class="kz-carousel-arrow is-next" type="button" data-carousel-next aria-label="Next quote">&rsaquo;</button>
      </div>
      <div class="kz-carousel-dots" data-carousel-dots>{carousel_dots}</div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band">
      <h2 class="head">See your clients, clearly.</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="/demo/">Book a demo</a>
      </div>
    </section>

    {footer_html(0)}
    '''
    extra_head = (f'<script defer src="assets/js/trial-form.js'
                  f'{asset_v("assets/js/trial-form.js")}"></script>')
    return page_head('Client super intelligence for client service teams', 0,
                     'Kaizan is the AI platform for client service professionals, '
                     'AI Helpers that work 24/7 to grow client ROI, satisfaction and revenue.',
                     extra_head=extra_head) + body + page_foot()


def _cs_stats_band_html() -> str:
    """Updated stats band (icon + 'avg.' label + white numbers) from the
    design artifact's Section5-Stats — replaces stats_band_html()'s plain
    bold-yellow-number version for this page only."""
    stats = [
        ('<rect x="4" y="3" width="14" height="18" rx="2" stroke="#FFB900" stroke-width="1.8"/>'
         '<path d="M8 8h6M8 12h6M8 16h3" stroke="#FFB900" stroke-width="1.8" stroke-linecap="round"/>'
         '<path d="M17 15l3 3-3 3" stroke="#FFB900" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
         'avg.', '21%', 'Average revenue increase per client'),
        ('<circle cx="12" cy="12" r="9" stroke="#FFB900" stroke-width="1.8"/>'
         '<path d="M12 7v5l4 2" stroke="#FFB900" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
         'avg.', '5.4 hrs', 'Admin saved per person, every week'),
        ('<circle cx="12" cy="12" r="9" stroke="#FFB900" stroke-width="1.8"/>'
         '<circle cx="12" cy="12" r="5" stroke="#FFB900" stroke-width="1.8"/>'
         '<circle cx="12" cy="12" r="1.4" fill="#FFB900"/>',
         'avg.', '45%', 'Of revenue at risk protected through early signals'),
        ('<path d="M4 15a8 8 0 0116 0" stroke="#FFB900" stroke-width="1.8"/>'
         '<path d="M4 15h16v3a2 2 0 01-2 2H6a2 2 0 01-2-2v-3z" stroke="#FFB900" stroke-width="1.8" stroke-linejoin="round"/>',
         'avg.', '4.8%', 'Increase in the addressable upsell pool for existing clients'),
        ('<path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" stroke="#FFB900" stroke-width="1.6" stroke-linejoin="round"/>',
         'avg.', '23%', 'Lower cost to serve each client'),
        ('<path d="M8 21h8M12 17v4M6 4h12v3a6 6 0 01-12 0V4z" stroke="#FFB900" stroke-width="1.8" stroke-linejoin="round"/>'
         '<path d="M6 6H3a3 3 0 003 3M18 6h3a3 3 0 01-3 3" stroke="#FFB900" stroke-width="1.8" stroke-linecap="round"/>',
         None, '11M+', 'Client service data points behind every recommendation'),
    ]

    def _stat(icon, avg_label, num, desc):
        avg_html = (f'<span style="font-size:14px;font-weight:600;color:rgba(255,255,255,.55);">{E(avg_label)}</span>'
                    if avg_label else '')
        return (f'<div><svg width="30" height="30" viewBox="0 0 24 24" fill="none" '
                f'style="margin:0 auto 14px;">{icon}</svg>'
                f'<div style="display:flex;align-items:baseline;justify-content:center;gap:6px;">'
                f'{avg_html}<div style="font-size:46px;font-weight:700;color:#FFFFFF;">{E(num)}</div></div>'
                f'<div style="font-size:17px;color:#ffffff;margin-top:6px;">{E(desc)}</div></div>')

    grid = '\n'.join(_stat(*s) for s in stats)
    return f'''<div class="kz-statsband" style="width: 100%; background: #000000; color: #FFFFFF; position: relative; overflow: hidden;">
  <section style="padding: 96px var(--kz-gutter); position: relative; z-index: 1;">
    <div style="max-width: 1100px; margin: 0 auto; text-align: center;">
      <h2 style="margin: 0 0 56px; font-size: 32px; font-weight: 400; letter-spacing: -0.01em; color: #FFFFFF;">Client teams using Kaizan see significant, measurable results:</h2>
      <div class="kz-statsband-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 48px 32px;">{grid}</div>
    </div>
  </section>
</div>'''


def _cs_lets_talk_html() -> str:
    """'Let's talk' closer — 3 benefit cards + a Book a demo CTA."""
    cards = [
        ('var(--kz-yellow)', '#FFFFFF', 'Protects the revenue you already have'),
        ('#7FB59E', '#FFFFFF', 'Gives your team their week back'),
        ('#2F5FE0', '#FFFFFF', 'Unlocks growth inside existing accounts'),
    ]
    cards_html = '\n'.join(
        f'<div class="cs-lt-card" style="background:{bg};color:{fg}">{E(text)}</div>'
        for bg, fg, text in cards
    )
    arrow = ('<svg width="16" height="12" viewBox="0 0 16 12" fill="none" aria-hidden="true">'
             '<path d="M1 6H15M15 6L10 1M15 6L10 11" stroke="currentColor" stroke-width="1.6" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return f'''<section class="cs-lets-talk">
      <div class="cs-lt-inner">
        <h2 class="cs-lt-title">Let&rsquo;s talk</h2>
        <p class="cs-lt-sub">3 ways Kaizan helps your client-facing team</p>
        <div class="cs-lt-grid">{cards_html}</div>
        <a class="kz-btn kz-btn-black cs-lt-cta" href="/demo/">Book a demo {arrow}</a>
      </div>
    </section>'''


def _cs_modules_html() -> str:
    """'Explore everything Kaizan does' module carousel. Reuses the site's
    existing generic carousel engine (initQuoteCarousel in site.js runs
    against any [data-carousel] root), so prev/next/dots/drag/auto-advance
    all work with no extra JS."""
    modules = [
        ('AI Assistant', 'Joins every call and keeps your systems up to date', '''
          <div style="width:100%;height:150px;background:#171511;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:14px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:8px;">
            <div style="background:#2A2620;border-radius:8px;display:flex;align-items:center;justify-content:center;"><div style="width:30px;height:30px;border-radius:999px;background:#D8D2BE;color:#171511;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;">JL</div></div>
            <div style="background:#2A2620;border-radius:8px;display:flex;align-items:center;justify-content:center;"><div style="width:30px;height:30px;border-radius:999px;background:#2F5FE0;color:#FFFFFF;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;">AC</div></div>
            <div style="background:#2A2620;border-radius:8px;display:flex;align-items:center;justify-content:center;"><div style="width:30px;height:30px;border-radius:999px;background:#7FB59E;color:#171511;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center;">N</div></div>
            <div style="background:var(--kz-yellow);border-radius:8px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;box-shadow:0 0 0 2px #FFFFFF inset;">
              <img src="/assets/img/kaizan-icon.png" alt="" style="width:24px;height:24px;border-radius:6px;">
              <span style="font-size:8px;font-weight:700;color:#171511;">Kaizan joined</span>
            </div>
          </div>'''),
        ('AI Helpers', 'Specialist helpers working 24/7 on every client', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;gap:10px;justify-content:center;">
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:var(--kz-yellow);display:flex;align-items:center;justify-content:center;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span style="font-size:12px;">Reply drafted &mdash; Acme Creative</span></div>
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:var(--kz-yellow);display:flex;align-items:center;justify-content:center;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span style="font-size:12px;">QBR brief compiled &mdash; Northwind</span></div>
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:#EDE4C6;display:flex;align-items:center;justify-content:center;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none"><path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.4.3.5.8.5 1.3V16h6v-.8c0-.5.1-1 .5-1.3A6 6 0 0012 3z" stroke="#8C8878" stroke-width="1.8" stroke-linejoin="round"/></svg></span><span style="font-size:12px;color:#8C8878;">Suggested: re-engage Stark Industries</span></div>
          </div>'''),
        ('Client Health Score', 'Relationship health on every account', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:14px 18px;display:flex;flex-direction:column;align-items:center;gap:4px;">
            <div style="align-self:flex-start;font-size:13px;font-weight:700;color:#171511;">Health Score</div>
            <div style="width:88px;height:88px;border-radius:999px;background:conic-gradient(#1FA591 0% 84%,#E3EDE9 84% 100%);display:flex;align-items:center;justify-content:center;">
              <div style="width:70px;height:70px;border-radius:999px;background:#FFFFFF;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;">
                <div style="font-size:20px;font-weight:800;color:#171511;">8.4</div>
                <div style="font-size:8px;font-weight:700;color:#1FA591;background:rgba(31,165,145,.15);padding:2px 7px;border-radius:999px;">THRIVING</div>
              </div>
            </div>
          </div>'''),
        ('Client News', 'Every conversation and commitment in one view', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;gap:10px;justify-content:center;">
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:var(--kz-yellow);display:flex;align-items:center;justify-content:center;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span style="font-size:13px;">Agenda drafted</span></div>
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:var(--kz-yellow);display:flex;align-items:center;justify-content:center;"><svg width="12" height="10" viewBox="0 0 12 10" fill="none"><path d="M1 5L4.2 8.2L11 1" stroke="#171511" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span style="font-size:13px;">Metrics compiled</span></div>
            <div style="display:flex;align-items:center;gap:10px;"><span style="width:24px;height:24px;border-radius:999px;background:#EDE4C6;"></span><span style="font-size:13px;color:#8C8878;">Deck exported</span></div>
          </div>'''),
        ('Risk Watcher', "Early warnings before a client leaves", '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;gap:10px;justify-content:center;">
            <div style="display:flex;align-items:center;gap:8px;"><span style="width:20px;height:20px;border-radius:999px;background:#E8432B;display:flex;align-items:center;justify-content:center;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M12 3L2 20h20L12 3z" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/></svg></span><span style="font-size:12px;color:#171511;">Acme Creative &mdash; sentiment dropping</span></div>
            <div style="display:flex;align-items:center;gap:8px;"><span style="width:20px;height:20px;border-radius:999px;background:var(--kz-yellow);display:flex;align-items:center;justify-content:center;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M12 3L2 20h20L12 3z" stroke="#171511" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v5" stroke="#171511" stroke-width="2" stroke-linecap="round"/></svg></span><span style="font-size:12px;color:#171511;">Northwind &mdash; renewal in 14 days</span></div>
            <div style="display:flex;align-items:center;gap:8px;"><span style="width:20px;height:20px;border-radius:999px;background:#E8432B;display:flex;align-items:center;justify-content:center;"><svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M12 3L2 20h20L12 3z" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/><path d="M12 9v5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/></svg></span><span style="font-size:12px;color:#171511;">Stark Industries &mdash; champion left</span></div>
          </div>'''),
        ('Expansion Scout', 'Upsell signals the moment they land', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;justify-content:center;gap:10px;">
            <div style="display:flex;align-items:flex-end;gap:8px;height:70px;">
              <div style="width:20px;height:35%;background:#EDE4C6;border-radius:4px 4px 0 0;"></div>
              <div style="width:20px;height:50%;background:#EDE4C6;border-radius:4px 4px 0 0;"></div>
              <div style="width:20px;height:68%;background:#7FB59E;border-radius:4px 4px 0 0;"></div>
              <div style="width:20px;height:100%;background:#7FB59E;border-radius:4px 4px 0 0;"></div>
            </div>
            <div style="font-size:11px;background:rgba(127,181,158,.18);color:#171511;font-weight:600;padding:5px 9px;border-radius:999px;width:fit-content;">&#9650; +$42k opportunity flagged</div>
          </div>'''),
        ('Reply Drafter', 'Follow-ups written in your voice', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;gap:8px;justify-content:center;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;"><span style="width:20px;height:20px;border-radius:999px;background:#2F5FE0;color:#FFFBF0;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;">JL</span><span style="font-size:12px;font-weight:600;color:#171511;">Reply to Jordan Lee</span></div>
            <div style="height:6px;border-radius:999px;background:#EDE4C6;width:95%;"></div>
            <div style="height:6px;border-radius:999px;background:#EDE4C6;width:80%;"></div>
            <div style="height:6px;border-radius:999px;background:#EDE4C6;width:60%;"></div>
            <div style="font-size:11px;color:#2F5FE0;font-weight:600;margin-top:4px;">&check; Draft ready for review</div>
          </div>'''),
        ('QBR Builder', 'Review decks compiled from real conversations', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;align-items:center;justify-content:center;gap:10px;">
            <div style="width:54px;height:76px;background:#EDE4C6;border-radius:6px;transform:rotate(-8deg);"></div>
            <div style="width:58px;height:82px;background:#7C5CFC;border-radius:6px;box-shadow:0 10px 20px rgba(124,92,252,.3);display:flex;align-items:center;justify-content:center;z-index:1;"><svg width="26" height="20" viewBox="0 0 26 20" fill="none"><rect x="1" y="12" width="4" height="7" fill="#FFFFFF" opacity=".8"/><rect x="7" y="7" width="4" height="12" fill="#FFFFFF"/><rect x="13" y="10" width="4" height="9" fill="#FFFFFF" opacity=".8"/><rect x="19" y="3" width="4" height="16" fill="#FFFFFF"/></svg></div>
            <div style="width:54px;height:76px;background:#EDE4C6;border-radius:6px;transform:rotate(8deg);"></div>
          </div>'''),
        ('Stakeholder Map', "See who matters and who's gone quiet", '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
            <div style="display:flex;gap:14px;align-items:center;">
              <div style="width:36px;height:36px;border-radius:999px;background:#1FA591;color:#FFFFFF;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px rgba(31,165,145,.3);">JL</div>
              <div style="width:36px;height:36px;border-radius:999px;background:#D8D2BE;color:#8C8878;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;">PS</div>
              <div style="width:36px;height:36px;border-radius:999px;background:#2F5FE0;color:#FFFFFF;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px rgba(47,95,224,.3);">AC</div>
              <div style="width:36px;height:36px;border-radius:999px;background:#D8D2BE;color:#8C8878;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;">NW</div>
            </div>
            <div style="font-size:11px;color:#8C8878;">2 stakeholders gone quiet</div>
          </div>'''),
        ('Ask Kaizan', 'Ask anything about any client and get cited answers', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;gap:8px;justify-content:center;">
            <div style="align-self:flex-end;max-width:80%;background:#171511;color:#FFFBF0;font-size:11px;padding:7px 11px;border-radius:999px 999px 4px 999px;">Is Acme at risk?</div>
            <div style="max-width:88%;background:#EDE4C6;color:#171511;font-size:11px;line-height:1.4;padding:7px 11px;border-radius:999px 999px 999px 4px;">Yes &mdash; sentiment dropped 18% <span style="color:#8C8878;">[Oct 3 call]</span></div>
          </div>'''),
        ('My Voice', 'Writes emails in your tone of voice', '''
          <div style="width:100%;height:150px;background:#FFFFFF;border-radius:12px;box-shadow:0 16px 32px rgba(23,21,17,.1);padding:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
            <div style="display:flex;align-items:center;gap:4px;height:44px;">
              <div style="width:4px;height:40%;background:#171511;border-radius:999px;"></div>
              <div style="width:4px;height:70%;background:#171511;border-radius:999px;"></div>
              <div style="width:4px;height:100%;background:var(--kz-yellow);border-radius:999px;"></div>
              <div style="width:4px;height:55%;background:#171511;border-radius:999px;"></div>
              <div style="width:4px;height:85%;background:var(--kz-yellow);border-radius:999px;"></div>
              <div style="width:4px;height:35%;background:#171511;border-radius:999px;"></div>
              <div style="width:4px;height:65%;background:#171511;border-radius:999px;"></div>
              <div style="width:4px;height:90%;background:var(--kz-yellow);border-radius:999px;"></div>
              <div style="width:4px;height:45%;background:#171511;border-radius:999px;"></div>
            </div>
            <div style="font-size:11px;color:#8C8878;">96% match to your tone</div>
          </div>'''),
    ]
    cards_html = '\n'.join(
        f'<div class="cs-modcard">{visual}'
        f'<div class="cs-modcard-title">{E(title)}</div>'
        f'<p class="cs-modcard-desc">{E(desc)}</p></div>'
        for title, desc, visual in modules
    )
    dots_html = '\n'.join(
        f'<button class="kz-carousel-dot" type="button" aria-label="Show module {i + 1}"></button>'
        for i in range(len(modules))
    )
    return f'''<section class="cs-modules">
      <div class="cs-modules-inner">
        <div class="cs-modules-head">
          <h2 class="cs-modules-title">Explore everything Kaizan does</h2>
        </div>
        <div class="kz-carousel" data-carousel>
          <button class="kz-carousel-arrow is-prev" data-carousel-prev type="button" aria-label="Previous module">&lsaquo;</button>
          <div class="kz-carousel-viewport" data-carousel-viewport>{cards_html}</div>
          <button class="kz-carousel-arrow is-next" data-carousel-next type="button" aria-label="Next module">&rsaquo;</button>
        </div>
        <div class="kz-carousel-dots" data-carousel-dots>{dots_html}</div>
      </div>
    </section>'''


def _cs_integrations_faq_html() -> str:
    """'Works with the tools you already use' icon grid + an FAQ accordion.
    The accordion uses native <details>/<summary> — no JS needed."""
    icons_html = '\n'.join(
        f'<div class="cs-int-icon"><div class="cs-int-icon-box">{INT_LOGOS.get(i["k"], "")}</div>'
        f'<div class="cs-int-icon-label">{E(i["name"])}</div></div>'
        for i in INT_DATA
    )
    faqs = [
        ('Is AI built into Kaizan, or is it an add-on?',
         'AI is the core of Kaizan. Your Helpers work from day one, capturing '
         'conversations, drafting follow-ups and flagging risk and opportunity '
         'without any extra setup.'),
        ('How does Kaizan help prevent client churn?',
         "Kaizan scores the health of every relationship and watches for early "
         "warning signs, like a quiet stakeholder or falling sentiment. You get "
         "an alert and a recommended next step while there's still time to act."),
        ('How much time will my team save?',
         'On average, 5.4 hours per person per week. Kaizan handles meeting '
         'notes, follow-ups, system updates and report prep, so your team can '
         'spend that time with clients.'),
        ('How does Kaizan find upsell opportunities?',
         'It listens for buying signals across every meeting, email and chat, '
         'such as a client asking "do you do analytics?". It then flags the '
         'opportunity and drafts a scoped pitch. Teams see an average 4.8% '
         'increase in their addressable upsell pool.'),
        ('What are the recommendations based on?',
         "Kaizan's forecasts draw on over 11 million points of client service "
         "data, benchmarked against best-in-class client teams, plus the "
         "conversations from your own accounts."),
    ]
    plus = ('<svg class="cs-faq-plus" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">'
            '<path d="M9 2v14M2 9h14" stroke="var(--kz-yellow)" stroke-width="2" stroke-linecap="round"/></svg>')
    faq_html = '\n'.join(
        f'<details class="cs-faq-item">'
        f'<summary class="cs-faq-summary"><span>{E(q)}</span>{plus}</summary>'
        f'<p class="cs-faq-body">{E(a)}</p>'
        f'</details>'
        for q, a in faqs
    )
    return f'''<section class="cs-integrations">
      <div class="cs-int-inner">
        <h2 class="cs-int-title">Works with the tools you already use</h2>
        <div class="cs-int-grid">{icons_html}</div>
      </div>
      <div class="cs-faq-inner">
        <h2 class="cs-faq-title">Frequently asked questions</h2>
        {faq_html}
      </div>
    </section>'''


def render_customer_success_software() -> str:
    """SEO landing page at /customer-success-software/ — a replica of the
    homepage (render_home) targeting the 'customer success software' search
    term. Same design/content throughout, minus the CARE, Personas and
    closing-CTA sections (stripped below); only the <title> and meta
    description otherwise differ, swapped in after the fact so the page can
    never drift from the homepage it mirrors.

    render_home()'s markup is written for a page living at the site root (its
    asset/internal links are root-relative, e.g. "assets/...", "demo/"), but
    this page is one folder down. A <base href="/"> makes every one of those
    links resolve against the site root regardless, so the output needs no
    further rewriting."""
    html = render_home()
    html = html.replace(
        '<title>Client super intelligence for client service teams · Kaizan</title>',
        '<base href="/">\n        <title>Customer Success Software · Kaizan</title>',
        1,
    )
    html = html.replace(
        'content="Kaizan is the AI platform for client service professionals, '
        'AI Helpers that work 24/7 to grow client ROI, satisfaction and revenue."',
        'content="Kaizan is customer success software that turns every call, email '
        'and signal into the next best action, AI Helpers that work 24/7 to grow '
        'client ROI, satisfaction and revenue."',
        1,
    )
    # Drop the CARE, Personas and closing-CTA sections for this landing page —
    # each <section> is self-contained (no nested <section> tags), so a
    # non-greedy match up to the next </section> is safe.
    for marker in ('<!-- CARE -->', '<!-- PERSONAS -->', '<!-- CTA -->'):
        html = re.sub(
            re.escape(marker) + r'\s*<section\b.*?</section>\s*',
            '',
            html,
            count=1,
            flags=re.S,
        )
    html = html.replace(
        '<div class="kz-eyebrow">In their words</div>', '', 1,
    )
    # (The Risk/Growth donut-ring swap that used to be hacked in here via
    # string-replace is now native to playbooks_sections_html() itself, so
    # every page — this one included — already gets it for free.)
    # Nav logo (header only — not the footer's copy, which comes later in the
    # document) stops linking home on this page: swap the <a href="/"> for a
    # plain <span> with the same class, so it keeps its look with no link.
    html = re.sub(
        r'<a class="kz-nav-logo" href="/">(.*?)</a>',
        r'<span class="kz-nav-logo">\1</span>',
        html, count=1, flags=re.S,
    )
    html = html.replace(
        '11M+ points of client service signals',
        '11M+ of client service signals',
        1,
    )
    # Swap in the updated stats band (icons + "avg." labels, white numbers)
    # from the design artifact's Section5-Stats, replacing the homepage's
    # plain bold-yellow-number version for this page only.
    html = re.sub(
        r'<div class="kz-statsband".*?</section>\n</div>',
        lambda _m: _cs_stats_band_html(),
        html,
        count=1,
        flags=re.S,
    )
    # Page-only look: trim the nav down to logo + "Book a demo" (no link list,
    # no mobile toggle, no "Client log in"), and bring back small prev/next
    # arrows on the testimonial carousel, moved up into its top-right corner.
    # Scoped to this page via an inline <style> (loads after site.css, so it
    # wins on tied specificity without needing !important) — the shared
    # homepage/site.css rules are untouched.
    html = html.replace('</head>', dedent('''\
        <style>
          /* Page-wide font swap to Helvetica Neue. The site's type classes
             all read from these custom properties (see tokens.css), so
             redefining them here — rather than overriding font-family on
             every individual selector — retargets every heading, button,
             nav link, card and paragraph on the page in one place.
             Helvetica Neue isn't a Google/web font, so no stylesheet link:
             it renders wherever the visitor's OS ships it (most Apple
             devices; Windows/Linux fall through to Arial). */
          :root {
            --kz-sans: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            --kz-display: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            --kz-mono: 'Helvetica Neue', Helvetica, Arial, sans-serif;
          }
          .kz-nav-links, .kz-nav-toggle { display: none; }
          .kz-nav-cta .kz-btn-ghost { display: none; }
          /* Hero's "Book a demo" pill defaults to align-self: center, which
             centers it under the lede instead of lining up with the
             left-aligned heading/lede above it. margin-top: auto (removed
             below) pins it to the bottom of the hero row, so it drifts down
             when the trial form on the right expands and grows taller —
             a fixed margin keeps it right after the lede instead. */
          .kz-hero-v2-cta { align-self: flex-start; margin-top: 0; }
          /* Small yellow bubble in the hero's decorative cluster → red.
             Its line color was overridden dark (for contrast on yellow);
             put it back to the same white the other bubbles use. */
          .kz-hero-bubble--gold {
            background: #E8432B; box-shadow: 0 14px 24px rgba(232,67,43,.4);
          }
          .kz-hero-bubble--gold span:first-child { background: rgba(255,255,255,.88); }
          .kz-hero-bubble--gold span:last-child { background: rgba(255,255,255,.6); }
          .kz-quotes { position: relative; }
          .kz-quotes .kz-carousel { position: static; }
          .kz-quotes .kz-carousel-arrow {
            display: flex; position: absolute; top: 48px;
            width: 32px; height: 32px; font-size: 15px;
          }
          .kz-quotes .kz-carousel-arrow.is-prev { right: calc(var(--kz-gutter) + 40px); }
          .kz-quotes .kz-carousel-arrow.is-next { right: var(--kz-gutter); }
          @media (max-width: 900px) {
            .kz-quotes .kz-carousel-arrow { display: none; }
          }

          /* ── "Let's talk" closer ─────────────────────────────── */
          .cs-lets-talk { background: var(--kz-sand); }
          .cs-lt-inner {
            max-width: 1280px; margin: 0 auto; padding: 96px var(--kz-gutter);
            text-align: center; display: flex; flex-direction: column; align-items: center; gap: 20px;
          }
          .cs-lt-title { margin: 0; font-size: 44px; line-height: 1.1; font-weight: 700; letter-spacing: -0.02em; }
          .cs-lt-sub { margin: 0; font-size: 22px; font-weight: 700; color: var(--kz-ink); max-width: 46ch; }
          .cs-lt-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; width: 100%; margin-top: 20px; }
          .cs-lt-card {
            min-height: 110px; border-radius: 26px 26px 26px 6px; display: flex;
            align-items: center; justify-content: center; padding: 18px 20px;
            font-size: 15px; font-weight: 600; text-align: center; line-height: 1.4;
            box-shadow: 0 16px 30px rgba(23,21,17,.14);
          }
          .cs-lt-cta { margin-top: 12px; padding: 14px 26px; font-size: 15px; }
          @media (max-width: 760px) { .cs-lt-grid { grid-template-columns: 1fr; } }

          /* ── Modules carousel ────────────────────────────────── */
          .cs-modules { background: var(--kz-yellow); }
          .cs-modules-inner { position: relative; max-width: 1240px; margin: 0 auto; padding: 72px var(--kz-gutter); }
          .cs-modules-head { margin-bottom: 40px; }
          .cs-modules-title { margin: 0; font-size: 36px; line-height: 1.15; font-weight: 700; letter-spacing: -0.02em; max-width: calc(100% - 160px); }
          .cs-modules .kz-carousel { position: static; }
          .cs-modules .kz-carousel-arrow {
            display: flex; position: absolute; top: 46px;
            width: 44px; height: 44px; font-size: 22px; background: #FFFFFF;
          }
          .cs-modules .kz-carousel-arrow.is-prev { right: 60px; }
          .cs-modules .kz-carousel-arrow.is-next { right: 0; }
          .cs-modcard {
            flex: 0 0 320px; scroll-snap-align: start; background: #000000;
            border-radius: 16px; padding: 28px; display: flex; flex-direction: column; gap: 16px;
          }
          .cs-modcard-title { font-size: 18px; font-weight: 700; color: #FFFFFF; }
          .cs-modcard-desc { margin: 0; font-size: 14px; line-height: 1.6; color: rgba(255,255,255,.78); }
          .cs-modules .kz-carousel-dots { margin-top: 32px; }
          @media (max-width: 760px) { .cs-modules-title { max-width: 100%; } }

          /* ── Integrations + FAQ ──────────────────────────────── */
          .cs-integrations { background: var(--kz-paper); }
          .cs-int-inner { max-width: 1280px; margin: 0 auto; padding: 88px var(--kz-gutter) 0; text-align: center; }
          .cs-int-title { margin: 0 0 44px; font-size: 34px; line-height: 1.15; font-weight: 700; letter-spacing: -0.02em; }
          .cs-int-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }
          .cs-int-icon { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 92px; }
          .cs-int-icon-box {
            background: #FFFFFF; border-radius: 16px; width: 76px; height: 76px;
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 8px 18px rgba(23,21,17,.07); transition: transform .2s ease;
          }
          .cs-int-icon:hover .cs-int-icon-box { transform: translateY(-3px); }
          .cs-int-icon-box img { width: 30px; height: 30px; object-fit: contain; }
          .cs-int-icon-label { font-size: 12px; font-weight: 600; text-align: center; }
          .cs-faq-inner { max-width: 1280px; margin: 0 auto; padding: 56px var(--kz-gutter) 110px; }
          .cs-faq-title { margin: 0 0 32px; font-size: 32px; font-weight: 700; letter-spacing: -0.02em; text-align: center; }
          .cs-faq-item { border-bottom: 1px solid var(--kz-line); padding: 22px 4px; }
          .cs-faq-item:last-of-type { border-bottom: none; }
          .cs-faq-summary {
            display: flex; align-items: center; justify-content: space-between; gap: 16px;
            font-size: 16px; font-weight: 700; cursor: pointer; list-style: none;
          }
          .cs-faq-summary::-webkit-details-marker { display: none; }
          .cs-faq-plus { flex: none; transition: transform .25s ease; }
          .cs-faq-item[open] .cs-faq-plus { transform: rotate(45deg); }
          .cs-faq-body { margin: 14px 0 0; font-size: 15px; line-height: 1.6; color: var(--kz-mute); }
        </style>
        </head>'''), 1)
    html = html.replace(
        '<footer class="kz-footer">',
        _cs_lets_talk_html() + '\n' + _cs_modules_html() + '\n' +
        _cs_integrations_faq_html() + '\n    <footer class="kz-footer">',
        1,
    )
    return html


def render_confirmation() -> str:
    """/confirmation/ — where the 14-day trial form (home hero) sends the
    visitor after a successful signup, instead of swapping the card in place.
    Mirrors the homepage hero exactly (trial_hero_copy_html / trial_form_html
    share their markup with render_home), but with the card already showing
    the "you're in" state and no live form to resubmit."""
    body = f'''
    {nav_html(1)}

    <section class="kz-hero kz-hero--trial kz-wash-gold-pale">
      {trial_hero_copy_html(1)}
      <div class="kz-trial">
        {TRIAL_SIGNAL_SVG}
        <div class="kz-trial-done">
          {trial_done_inner_html()}
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Thanks for signing up', 1,
                     "You're in — check your inbox for the next steps on your 14-day trial.",
                     extra_head='<meta name="robots" content="noindex">') + body + page_foot()


def render_product() -> str:
    helpers = [
        dict(k='$', name='ROI Helpers', tag='Grow client ROI',
             blurb=('Agents that read every piece of work, every brief, deck, recap, deliverable, call, across every client, and tell you where the work itself is leaking value. They benchmark across the book, then suggest exactly what would lift output for that one client.'),
             signals=[
                'Acme briefs 28% shorter than top-quartile clients · template suggested',
                'Verkeer creative review skipped 3 weeks running · cadence fix drafted',
                'Northwind targeting brief missing 4 fields your best work always has',
                'Hooli campaign tracking 12% under benchmark · two playbooks pulled from wins',
             ],
             evidence=("Helpers compare each client’s work against the patterns your best work follows, pulled live from your docs, decks, transcripts and outcomes. Continuously learning, so the suggestion for Acme on Friday is sharper than the one on Monday.")),
        dict(k='❤', name='Relationship Helpers', tag='Deepen relationship strength',
             blurb='Agents that map every stakeholder and act on the gaps. They catch silence, dormant champions and thin coverage, and write the warm re-intro before your weekly review.',
             signals=[
                '21 days silent · Mike @ Acme · re-intro draft ready',
                'No senior coverage at Northwind · exec match suggested',
                'New buyer joined at Stark · onboarding note drafted',
                'Tone shift on Sarah @ Hooli · escalation flagged with evidence',
             ],
             evidence='Trained on your conversations: who replies fast, who goes quiet, what tone your champions actually use. The longer you run it, the more the helpers sound like your best AM at their best moment.'),
        dict(k='⚙', name='Growth Helpers', tag='Proactive client growth',
             blurb=("Agents that listen for the moment a client says something they didn’t mean as a buying signal, and turn it into a proactive, client-specific suggestion. Not generic upsell. The next right move for that client, this week."),
             signals=[
                '"Do you do analytics?" · Acme · scoped pitch drafted using 3 lookalike wins',
                "Hooli mentioned a new product line on Tuesday’s call · launch playbook pulled",
                'Verkeer brief widened to include retention work · capacity check + brief drafted',
                'Scale CMO joined Stark · suggest re-pitching the measurement workstream',
             ],
             evidence=("Suggestions are specific to that client’s objectives, history and tone, not a template. Helpers read every conversation across every account, so a cue heard on a Wednesday call shows up as a written-up move on Thursday morning.")),
        dict(k='+', name='Custom Helpers', tag='Build your own',
             blurb='Spin up a helper grounded in your data and your objective: onboarding QA, exec read-outs, pitch prep, capacity planning. Describe the outcome; Kaizan assembles the agent.',
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
         'How the client actually feels about the work: tone, effort, intent, pulled from every email, call and review.', 78, '+3'),
        ('A', 'Account activity',
         'Volume, velocity and seniority of two-way contact. Catches drift before the client feels it.', 64, '+1'),
        ('R', 'Relationship coverage',
         'Who you know, how senior, how warm. Spots thin coverage and dormant champions before the work suffers.', 52, '-9'),
        ('E', 'Engagement growth',
         'Where the scope can deepen: capability gaps, brief widenings, exec asks. Pulled from the language clients actually use.', 71, '+2'),
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
         "Reads every doc, deck and Slack thread for that client, so a draft for Acme actually sounds like Acme, not a template."),
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
        dict(when='Mon · 09:15', who='Slack #acme-team',
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
        ('EXEC MOVE', 'New CMO joined from Stark, Jen Patel',
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
      <div class="kz-product-hero-row">
        <p class="kz-lede" style="font-size:19px;max-width:640px;">
          The AI Assistant captures and unifies every meeting, chat and email.
          The CARE Client Health Model scores every relationship.
          AI Helpers act on every client for you.
          Client360 shares market intel that affects clients.
          Together they form a system of truth and action for your client teams.
        </p>
        <div class="cta">
          <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="/demo/">Book a demo →</a>
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
            The AI Assistant joins every call (Teams, Zoom, Google Meet) and turns it into structured,
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
          Three packs of AI Helpers, plus your own. Every helper is grounded in your company data:
          docs, decks, transcripts, Slack, CRM, email. They keep learning from every new conversation,
          so the output gets more personal to each client&rsquo;s objectives the longer you run them.
        </p>
      </div>
      <div class="kz-helpers-tabs">{helpers_tabs}</div>
      {helpers_panels}
    </section>

    <!-- 03 · CARE MODEL -->
    <section class="kz-section-loose" id="health-model">
      <div class="kz-product-care-row">
        <div>
          <div class="kz-eyebrow">03 · CARE Client Health Model</div>
          <h2 class="kz-h2 kz-h2-lg" style="margin-top:14px;max-width:520px;">
            A self-learning relationship score, grounded in your data.
          </h2>
          <p class="kz-lede" style="font-size:18px;margin-top:22px;max-width:520px;">
            The unifying score across every Helper. It learns from your won pitches, kept clients and
            lost briefs: what predicts a healthy engagement in your company, not the average of someone
            else&rsquo;s. Not a biased RAG status. Re-tuned weekly against your data.
          </p>
          <div style="margin-top:26px;padding:18px 22px;background:var(--kz-paper);border:1px solid var(--kz-line);border-radius:12px;max-width:520px;">
            <div class="kz-eyebrow" style="margin-bottom:10px;">Trained on you</div>
            <p style="font-size:15px;line-height:1.55;color:rgba(10,10,10,.78);">
              The weights that drive CARE for a 200-person agency look nothing like a 20-person consultancy.
              We tune privately, per tenant. Your model never trains a foundation model and never crosses
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
            Client 360 continuously researches every account (funding, hiring, exec moves, competitor noise,
            earnings tone, product launches) and feeds it into the Helpers as live ground truth. So when CARE drops,
            you don&rsquo;t just know <em>that</em> something changed: you know <em>what</em>.
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
        Answers ship with our security review pack. <a href="/demo/" style="color:var(--kz-ink);font-weight:600;">Request the pack →</a>
      </p>
    </section>

    <!-- PRICING anchor (placeholder) -->
    <section class="kz-section-tight" id="pricing">
      <div class="kz-eyebrow">Pricing</div>
      <h2 class="kz-h3" style="margin-top:10px;font-size:24px;max-width:820px;">
        Tiered by seats and integration depth.
      </h2>
      <p class="kz-lede" style="margin-top:14px;max-width:720px;">
        Detailed pricing is shared in the demo. <a href="/demo/" style="color:var(--kz-ink);font-weight:600;">Book a demo →</a>
      </p>
    </section>

    <!-- QUOTE -->
    <section class="kz-section">
      <div class="kz-product-quote-row">
        {portrait(q['name'], q['role'], q['co'], q['tone'], size='xl', depth=1)}
        <div class="quote">
          &ldquo;{E(q['q'])}&rdquo;
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="kz-cta-band kz-cta-band-md">
      <h2 class="head">Put the helpers to work.</h2>
      <div class="actions">
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="/demo/">Book a demo</a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Product', 1,
                     'AI Assistant, AI Helpers, the Client Health Model and Client 360, '
                     'one platform for AI-first client service teams.') + body + page_foot()


def render_persona(slug: str) -> str:
    p = PERSONAS[slug]
    others = [(k, n) for k, n in PERSONA_LIST if k != slug][:3]
    h1_head, h1_hl, h1_tail = p['h1']

    # Hero quote card: optional circular headshot, the pull quote, attribution
    # block, and a "Read more" pill linking to the related customer story.
    photo_file = PEOPLE_PHOTOS.get(p['quote_name'])
    nudge_cls = ' is-nudge' if p.get('quote_nudge') else ''
    if photo_file:
        photo_html = (
            f'<img src="../../assets/img/people/{E(photo_file)}" alt="{E(p["quote_name"])}" '
            f'class="photo" loading="lazy">'
        )
    else:
        initials = ''.join(part[0] for part in p['quote_name'].split()[:2]).upper()
        photo_html = f'<div class="photo is-placeholder">{E(initials)}</div>'

    # Company name in the quote attribution — hyperlinked when quote_co_url is set.
    co_html = E(p['quote_co'])
    if p.get('quote_co_url'):
        co_html = f'<a href="{E(p["quote_co_url"])}">{co_html}</a>'

    # "Watch video" button: rendered only when a matching file exists at
    # assets/video/people/<name-slug>.{mp4,webm}. Opens in the shared lightbox
    # (kz-video-lightbox) wired up in assets/js/site.js.
    name_slug = p['quote_name'].lower().replace(' ', '-')
    video_html = ''
    for ext in ('mp4', 'webm'):
        f = ROOT / 'assets' / 'video' / 'people' / f'{name_slug}.{ext}'
        if f.exists():
            video_src = f'../../assets/video/people/{name_slug}.{ext}'
            video_html = (
                f'<button class="watch-video" type="button" data-video-btn '
                f'data-video-src="{E(video_src)}">'
                f'<span class="play" aria-hidden="true">▶</span> Watch video'
                f'</button>'
            )
            break

    # "Why X love Kaizan" grid - 2 cols when 4 cards, 3 cols when 3 cards.
    love_cols_cls = ' cols-2' if len(p['love']) == 4 else ' cols-3'
    love_html = '\n'.join(
        f'''<div class="kz-love-cell">
          <div class="n">0{i+1}</div>
          <div class="t">{E(t)}</div>
          <div class="d">{E(d)}</div>
        </div>''' for i, (t, d) in enumerate(p['love'])
    )

    # Each product row optionally shows a looping asset from
    # assets/img/personas/<slug>/0N.{mp4,webm,gif,png,jpg}. Prefer video
    # (mp4 > webm) for smaller files; fall back to image; otherwise show
    # the diagonal-stripe placeholder.
    def _product_media(idx: int, name: str) -> str:
        base = ROOT / 'assets' / 'img' / 'personas' / slug
        stem = f'0{idx+1}'
        for ext in ('mp4', 'webm'):
            f = base / f'{stem}.{ext}'
            if f.exists():
                src = f'../../assets/img/personas/{slug}/{stem}.{ext}'
                return (f'<video class="frame-fill is-media" src="{E(src)}" '
                        f'autoplay muted loop playsinline preload="metadata" '
                        f'aria-label="{E(name)} product loop"></video>')
        for ext in ('gif', 'png', 'jpg', 'jpeg', 'webp'):
            f = base / f'{stem}.{ext}'
            if f.exists():
                src = f'../../assets/img/personas/{slug}/{stem}.{ext}'
                return (f'<img class="frame-fill is-media" src="{E(src)}" '
                        f'alt="{E(name)} product loop" loading="lazy">')
        return '<div class="frame-fill">GIF · product loop</div>'

    products_html = '\n'.join(
        f'''<div class="kz-product-row">
          <div class="n">0{i+1}</div>
          <div><div class="t">{E(name)}</div><div class="d">{E(desc)}</div></div>
          <div class="frame">
            {_product_media(i, name)}
          </div>
        </div>''' for i, (name, desc) in enumerate(p['products'])
    )

    faqs_html = '\n'.join(
        f'<div class="kz-objections-row"><div class="q">{E(qq)}</div><div class="a">{E(aa)}</div></div>'
        for qq, aa in p['faqs']
    )

    others_html = '\n'.join(
        f'<a class="kz-persona-pill" href="../{k}/"><span>For {E(n)}</span><span class="arr">→</span></a>'
        for k, n in others
    )

    # H1: optional head, highlighted middle, optional tail.
    h1_parts = []
    if h1_head:
        h1_parts.append(f'{E(h1_head)} ')
    h1_parts.append(f'<span class="kz-mark">{E(h1_hl)}</span>')
    if h1_tail:
        h1_parts.append(E(h1_tail))
    h1_html = ''.join(h1_parts)

    body = f'''
    {nav_html(2)}

    <!-- HERO -->
    <section class="kz-persona-hero">
      <div class="kz-eyebrow">{E(p['eyebrow'])}</div>
      <div class="kz-persona-hero-grid">
        <div>
          <h1 class="kz-h1">{h1_html}</h1>
          <p class="kz-lede" style="margin-top:26px;max-width:560px;">{E(p['sub'])}</p>
          <div class="kz-flex" style="gap:10px;margin-top:28px;">
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="/demo/">Book a demo →</a>
            <a class="kz-btn kz-btn-ghost" style="padding:14px 22px;" href="../../white-paper/">Download CARE white paper</a>
          </div>
        </div>
        <div class="kz-persona-quote{nudge_cls}" style="background:{p['quote_bg']};">
          <div class="photo-wrap">{photo_html}</div>
          <div class="copy">
            <q>{E(p['quote_pull'])}</q>
            <div class="who">
              <div class="name">{E(p['quote_name'])}</div>
              <div class="role">{E(p['quote_role'])}</div>
              <div class="co">{co_html}</div>
            </div>
          </div>
          <div class="actions-stack">
            {video_html}
            <a class="read-more" href="{E(p['quote_cta_href'] if p['quote_cta_href'].startswith(('http://','https://','mailto:')) else '../../' + p['quote_cta_href'])}"{(' target="_blank" rel="noopener"' if p['quote_cta_href'].startswith(('http://','https://')) else '')}>{E(p['quote_cta'])}</a>
          </div>
        </div>
      </div>
    </section>

    <!-- WHY {E(p['role_cap']).upper()} LOVE KAIZAN -->
    <section class="kz-section" style="border-top:1px solid var(--kz-line);">
      <div class="kz-eyebrow">Why {E(p['role'])} love Kaizan</div>
      <h2 class="kz-h2" style="margin:10px 0 28px;max-width:900px;">The things {E(p['role_cap'])} love.</h2>
      <div class="kz-love-grid{love_cols_cls}">{love_html}</div>
    </section>

    <!-- HOW KAIZAN HELPS -->
    <section class="kz-section">
      <div class="kz-eyebrow">How Kaizan helps</div>
      <h2 class="kz-h2" style="margin:12px 0 36px;max-width:900px;">{E(p['product_h2'])}</h2>
      {products_html}
    </section>

    <!-- FAQs -->
    <section class="kz-section">
      <div class="kz-eyebrow">FAQs</div>
      <h2 class="kz-h2" style="margin-top:10px;margin-bottom:32px;">
        The questions {E(p['role'])} ask us.
      </h2>
      <div class="kz-objections">{faqs_html}</div>
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
        <a class="kz-btn kz-btn-yellow" style="padding:14px 24px;font-size:15px;" href="/demo/">Book a demo</a>
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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="/demo/">Book a demo</a>
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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="/demo/">Book a demo</a>
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
    {nav_html(1, active='Resources')}

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
                     'Notes on building client super intelligence: POV, product updates, field notes and benchmarks.') + body + page_foot()


def cover_src(post: dict, depth: int) -> str:
    """Cover image src for a post page at the given depth: the colocated asset if
    present (assets/img/blog/<slug>/...), else a generated gradient fallback."""
    if post.get('cover_asset'):
        return relpath(depth) + 'assets/img/' + post['cover_asset']
    glyph = (post.get('title') or 'KZ').strip()[:2].upper() or 'KZ'
    return cover('#FFB900', '#FFD86B', glyph)


def og_tags(post: dict) -> str:
    """OpenGraph/Twitter/canonical <head> tags for a blog post (depth 2).
    `canonical` frontmatter (set on Medium imports) wins; else self-canonical."""
    url = f"https://kaizan.ai/blog/{post['slug']}/"
    img = f"https://kaizan.ai/assets/img/{post['cover_asset']}" if post.get('cover_asset') else ''
    canon = post.get('canonical') or url
    t = [
        f'<link rel="canonical" href="{E(canon)}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:title" content="{E(post["title"])}">',
        f'<meta property="og:description" content="{E(post.get("excerpt", ""))}">',
        f'<meta property="og:url" content="{E(url)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{E(post["title"])}">',
        f'<meta name="twitter:description" content="{E(post.get("excerpt", ""))}">',
    ]
    if img:
        t.append(f'<meta property="og:image" content="{E(img)}">')
        t.append(f'<meta name="twitter:image" content="{E(img)}">')
    if post.get('iso_date'):
        t.append(f'<meta property="article:published_time" content="{E(post["iso_date"])}">')
    return '\n        '.join(t)


def render_blog_index(posts: list) -> str:
    """The public /blog/ landing — a card grid of all published posts (depth 1)."""
    if posts:
        cards_html = '\n'.join(
            f'''<a class="kz-insights-card" href="{E(p["slug"])}/">
              <div class="cover" style="background-image:url('{cover_src(p, 1)}');"></div>
              <div class="body">
                <h3 class="title">{E(p["title"])}</h3>
                <p class="excerpt">{E(p["excerpt"])}</p>
                <div class="meta">{E(p["date"].upper())}</div>
              </div>
            </a>''' for p in posts
        )
        grid = f'<section class="kz-insights-grid"><div class="kz-insights-cards">{cards_html}</div></section>'
    else:
        grid = '''<section class="kz-blog-empty">
          <div class="head">No posts yet.</div>
          <p>Add a post at <code>content/blog/&lt;slug&gt;/index.md</code> and re-run
          <code>python3 tools/build.py</code>. See <code>content/blog/AUTHORING.md</code>.</p>
        </section>'''

    body = f'''
    {nav_html(1, active='Blog')}
    <section class="kz-insights-hero">
      <div class="kz-eyebrow">Blog · from the Kaizan team</div>
      <h1 class="kz-h1 kz-h1-xl" style="margin:20px 0 0;max-width:1100px;">
        Client Service <span class="kz-mark kz-mark-tight">Super Intelligence</span>
      </h1>
      <p class="kz-lede" style="margin-top:22px;max-width:680px;">
        How the best client teams win, keep and grow the relationships that matter.
      </p>
    </section>
    {grid}
    {footer_html(1)}
    '''
    return page_head('Blog', 1,
                     'Field notes, product updates and research on client relationships from the '
                     'Kaizan team.') + body + page_foot()


def render_blog_post(post: dict) -> str:
    """Render a single blog post page at /blog/<slug>/index.html (depth 2)."""
    hero = (f'<img class="kz-post-hero" src="{cover_src(post, 2)}" '
            f'alt="{E(post["title"])}" decoding="async">') if post.get('cover_asset') else ''
    body = f'''
    {nav_html(2, active='Blog')}
    <article class="kz-essay kz-post" style="padding-top:48px;">
      <div class="kz-essay-body kz-post-body">
        <div class="kz-eyebrow">{E(post.get('date', ''))}</div>
        <h1 class="kz-post-title">{E(post['title'])}</h1>
        {hero}
        {post.get('body', '<p>(empty)</p>')}
        <div class="kz-post-back"><a href="../">← Back to all posts</a></div>
      </div>
    </article>
    {footer_html(2)}
    '''
    return page_head(post['title'], 2, post.get('excerpt', ''),
                     extra_head=og_tags(post)) + body + page_foot()


def render_about() -> str:
    body = f'''
    {nav_html(1, active='About')}

    <!-- HERO -->
    <section class="kz-about-hero">
      <div class="kz-eyebrow">Founder&rsquo;s Letter · Kaizan</div>
      <h1 class="kz-h1" style="margin:22px 0 0;max-width:1200px;">
        A proactive system of <span class="kz-mark">intelligence</span> for client service.
      </h1>
    </section>

    <!-- ESSAY -->
    <article class="kz-essay">
      <aside class="kz-about-byline">
        <img class="photo" src="../assets/img/people/glen-calvert.png" alt="Glen Calvert" loading="lazy">
        <div class="name">Glen Calvert</div>
        <div class="meta">Co-founder &amp; CEO, Kaizan</div>
      </aside>
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

        <div class="kz-essay-sign-off">Glen &amp; Pravin</div>
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
          <a class="btn" href="/demo/">Book time with Glen →</a>
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


# Mailchimp embedded-form endpoints for the July free-coffee campaign.
MC_POST = 'https://kaizan.us6.list-manage.com/subscribe/post?u=b61e5cb1cebf0c30b44ebb455&id=40f0f855d8&f_id=006befe5f0'
MC_JSON = 'https://kaizan.us6.list-manage.com/subscribe/post-json?u=b61e5cb1cebf0c30b44ebb455&id=40f0f855d8&f_id=006befe5f0'
MC_HONEYPOT = 'b_b61e5cb1cebf0c30b44ebb455_40f0f855d8'


JULY_OFFER_STYLE = '''
<style>
  .july-wrap { max-width: 1140px; margin: 0 auto; padding: 0 24px; }
  .july-hero { display: grid; grid-template-columns: 1.05fr 1fr; gap: 60px; align-items: center; padding: 80px 0 64px; }
  .july-hero-head { position: relative; display: inline-block; }
  .july-rays { position: absolute; top: -68px; left: -78px; width: 200px; height: 200px; pointer-events: none; }
  .july-hero h1 { font-size: 72px; line-height: 0.98; letter-spacing: -0.02em; margin: 0; color: var(--kz-ink); }
  .july-hero .july-lede { font-size: 18px; line-height: 1.55; color: var(--kz-ink-soft, #6b6b6b); margin: 22px 0 0; max-width: 440px; }
  .july-imgwrap { border-radius: 22px; overflow: hidden; box-shadow: 0 24px 60px -24px rgba(0,0,0,.30); }
  .july-imgwrap img { display: block; width: 100%; height: auto; }
  .july-form { background: #fff; border: 1px solid rgba(0,0,0,.07); border-radius: 18px; padding: 34px; margin-top: 30px; max-width: 560px;
               box-shadow: 0 2px 0 rgba(0,0,0,.03), 0 22px 54px -22px rgba(0,0,0,.24); }
  .july-form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .july-form label { display: block; font-size: 14px; font-weight: 600; color: var(--kz-ink); margin: 0 0 8px; }
  .july-form input, .july-form select { width: 100%; padding: 15px 16px; font-size: 16px; border: 1px solid rgba(0,0,0,.16); border-radius: 12px;
                                        font-family: inherit; color: var(--kz-ink); background: #fff; }
  .july-form input:focus, .july-form select:focus { outline: none; border-color: var(--kz-yellow); box-shadow: 0 0 0 3px rgba(255,185,0,.25); }
  .july-form .kz-btn { width: 100%; justify-content: center; margin-top: 14px; padding: 15px 22px; font-size: 16px; }
  .july-msg { display: none; margin: 14px 0 0; font-size: 15px; font-weight: 500; }
  .july-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 1140px; margin: 0 auto; padding: 0 24px; }
  .july-step { background: #fff; border: 1px solid rgba(0,0,0,.07); border-radius: 16px; padding: 26px;
               box-shadow: 0 12px 30px -18px rgba(0,0,0,.16); }
  .july-badge { display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 8px;
                background: var(--kz-yellow); color: var(--kz-ink); font-weight: 700; font-size: 15px; }
  .july-steplabel { display: inline-block; margin-left: 10px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--kz-ink-soft, #6b6b6b); vertical-align: middle; }
  .july-step h3 { font-size: 20px; margin: 16px 0 8px; color: var(--kz-ink); }
  .july-step p { margin: 0; color: var(--kz-ink-soft, #6b6b6b); line-height: 1.5; }
  .july-fine { text-align: center; font-size: 16px; color: var(--kz-ink-soft, #6b6b6b); margin: 30px auto 96px; }
  @media (max-width: 900px) {
    .july-hero { grid-template-columns: 1fr; gap: 34px; padding: 52px 0 44px; }
    .july-hero h1 { font-size: 48px; }
    .july-form { max-width: none; }
    .july-steps { grid-template-columns: 1fr; }
  }
  @media (max-width: 460px) { .july-form-row { grid-template-columns: 1fr; } }
</style>
'''

JULY_OFFER_SCRIPT = '''
<script>
// Submit the inline form to Mailchimp via JSONP so the visitor stays on the page
// and we can show an inline confirmation. If JS is unavailable, the form still
// POSTs normally to Mailchimp (progressive enhancement via the form action).
(function () {
  var form = document.getElementById('kz-coffee-form');
  if (!form) return;
  var msg = document.getElementById('kz-coffee-msg');
  var jsonUrl = form.getAttribute('data-mc-json');
  function show(text, ok) {
    if (!msg) return;
    msg.textContent = text;
    msg.style.color = ok ? 'var(--kz-ink)' : '#b00020';
    msg.style.display = 'block';
  }
  form.addEventListener('submit', function (e) {
    if (!jsonUrl) return;                 // no-JS / no endpoint -> normal POST
    e.preventDefault();
    var emailEl = form.querySelector('[name=EMAIL]');
    if (!emailEl || !emailEl.value) { show('Please enter your email.', false); return; }
    var params = new URLSearchParams(new FormData(form)).toString();
    var cb = 'mccb_' + Date.now();
    var s;
    window[cb] = function (data) {
      try {
        if (data && data.result === 'success') {
          form.reset();
          form.style.display = 'none';
          var succ = document.getElementById('kz-success');
          if (succ) succ.style.display = 'block';
        } else {
          var m = (data && data.msg) ? String(data.msg).replace(/^\\d+\\s*-\\s*/, '') : 'Something went wrong \\u2014 please try again.';
          show(m, false);
        }
      } finally {
        delete window[cb];
        if (s && s.parentNode) s.parentNode.removeChild(s);
      }
    };
    s = document.createElement('script');
    s.src = jsonUrl + '&' + params + '&c=' + cb;
    s.onerror = function () { show('Network error \\u2014 please try again.', false); };
    document.body.appendChild(s);
  });
})();
</script>
'''


def render_july_offer() -> str:
    """Campaign landing page: /marketing/july-offer/ — free iced-coffee offer.

    Collects email + role via a Mailchimp pop-up, which then reveals the offer
    code. Submitting the inline form opens the pop-up; the Mailchimp embed script
    goes in MAILCHIMP_POPUP (injected into <head> alongside the page styles)."""
    role_options = '<option value="">Select your role…</option>\n                  ' + '\n                  '.join(
        f'<option>{E(name)}</option>' for _, name in PERSONA_LIST
    ) + '\n                  <option>Other</option>'
    # Sun-ray burst wrapping the top-left corner of the heading (tapered rays,
    # thick at the base, coming to a fine point — drawn as triangles).
    import math
    C, R_IN, R_OUT, W = 60, 22, 56, 0.5  # centre, inner gap, ray length, half base-width
    def ray(d):
        a = math.radians(d)
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx                      # perpendicular
        ix, iy = C + R_IN * dx, C + R_IN * dy  # base centre
        ox, oy = C + R_OUT * dx, C + R_OUT * dy  # tip
        return (f'{ix + W*px:.1f},{iy + W*py:.1f} '
                f'{ox:.1f},{oy:.1f} '
                f'{ix - W*px:.1f},{iy - W*py:.1f}')
    rays = ''.join(f'<polygon points="{ray(d)}"/>' for d in range(150, 331, 30))
    rays_svg = (
        '<svg class="july-rays" viewBox="0 0 120 120" aria-hidden="true">'
        f'<g fill="var(--kz-yellow)" stroke="var(--kz-yellow)" stroke-width="1.6" '
        f'opacity="0.55" stroke-linejoin="round" stroke-linecap="round">{rays}</g>'
        '</svg>'
    )
    body = f'''
    {nav_html(2)}

    <section class="july-wrap">
      <div class="july-hero">
        <div>
          <div class="july-hero-head">{rays_svg}<h1>Iced coffees on us!</h1></div>
          <p class="july-lede">
            Pop in your email and role and we&rsquo;ll hand you a code for a free iced
            coffee on <strong>Thursday 30 July</strong>. Our way of beating the heat, and saying hello.
          </p>

          <form id="kz-coffee-form" class="july-form" action="{MC_POST}" method="post" target="_blank"
                data-mc-json="{MC_JSON}" novalidate>
            <div class="july-form-row">
              <div>
                <label for="mce-EMAIL">Work email</label>
                <input id="mce-EMAIL" name="EMAIL" type="email" placeholder="you@company.com" autocomplete="email" required>
              </div>
              <div>
                <label for="mce-ROLE">Your role</label>
                <select id="mce-ROLE" name="ROLE">
                  {role_options}
                </select>
              </div>
            </div>
            <!-- Tag every landing-page signup so the voucher automation fires; do not remove -->
            <input type="hidden" name="tags" value="july-coffee">
            <!-- Mailchimp bot-prevention field, keep, do not remove -->
            <div style="position:absolute;left:-5000px;" aria-hidden="true">
              <input type="text" name="{MC_HONEYPOT}" tabindex="-1" value="">
            </div>
            <button type="submit" name="subscribe" class="kz-btn kz-btn-yellow">Claim your free iced coffee →</button>
            <p id="kz-coffee-msg" class="july-msg" role="status" aria-live="polite"></p>
          </form>

          <div id="kz-success" style="display:none; text-align:center; padding:32px; background:#FFB900; border-radius:16px; font-family:Arial, sans-serif;">
            <h2 style="margin:0 0 8px; color:#000; font-size:28px; font-weight:bold;">You're in! ☕</h2>
            <p style="margin:0 0 16px; color:#000; font-size:16px;">Show this at the counter at Kaffeine to claim your free iced coffee:</p>
            <div style="display:inline-block; background:#000; color:#FFB900; font-size:30px; font-weight:bold; letter-spacing:0.15em; padding:16px 28px; border-radius:12px;">KAIZAN</div>
            <p style="margin:16px 0 0; color:#000; font-size:13px;">We've also emailed this to you, check your inbox in a few minutes.</p>
          </div>
        </div>

        <div class="july-imgwrap">
          <img src="{relpath(2)}assets/img/marketing/july-offer-coffee.png"
               alt="Four hands holding iced coffees with sleeves reading: Survived another client call? Have a coffee on us. Kaffeine x Kaizan."
               decoding="async">
        </div>
      </div>
    </section>

    <section class="july-steps">
      <div class="july-step">
        <div><span class="july-badge">1</span><span class="july-steplabel">Step 01</span></div>
        <h3>Tell us who you are</h3>
        <p>Enter your email and role in the quick pop-up.</p>
      </div>
      <div class="july-step">
        <div><span class="july-badge">2</span><span class="july-steplabel">Step 02</span></div>
        <h3>Get your code</h3>
        <p>We&rsquo;ll email you your code &mdash; show the email to the baristas at Kaffeine.</p>
      </div>
      <div class="july-step">
        <div><span class="july-badge">3</span><span class="july-steplabel">Step 03</span></div>
        <h3>Enjoy the coffee</h3>
        <p>Show your code at Kaffeine and enjoy an iced coffee on Kaizan.</p>
      </div>
    </section>

    <p class="july-fine">Valid <strong>Thursday 30 July</strong> only at <strong>Kaffeine</strong>, <strong>15 Eastcastle Street, London W1W 8DY</strong>. One coffee per person, while stocks last.</p>

    {JULY_OFFER_SCRIPT}
    {footer_html(2)}
    '''
    return page_head('Free iced coffee this July', 2,
                     "Iced coffee's on us this July: enter your email and role to get your free coffee code.",
                     extra_head=JULY_OFFER_STYLE) + body + page_foot()



def render_404() -> str:
    body = f'''
    {nav_html(0)}
    <section class="kz-404">
      <div class="num">404</div>
      <div class="head">That page got distracted by a client.</div>
      <div class="sub">The link you followed isn&rsquo;t here. Try the homepage, or one of the main sections below.</div>
      <div class="kz-flex" style="gap:12px;margin-top:14px;">
        <a class="kz-btn kz-btn-yellow" href="/">Back to home</a>
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

# Connector brand marks. Real SVG files live in assets/img/integrations/.
# `kzapi` is the only inline mark (the featured Kaizan API tile — no real brand,
# we draw it ourselves in brand black + yellow).
def _int_img(filename: str, alt: str) -> str:
    return f'<img src="../assets/img/integrations/{filename}" alt="{E(alt)}" loading="lazy">'

INT_LOGOS = {
    'teams':      _int_img('teams.svg',      'Microsoft Teams'),
    'claude':     _int_img('claude.svg',     'Claude'),
    'slack':      _int_img('slack.svg',      'Slack'),
    'hubspot':    _int_img('hubspot.svg',    'HubSpot'),
    'salesforce': _int_img('salesforce.svg', 'Salesforce'),
    'gmeet':      _int_img('gmeet.svg',      'Google Meet'),
    'gdrive':     _int_img('gdrive.svg',     'Google Drive'),
    'monday':     _int_img('monday.svg',     'Monday'),
    'sharepoint': _int_img('sharepoint.svg', 'SharePoint'),
    'zoom':       _int_img('zoom.svg',       'Zoom'),
    'wrike':      _int_img('wrike.svg',      'Wrike'),
    'kzapi': '''<svg viewBox="0 0 48 48" width="44" height="44"><rect x="4" y="4" width="40" height="40" rx="10" fill="#0A0A0A"/><path d="M14 18 l-5 6 l5 6 M34 18 l5 6 l-5 6 M22 32 l4 -16" stroke="#FFB900" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
    'gmail':      _int_img('gmail.svg',      'Gmail'),
    'outlook':    _int_img('outlook.svg',    'Outlook'),
    'jira':       _int_img('jira.svg',       'Jira'),
    'asana':      _int_img('asana.svg',      'Asana'),
    'clickup':    _int_img('clickup.svg',    'ClickUp'),
    'notion':     _int_img('notion.svg',     'Notion'),
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
        Kaizan builds a continuous memory on every client by automatically capturing every meeting,
        message, doc and report. <strong style="color:var(--kz-ink);font-weight:600;">All standard
        integrations are free.</strong> All client and communication data assigned to the right
        client, the right stakeholders, with the right access rights. Unify your most precious
        asset for your team and their AI Helpers.
      </p>
      <div class="kz-int-meta">
        <span><span class="kz-dot"></span> <strong>2-way sync</strong></span>
        <span><span class="kz-dot"></span> <strong>Read &amp; Write</strong></span>
        <span><span class="kz-dot"></span> <strong>OAuth Access</strong></span>
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
          <p class="lede">Leverage all your unified client intelligence (every meeting, every signal,
            every score) in your own systems and agents. SOC 2 logged, two-way sync, scoped per tenant.</p>
        </div>
        <div class="actions">
          <a class="kz-btn kz-btn-yellow" style="padding:12px 20px;font-size:14px;white-space:nowrap;" href="/demo/">Talk to us</a>
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
            with your internal systems, for more client intelligence, workflow automation and autonomous
            client growth.
          </p>
          <div class="kz-flex" style="margin-top:26px;">
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;font-size:14px;" href="/demo/">Book demo →</a>
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
          <p>If you&rsquo;re an enterprise and your stack includes a tool we don&rsquo;t support yet, tell us.
            We&rsquo;ve shipped two new connectors per quarter for the last year.</p>
        </div>
        <a class="kz-btn kz-btn-black" style="padding:16px 26px;font-size:15px;white-space:nowrap;" href="/demo/">
          Request an integration →
        </a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Integrations', 1,
                     'Native connectors for Microsoft Teams, Slack, HubSpot, Salesforce, Google Meet '
                     'and more, plus the Kaizan API.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# PRICING
# ─────────────────────────────────────────────────────────────────────

PRICING_TIERS = [
    dict(name='Pilot', clients_pre='Full access for ', clients_bold='14 days',
         price='Free', per='No card, no commitment',
         plan='Speak to a Kaizan Account Executive to get set up',
         cta='Book a kickoff call', cta_note='Live the same day, connect by OAuth',
         cta_style='primary', ribbon='Start here', card='hero',
         features=['Full platform for 14 days',
                   'Connect your own client data',
                   'Guided setup and kick off',
                   '2 to 3 outcomes agreed up front',
                   'CARE']),   # 'CARE' renders the linked CARE bullet
    dict(name='Starter', clients_pre='Minimum ', clients_bold='10 clients',
         price='£99', per='per client / month, billed as one flat monthly plan',
         plan='Minimum 10 clients on contract',
         cta='Book a demo', cta_note='Upgrade any time as your book grows', cta_style='outline',
         features=['Unlimited users, no extra cost',
                   'Meeting assistant',
                   'Standard chat and CRM integrations',
                   'Client intelligence platform',
                   'MCP access',
                   'Desktop SDK',
                   'Dedicated account manager']),
    dict(name='Growth', clients_pre='Minimum ', clients_bold='25 clients',
         price='£119', per='per client / month, billed as one flat monthly plan',
         plan='Minimum 25 clients on contract',
         cta='Book a demo', cta_note='Upgrade any time as your book grows', cta_style='outline',
         ribbon='Most popular', ribbon_quiet=True, card='changed',
         features=['Everything in Starter',
                   'Guided onboarding and AI maturity framework assessment',
                   'API access',
                   'Priority support']),
    dict(name='Enterprise', clients_pre='Large portfolios ', clients_bold='and custom work',
         price='Custom', per='Per client rate negotiated to your portfolio',
         plan='Scoped with you, billed as one flat monthly plan',
         cta='Talk to us', cta_note='', cta_style='dark',
         features=['Unlimited users, no per seat fees',
                   'Unlimited portfolio, multi office and region',
                   'Multi team segmentation across practices',
                   'CARE calibration per practice',
                   'Custom AI helpers, quoted to your requirements',
                   'API and MCP, extended access and rate limits',
                   'Custom integrations and bespoke builds']),
]


def tier_card(t: dict, p: str = '', demo_href: str = '/demo/') -> str:
    care_href = f'{p}product/#health-model'
    feats = []
    for f in t['features']:
        if f == 'CARE':
            feats.append(f'<li><span><a href="{care_href}">CARE</a> scores and findings at day 14</span></li>')
        else:
            feats.append(f'<li>{E(f)}</li>')
    features = '\n        '.join(feats)
    ribbon = ''
    if t.get('ribbon'):
        rc = ' quiet' if t.get('ribbon_quiet') else ''
        ribbon = f'<div class="kzp-ribbon{rc}">{E(t["ribbon"])}</div>'
    card_cls = f' {t["card"]}' if t.get('card') else ''
    note = E(t['cta_note']) if t.get('cta_note') else '&nbsp;'
    style = t.get('cta_style', 'outline')
    return f'''<div class="kzp-tier{card_cls}">
        {ribbon}
        <div class="kzp-name">{E(t["name"])}</div>
        <div class="kzp-clients">{E(t["clients_pre"])}<strong>{E(t["clients_bold"])}</strong></div>
        <div class="kzp-price{' sm' if t.get('price_small') else ''}">{E(t["price"])}</div>
        <p class="kzp-per">{E(t["per"])}</p>
        <p class="kzp-plan">{E(t["plan"])}</p>
        <ul class="kzp-features">
        {features}
        </ul>
        <a class="kzp-btn kzp-btn-{style}" href="{demo_href}" target="_blank" rel="noopener">{E(t["cta"])}</a>
        <p class="kzp-btn-note">{note}</p>
      </div>'''


# US (USD) pricing tiers. Same card shape as PRICING_TIERS, but band-based
# ("up to N" / "N to M") rather than minimum-based, per the approved US artefact.
# Rendered US-only into /us/pricing/ by build_us_locale() (see us_pricing_section).
PRICING_TIERS_US = [
    dict(name='Pilot', clients_pre='14 days of ', clients_bold='full access',
         price='Free', per='No card, no commitment',
         plan='Speak to a Kaizan Account Executive to get set up',
         cta='Book a kickoff call', cta_note='Live the same day, connect by OAuth',
         cta_style='primary', ribbon='Start here', card='hero',
         features=['Full platform for 14 days',
                   'Connect your own client data',
                   'Guided setup and kick off',
                   '2 to 3 outcomes agreed up front',
                   'CARE']),
    dict(name='Starter', clients_pre='Up to ', clients_bold='20 clients',
         price='$129', per='per client / month, billed as one flat monthly plan',
         plan='$2,580 a month at 20 clients',
         cta='Book a demo', cta_note='Upgrade any time as your book grows', cta_style='outline',
         features=['Unlimited users, no extra cost',
                   'Meeting assistant',
                   'Full integrations suite',
                   'Client intelligence platform',
                   'API and MCP access',
                   'Dedicated account manager']),
    dict(name='Growth', clients_pre='21 to ', clients_bold='49 clients',
         price='$159', per='per client / month, billed as one flat monthly plan',
         plan='$7,791 a month at 49 clients',
         cta='Book a demo', cta_note='Upgrade any time as your book grows', cta_style='outline',
         ribbon='Most popular', ribbon_quiet=True, card='changed',
         features=['Everything in Starter',
                   'Bigger portfolio, up to 49 accounts',
                   'Guided onboarding with CARE calibration']),
    dict(name='Enterprise', clients_pre='Large portfolios ', clients_bold='and custom work',
         price='Custom', per='Per client rate negotiated to your portfolio',
         plan='Scoped with you, billed as one flat monthly plan',
         cta='Talk to us', cta_note='', cta_style='dark', price_small=True,
         features=['Unlimited portfolio, multi office and region',
                   'Unlimited users, no per-seat fees',
                   'Multi team segmentation across practices',
                   'Custom AI helpers, quoted to your requirements',
                   'API and MCP, extended access and rate limits',
                   'Custom integrations and bespoke builds',
                   'SSO and SAML, custom retention and data residency']),
]


def us_pricing_section() -> str:
    """The USD <section class="kzp"> for /us/pricing/. Injected by build_us_locale
    in place of the mirrored GBP section. CTAs point at the US booking; the CARE
    link and 'View UK pricing' link resolve correctly from /us/pricing/."""
    tiers_html = '\n'.join(tier_card(t, '../', '/us/demo/') for t in PRICING_TIERS_US)
    return f'''<section class="kzp">
      <div class="kzp-wrap">
        <h1 class="kzp-h1">Priced by the size of the portfolio we help you grow.</h1>
        <p class="kzp-sub">Every engagement starts with a free 14-day pilot on your own data. After that, the rate is set by how many clients you cover. Unlimited users on every tier.</p>
        <div class="kzp-badges">
          <span class="kzp-tag">✓ New: 14-day pilot, free of charge</span>
          <span class="kzp-tag">✓ Unlimited users on every plan</span>
        </div>
        <div class="kzp-grid">{tiers_html}</div>
        <p class="kzp-foot">All prices in USD, exclusive of applicable sales tax, calculated at checkout by billing state. Annual contract, unlimited users on every tier. Billed in USD through Kaizan&rsquo;s New York entity. Fair use limits apply on storage, API calls and integration volumes. Custom AI helpers, integrations and bespoke engineering quoted separately. <a href="/pricing/">View GBP / UK pricing &rarr;</a></p>
      </div>
    </section>'''


PRICING_HELPERS = [
    dict(tag='AI ASSISTANT', name='For the Team',
         sub='Joins every meeting, knows every client conversation, drafts what you need and updates your tools, accessed through your LLM of choice.',
         features=['LLM of choice', 'Auto-updates CRM & PM', 'Search all unified data']),
    dict(tag='AI HELPER', name='Client ROI',
         sub='Proactively increase the ROI on every client by turning conversations, emails and project activity into demonstrable value.',
         features=['Auto-built QBR decks', 'Value-gap alerts', 'Renewal risk scoring']),
    dict(tag='AI HELPER', name='Relationships',
         sub='Grow CSAT with proactive recommendations: Kaizan flags weakening relationships before they cost you a renewal.',
         features=['Disengagement flags', 'Stakeholder coverage maps', 'Drafted re-engagement']),
    dict(tag='AI HELPER', name='Expansion',
         sub='Maximise client revenue with continuous market research, drafted outbound, and solutions matched to each client’s stated objectives.',
         features=['Continuous market research', 'Drafted outbound', 'Solutions matched to objectives']),
]


# The ROI calculator is a self-contained widget (scoped #kaizan-roi markup +
# assets/css/roi-calculator.css + assets/js/roi-calculator.js). It replaces the
# old tier-cards pricing page — the tiers/cost are shown inside the calculator.
# PRICING_TIERS / PRICING_HELPERS above are now unused but kept for reference.
#
# Lead capture is a HubSpot form (EU portal 144688314) rendered into
# #kzroi-hubspot-form by roi-calculator.js. On successful submit, the JS unlocks
# the "Download your breakdown (PDF)" button, which prints a report of the user's
# own numbers (print-to-PDF, no dependency).
ROI_CALCULATOR_SECTION = '''
<section id="kaizan-roi">
  <div class="kzroi-inner">

    <!-- section header -->
    <div class="kzroi-eyebrow">ROI calculator</div>
    <h2 class="kzroi-h2">What Kaizan <span class="hl">returns</span> on the portfolio you run today.</h2>

    <!-- full-width headline result bar -->
    <div class="kzroi-bar">
      <div class="kzroi-bar-top">
        <div>
          <div class="kzroi-bar-label" data-roi="headline-label">Net annual gain with Kaizan</div>
          <div class="kzroi-net-row">
            <span class="kzroi-net" data-roi="net">£0</span>
            <span class="kzroi-net-unit">/ yr</span>
          </div>
          <div class="kzroi-custom-note kzroi-hidden" data-roi="custom-note">before platform cost: Enterprise pricing is bespoke</div>
        </div>
        <div class="kzroi-metrics" data-roi="metrics"><!-- metrics injected by JS --></div>
      </div>
      <div class="kzroi-bar-bottom" data-roi="cost-row"><!-- cost row injected by JS --></div>
    </div>

    <!-- proof point -->
    <div class="kzroi-proof">
      <span class="star" aria-hidden="true">★</span>
      <span>Modelled on Kaizan clients seeing <strong>21%+ average revenue growth per client</strong>.</span>
    </div>

    <!-- model toggle (left) + CTAs (right) -->
    <div class="kzroi-controls">
      <div class="kzroi-toggle-wrap">
        <span class="kzroi-toggle-q">How hard should we model it?</span>
        <div class="kzroi-toggle" data-roi="mode-toggle">
          <button type="button" class="kzroi-toggle-btn" data-mode="Conservative">Conservative</button>
          <button type="button" class="kzroi-toggle-btn is-active" data-mode="Expected">Expected</button>
        </div>
      </div>
      <div class="kzroi-actions">
        <button type="button" class="kzroi-leadbtn" data-roi="lead-toggle">Email me the breakdown</button>
        <a href="/demo/" target="_blank" rel="noopener" class="kzroi-pill kzroi-pill-gold in-controls">Book a demo →</a>
      </div>
    </div>

    <!-- lead-capture lives in a modal (see end of section), opened by the
         "Email me the breakdown" buttons. -->

    <!-- two columns: inputs (left) · results (right) -->
    <div class="kzroi-cols">

      <!-- LEFT: portfolio inputs -->
      <div class="kzroi-panel">
        <div class="kzroi-panel-title">Your client portfolio today</div>
        <div class="kzroi-panel-sub">Four things you'll know off the top of your head. We handle the rest.</div>

        <div class="kzroi-num" data-key="totalHeadcount" data-min="1" data-max="5000" data-step="1">
          <label class="kzroi-num-label">Total company headcount</label>
          <div class="kzroi-num-row">
            <button type="button" class="kzroi-step" data-act="dec" aria-label="Decrease Total company headcount">−</button>
            <div class="kzroi-field"><input type="text" inputmode="numeric"></div>
            <button type="button" class="kzroi-step" data-act="inc" aria-label="Increase Total company headcount">+</button>
          </div>
          <div class="kzroi-num-help">Everyone at your company. Kaizan is unlimited users: finance, ops and leadership can all use it at no extra cost.</div>
        </div>

        <div class="kzroi-num" data-key="team" data-min="1" data-max="500" data-step="1">
          <label class="kzroi-num-label">Client delivery team size</label>
          <div class="kzroi-num-row">
            <button type="button" class="kzroi-step" data-act="dec" aria-label="Decrease Client delivery team size">−</button>
            <div class="kzroi-field"><input type="text" inputmode="numeric"></div>
            <button type="button" class="kzroi-step" data-act="inc" aria-label="Increase Client delivery team size">+</button>
          </div>
          <div class="kzroi-num-help">Of your headcount, those who touch client work: account managers, client success, delivery. This is what drives the capacity figure.</div>
        </div>

        <div class="kzroi-num" data-key="clients" data-min="1" data-max="2000" data-step="1">
          <label class="kzroi-num-label">Number of clients</label>
          <div class="kzroi-num-row">
            <button type="button" class="kzroi-step" data-act="dec" aria-label="Decrease Number of clients">−</button>
            <div class="kzroi-field"><input type="text" inputmode="numeric"></div>
            <button type="button" class="kzroi-step" data-act="inc" aria-label="Increase Number of clients">+</button>
          </div>
        </div>

        <div class="kzroi-num" data-key="revPer" data-min="1000" data-max="5000000" data-step="5000">
          <label class="kzroi-num-label">Average annual revenue per client</label>
          <div class="kzroi-num-row">
            <button type="button" class="kzroi-step" data-act="dec" aria-label="Decrease Average annual revenue per client">−</button>
            <div class="kzroi-field"><span class="kzroi-prefix">£</span><input type="text" inputmode="numeric"></div>
            <button type="button" class="kzroi-step" data-act="inc" aria-label="Increase Average annual revenue per client">+</button>
          </div>
          <div class="kzroi-num-help">Your average annual client value across the portfolio.</div>
        </div>

        <div class="kzroi-num" data-key="churn" data-min="1" data-max="60" data-step="1">
          <label class="kzroi-num-label">Typical annual client attrition rate</label>
          <div class="kzroi-num-row">
            <button type="button" class="kzroi-step" data-act="dec" aria-label="Decrease Typical annual client attrition rate">−</button>
            <div class="kzroi-field"><input type="text" inputmode="numeric"><span class="kzroi-suffix">%</span></div>
            <button type="button" class="kzroi-step" data-act="inc" aria-label="Increase Typical annual client attrition rate">+</button>
          </div>
          <div class="kzroi-num-help">The share of client accounts you lose in a typical year.</div>
        </div>

        <div class="kzroi-portfolio-row">
          <span class="kzroi-portfolio-label">Client portfolio value</span>
          <span class="kzroi-portfolio-val"><span data-roi="portfolio">£0</span> <span class="unit">/ yr</span></span>
        </div>

        <details class="kzroi-method">
          <summary>How we calculate this</summary>
          <div class="mbody">
            <p><strong>Retention.</strong> Your attrition × portfolio value is the revenue at risk each year. We credit Kaizan with the share it protects via early CARE signals: <span data-roi="m-churn">45</span>% in <span data-roi="m-mode">Expected</span> mode (saves, scope recovered, cycles extended). We never count more than your actual attrition.</p>
            <p><strong>White space.</strong> Upsell is modelled on an 8% addressable pool of your portfolio, of which we count <span data-roi="m-upsell">60</span>%: opportunities surfaced from clients you already have.</p>
            <p><strong>Capacity.</strong> 9 admin hrs/week per client-facing person (UK companies report ~13 non-billable hrs), of which <span data-roi="m-capacity">60</span>% is handed back, across 46 working weeks. Valued at £30/hr loaded cost: UK client-service salary ~£40k × ~1.3 overhead ÷ 1,725 FTE hrs.</p>
            <p><strong>Satisfaction</strong> is shown directionally and never monetised. <strong>Pricing</strong> is set automatically from your client count; users are unlimited.</p>
          </div>
        </details>
      </div>

      <!-- RIGHT: results detail -->
      <div class="kzroi-right">

        <!-- composition card -->
        <div class="kzroi-comp">
          <div class="kzroi-comp-title">Where the <span class="mono" data-roi="gross">£0</span> of annual benefit comes from</div>
          <div class="kzroi-bar-track" data-roi="seg-track"><!-- segments injected by JS --></div>
          <div class="kzroi-legend" data-roi="legend"><!-- legend injected by JS --></div>
        </div>

        <!-- area cards -->
        <div class="kzroi-areas">
          <div class="kzroi-card">
            <div class="kzroi-card-kicker">Retention <span class="agent">· AI Agents</span></div>
            <div class="kzroi-card-fig-wrap"><div class="kzroi-card-fig" data-roi="fig-retained">£0</div></div>
            <div class="kzroi-card-title">Revenue protected from churn</div>
            <div class="kzroi-card-bullets">
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span><span data-roi="at-risk">£0</span> of your portfolio is at risk each year</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Every conversation scored against CARE: risks flagged before clients go quiet</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Drafted re-engagement, ready to send</span></div>
            </div>
          </div>

          <div class="kzroi-card">
            <div class="kzroi-card-kicker">White space <span class="agent">· AI Agents</span></div>
            <div class="kzroi-card-fig-wrap"><div class="kzroi-card-fig" data-roi="fig-upsold">£0</div></div>
            <div class="kzroi-card-title">Revenue expanded through upsell</div>
            <div class="kzroi-card-bullets">
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Buying signals spotted in every client conversation</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Continuous research matched to each client's stated objectives</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>The most growth you'll get is from clients you already have</span></div>
            </div>
          </div>

          <div class="kzroi-card">
            <div class="kzroi-card-kicker">Efficiency <span class="agent">· AI Agents</span></div>
            <div class="kzroi-card-fig-wrap"><div class="kzroi-card-fig" data-roi="fig-capacity">£0</div><div class="kzroi-card-sub" data-roi="fig-fte">+0.0 FTE</div></div>
            <div class="kzroi-card-title">Capacity recovered from admin</div>
            <div class="kzroi-card-bullets">
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span><span data-roi="admin-hours">0</span> admin hours sit across your team each year</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Notes, follow-ups and CRM updates handled automatically</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Time goes straight back into client-facing work</span></div>
            </div>
          </div>

          <div class="kzroi-card">
            <div class="kzroi-card-kicker">Satisfaction <span class="agent">· AI Agents</span></div>
            <div class="kzroi-card-fig-wrap">
              <div class="kzroi-card-fig">
                <svg width="68" height="26" viewBox="0 0 68 26" fill="none" aria-label="trending up" style="display:block">
                  <polyline points="2,22 17,15 30,18 46,9 66,3" stroke="#2E6F4E" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"></polyline>
                </svg>
              </div>
              <div class="kzroi-card-sub">NPS tends to climb</div>
            </div>
            <div class="kzroi-card-title">Client satisfaction</div>
            <div class="kzroi-card-bullets">
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Every client conversation scored against the CARE framework</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Risks addressed early, actions never dropped</span></div>
              <div class="kzroi-bullet"><span class="arrow" aria-hidden="true">→</span><span>Directional only: NPS typically rises over the first 1–2 quarters, never counted in the figures above</span></div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- full-width centred footnote -->
    <div class="kzroi-footnote">
      <span data-roi="footnote"><!-- injected by JS --></span>
    </div>

    <!-- closing CTA band -->
    <div class="kzroi-cta-band">
      <h3>See your clients, clearly.</h3>
      <p>Take the full breakdown with you (your numbers, the workings, and what comparable Kaizan clients see) or jump straight to a demo.</p>
      <div class="kzroi-cta-actions">
        <a href="/demo/" target="_blank" rel="noopener" class="kzroi-pill kzroi-pill-gold">Book a demo →</a>
        <button type="button" class="kzroi-pill kzroi-pill-ghost" data-roi="lead-toggle-cta">Email me the breakdown</button>
      </div>
    </div>

    <!-- lead-capture modal (opened by the "Email me the breakdown" buttons).
         HubSpot form (EU portal 144688314); on submit the JS swaps to the
         download view. Close via the ×, the backdrop, or Esc. -->
    <div class="kzroi-modal kzroi-hidden" data-roi="modal" role="dialog" aria-modal="true" aria-label="Get your ROI breakdown">
      <div class="kzroi-modal-backdrop" data-roi="modal-close"></div>
      <div class="kzroi-modal-card" role="document">
        <button type="button" class="kzroi-modal-x" data-roi="modal-close" aria-label="Close">×</button>
        <div data-roi="lead-form">
          <div class="kzroi-modal-title">Get your ROI breakdown</div>
          <div class="lf-intro">Your results are yours either way. For the full PDF breakdown (your numbers and the workings) tell us where to send it, then download it here.</div>
          <div id="kzroi-hubspot-form" class="kzroi-hsform"></div>
        </div>
        <div class="kzroi-leadsent kzroi-hidden" data-roi="lead-sent">
          <div class="ls-msg">Thanks, your breakdown is ready.</div>
          <button type="button" class="kzroi-leadform-submit" data-roi="download">Download your breakdown (PDF) →</button>
        </div>
      </div>
    </div>

  </div>
</section>
'''


def render_pricing() -> str:
    p = relpath(1)
    extra_head = (
        f'<link rel="stylesheet" href="{p}assets/css/pricing.css{asset_v("assets/css/pricing.css")}">\n'
        f'        <link rel="stylesheet" href="{p}assets/css/roi-calculator.css{asset_v("assets/css/roi-calculator.css")}">\n'
        f'        <link rel="stylesheet" href="{p}assets/css/roi-accordion.css{asset_v("assets/css/roi-accordion.css")}">\n'
        f'        <script charset="utf-8" defer src="//js-eu1.hsforms.net/forms/embed/v2.js"></script>\n'
        f'        <script defer src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>\n'
        f'        <script defer src="{p}assets/js/roi-calculator.js{asset_v("assets/js/roi-calculator.js")}"></script>'
    )
    tiers_html = '\n'.join(tier_card(t, p) for t in PRICING_TIERS)
    pricing_section = f'''
    <section class="kzp">
      <div class="kzp-wrap">
        <h1 class="kzp-h1">Priced by the size of the portfolio we help you grow.</h1>
        <p class="kzp-sub">Every engagement starts with a free 14 day pilot on your own data. After that, the rate is set by how many clients you cover. Unlimited users on every tier.</p>
        <div class="kzp-badges">
          <span class="kzp-tag">✓ New: 14 day pilot, free of charge</span>
          <span class="kzp-tag">✓ Unlimited users on every plan</span>
        </div>
        <div class="kzp-grid">{tiers_html}</div>
        <p class="kzp-foot">All prices GBP, annual contract. Unlimited users on every tier. Fair use limits apply on storage, API calls and integration volumes. Custom AI helpers, integrations and bespoke engineering quoted separately.</p>
      </div>
    </section>'''
    chevron = ('<svg class="kzacc-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
               'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
               '<polyline points="6 9 12 15 18 9"></polyline></svg>')
    accordion = f'''
    <section class="kzp-calc">
      <details class="kzacc">
        <summary class="kzacc-summary">
          <div>
            <p class="kzacc-title">Worried this costs more than it saves? See the maths.</p>
            <p class="kzacc-sub">Takes 30 seconds. No email required.</p>
          </div>
          {chevron}
        </summary>
        <div class="kzacc-body">
          {ROI_CALCULATOR_SECTION}
        </div>
      </details>
    </section>'''
    body = nav_html(1, active='Pricing') + pricing_section + accordion + footer_html(1)
    return page_head('Pricing', 1,
                     'Kaizan pricing: priced by the size of the client portfolio we help you grow. '
                     'Free 14 day pilot, then per client per month. Unlimited users on every tier.',
                     extra_head=extra_head) + body + page_foot()



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
             desc='Kaizan complies with leading industry standards and regulations, including SOC 2 and UK & EU GDPR. Transfers of personal data to US-based subprocessors are safeguarded under the UK International Data Transfer Agreement and, where the subprocessor is certified, the EU-U.S. Data Privacy Framework. Regular audits and third-party assessments help us maintain and improve our security posture.',
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
        return ('<div class="kz-secvis kz-secvis-badges">'
                '<img src="../assets/img/security/Security.png" '
                'alt="SOC 2, ISO 27001, GDPR, CASA Verified, CCPA: security and compliance certifications" '
                'loading="lazy">'
                '</div>')
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
        rows = [('12:04:18','admin@northwind.com','role.update','kz-care-001 → manager'),
                ('12:04:09','jdoe@hooli.io','session.start','sso · okta'),
                ('12:03:55','sec-bot','access.review','weekly · ok'),
                ('12:03:41','priya@pied-piper.com','export.audit','180 events · csv'),
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
    {nav_html(1, active='Resources')}

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
      <a class="kz-btn kz-btn-black" style="padding:18px 28px;font-size:16px;" href="https://security.kaizan.ai/">Visit our Trust Centre →</a>
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
        <div class="signoff">Glen &amp; the team</div>
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
        Don&rsquo;t see the right role? <a href="mailto:hi@kaizan.ai">hi@kaizan.ai</a>, we always read
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
         'Kaizan is an AI platform built for Client Service teams and their AI Agents. It unifies all client data, captures every client meeting, email and message, scores the health of each relationship, surfaces risks before they become issues, and drafts the follow-ups, updates market intelligence and expansion plays that account managers spend most of their time doing. Kaizan is used by client-services teams globally obsessed with delivering elite client service.'),
        ('Who built Kaizan and where is the company based?',
         'Kaizan was founded by Glen Calvert and Pravin Paratey and is headquartered in London, UK.'),
        ('What does the name "Kaizan" mean?',
         'Kaizan is taken from the Japanese word kaizen (改善), meaning continuous improvement. The product is designed around the same idea: client relationships compound, and small, consistent improvements in how an account manager listens, follows up and reports compound into materially better retention and expansion outcomes.'),
    ]),
    ('Who Kaizan is for', [
        ('Who is Kaizan designed for?',
         'Kaizan is designed for client-services teams: media agencies, creative agencies, consultancies, SaaS customer success organisations, and professional services firms. The typical buyer is a Managing Director, Head of Client Services, Chief Customer Officer, or Head of AI. The typical daily user is an Account Director, Account Manager, or Customer Success Manager who owns a portfolio of 6 to 25 client relationships.'),
        ('How big does my team need to be to get value from Kaizan?',
         'Kaizan is most useful for teams of 10 to 500 client-facing people. Teams over 500 typically run Kaizan in 2 to 3 business units in parallel rather than one global rollout.'),
        ('Is Kaizan a CRM replacement?',
         'No. Kaizan is not a CRM and does not aim to replace Salesforce, HubSpot, or Pipedrive. Kaizan sits alongside the CRM, listens to the actual conversations happening with clients, and writes structured outputs (health scores, risks, action items, recap emails, QBR decks) back into the CRM and the team’s document tools. Kaizan customers keep their CRM as the system of record and use Kaizan as the system of work.'),
    ]),
    ('How Kaizan works', [
        ('How does Kaizan listen to client conversations?',
         'Kaizan ingests three sources: meeting transcripts (from Zoom, Google Meet, Microsoft Teams, Gong and Chorus), email threads (from Gmail and Outlook / Microsoft 365), and chat (from Slack and Microsoft Teams chat). Audio is transcribed by a speech-to-text model with speaker diarisation. Text is parsed for participants, topics, commitments, risks, sentiment and questions.'),
        ('What does Kaizan actually output?',
         'Kaizan and its AI Helpers work 24/7 on every client for all users in your company. Providing an AI Assistant for every user to make them more efficient and a health score across four dimensions - Client Satisfaction, Activity, Relationship, Expansion (the CARE model); (2) a live view of risks and opportunities with the underlying evidence cited from real conversations and interactions; (3) drafted follow-up emails, recap notes, system updates and meeting agendas in the account manager’s voice; (4) an army of AI Helpers working to complete tasks for the team as they arise to improve client ROI, satisfaction and revenue.'),
        ('What is the CARE model?',
         'CARE is Kaizan’s framework for account health and how AI Helpers measure what they need to do on each client, with four pillars. Client Satisfaction measures how many stakeholders are satisfied with the work being done by your company. Activity measures the cadence and quality of touchpoints with stakeholders. Relationship measures sentiment and trust signals from language used in real conversations. Expansion measures observed buying signals, whitespace analysis and growth intent. Each pillar contains 6 sub-sections specific to that area of the relationship, and is scored 0 to 10 in real-time, with the underlying evidence cited and explained.'),
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
         'Yes. Kaizan is hiring engineers, designers, GTM and customer success roles, primarily in London and remote across UK and EU time zones. To express interest, email hello@kaizan.ai. The team is fifteen people as of 2026 and intentionally hiring slowly to preserve quality of work and culture.'),
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
    {nav_html(1, active='Resources')}

    <section class="kz-section-tight" style="padding-top:60px;border-bottom:1px solid var(--kz-line);">
      <div class="kz-eyebrow">FAQ · Last updated April 2026</div>
      <h1 class="kz-h1" style="margin-top:18px;max-width:1100px;">Frequently asked questions about Kaizan.</h1>
      <p class="kz-lede" style="margin-top:18px;max-width:820px;">
        Plain-text answers, written so a person (or a language model) can read any single question and
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
            <a class="kz-btn kz-btn-yellow" href="/demo/">Book a demo</a>
            <a class="kz-btn kz-btn-ghost-light" href="../insights/">Read our insights</a>
          </div>
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('FAQs', 1,
                     'Plain-text answers about Kaizan: designed for people and language models.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# RESEARCH  (Our Research — features the one published report)
# ─────────────────────────────────────────────────────────────────────

# The single published research report. No placeholders — when a second
# report ships, add it to this list and extend render_research().
RESEARCH_REPORT = dict(
    eyebrow='OUR RESEARCH · THE 2026 CLIENT SERVICE REPORT',
    title_a='The Best',
    title_b='vs The Rest.',
    sub='What drives higher revenue and CSAT in the top 10% of clients.',
    lede=("A first-of-its-kind benchmark drawn from 1M+ calls, 10M+ emails and thousands of "
          "chat messages (all anonymised) comparing how client service professionals work on "
          "the relationships that grow versus the ones that slip away."),
    meta='Free · 15 pages · Instant download',
    inside=[
        'The 8 behaviours that consistently mark the top 10% of account teams',
        'The KPIs that actually lead to happier, higher-revenue clients',
        'The CARE framework: how the patterns cluster into four pillars',
    ],
    dataset=[
        ('1M+',  'Anonymised client conversations'),
        ('10M+', 'Emails analysed'),
        ('15',   'Pages of research'),
        ('8',    'Behaviours decoded'),
    ],
    numbers=[
        ('2.2', '×', 'More risks surfaced at top-performing accounts than at bottom-performing ones. '
                     'The accounts that look quiet and healthy usually are not: silence is absence, '
                     'not stability.', 'The Risk Paradox'),
        ('66', '%', 'Of all client-facing calls are handled by just 25% of account managers. Coverage '
                    'across the whole portfolio is the lever most teams leave unpulled.', 'The AM Power Law'),
        ('1.84', '×', 'More calls per account manager on top-performing clients, at the same portfolio '
                      'size, email-to-call ratio and talk-time share. Top accounts are more of the same '
                      'conversation, not a different one.', 'The Ideal AM Profile'),
    ],
    care=[
        ('C', 'Client satisfaction', 'How happy the client is with you and the work being delivered.',
         '4.2×', 'More proactive comms per account at the top decile'),
        ('A', 'Activity with stakeholders', 'Stakeholder coverage and account context: who matters, '
         'what changed this week, the shape of the next conversation.',
         '73%', 'Of top performers maintain a live stakeholder map'),
        ('R', 'Relationship strength', 'Strategic partner or just a vendor? Whether rapport, trust and '
         'sentiment are where they need to be.',
         '2.1h', 'Median first response time at the top 10%'),
        ('E', 'Expansion opportunities', 'Inbound-signal capture and conversion: the quiet ask in '
         'passing, or the proactive suggestion of how to grow their business.',
         '82%', 'Of expansion revenue comes from prioritising commercial conversations early'),
    ],
    audiences=[
        ('Heads of Client Services & CS', 'Set the bar for the team. Benchmark, retrain, repeat.'),
        ('Account Directors & Managers', 'See where your book sits, and what to change on Monday.'),
        ('Agency Leaders', 'An operating system for client-facing teams at scale.'),
        ('Founders & CEOs', 'Retention is the lever. Here is what moves it.'),
        ('C-level teams', '82% of expansion is inbound: the data on how to catch it.'),
        ('Heads of AI & CTOs', 'The metrics, the tooling and the workflow. Page 28 onward.'),
    ],
)


def render_research() -> str:
    r = RESEARCH_REPORT

    inside_html = '\n'.join(
        f'<li><span class="tick" aria-hidden="true">→</span>{E(x)}</li>' for x in r['inside']
    )
    dataset_html = '\n'.join(
        f'''<div class="kz-stat-cell">
          <div class="num">{E(num)}</div>
          <div class="lbl">{E(lbl)}</div>
        </div>''' for num, lbl in r['dataset']
    )
    numbers_html = '\n'.join(
        f'''<div class="kz-research-num">
          <div class="kz-display-stat n">{E(n)}<span class="u">{E(u)}</span></div>
          <p>{E(desc)}</p>
          <div class="kz-eyebrow src">Source · {E(src)}</div>
        </div>''' for n, u, desc, src in r['numbers']
    )
    care_html = '\n'.join(
        f'''<div class="kz-research-care-card">
          <div class="head"><span class="badge">{E(letter)}</span>
            <h3 class="kz-h3">{E(name)}</h3></div>
          <p>{E(desc)}</p>
          <div class="foot"><span class="stat">{E(stat)}</span><span class="note">{E(note)}</span></div>
        </div>''' for letter, name, desc, stat, note in r['care']
    )
    aud_html = '\n'.join(
        f'''<div class="kz-research-aud-card">
          <h3 class="kz-h3" style="font-size:18px;">{E(name)}</h3>
          <p>{E(desc)}</p>
        </div>''' for name, desc in r['audiences']
    )

    body = f'''
    {nav_html(1, active='Resources')}

    <section class="kz-research-hero kz-wash-gold">
      <div class="copy">
        <div class="kz-eyebrow">{E(r['eyebrow'])}</div>
        <h1 class="kz-h1 kz-h1-xl" style="margin:20px 0 0;">
          <span class="kz-mark kz-mark-tight">{E(r['title_a'])}</span> {E(r['title_b'])}
        </h1>
        <p class="kz-h3" style="margin-top:22px;font-weight:500;color:var(--kz-mute);max-width:640px;">
          {E(r['sub'])}
        </p>
        <p class="kz-lede" style="margin-top:18px;max-width:660px;">{E(r['lede'])}</p>
        <ul class="kz-research-inside">{inside_html}</ul>
        <div class="kz-flex" style="gap:12px;margin-top:32px;">
          <a class="kz-btn kz-btn-yellow" href="#get-report">Download the report</a>
          <a class="kz-btn kz-btn-ghost" href="/demo/">Book a demo</a>
        </div>
        <div class="kz-eyebrow" style="margin-top:18px;">{E(r['meta'])}</div>
      </div>
      <aside class="kz-research-cover" aria-hidden="true">
        <div class="kz-research-cover-card">
          <div class="kz-eyebrow" style="color:rgba(255,251,240,.6);">2026 REPORT</div>
          <div class="big">The Best<br>vs<br>The Rest.</div>
          <div class="kz-eyebrow" style="color:var(--kz-yellow);">15 PAGES · FREE</div>
        </div>
      </aside>
    </section>

    <section class="kz-section-x" style="padding-top:48px;padding-bottom:8px;">
      <div class="kz-eyebrow">What you're getting</div>
    </section>
    <div class="kz-stat-row">{dataset_html}</div>

    <section class="kz-section">
      <div class="kz-eyebrow">01 · Unique insights</div>
      <h2 class="kz-h2 kz-h2-lg" style="margin:14px 0 0;max-width:760px;">
        Three numbers that say it <span class="kz-mark kz-mark-tight">all.</span>
      </h2>
      <div class="kz-research-nums">{numbers_html}</div>
    </section>

    <section class="kz-section" style="background:var(--kz-sand);">
      <div class="kz-eyebrow">02 · The framework</div>
      <h2 class="kz-h2 kz-h2-lg" style="margin:14px 0 8px;max-width:820px;">
        CARE: how the patterns cluster.
      </h2>
      <p class="kz-lede" style="margin-bottom:36px;">Eleven behaviours, four pillars: the structure behind every top-decile account team.</p>
      <div class="kz-research-care">{care_html}</div>
    </section>

    <section class="kz-section">
      <div class="kz-eyebrow">03 · Who it's for</div>
      <h2 class="kz-h2 kz-h2-lg" style="margin:14px 0 36px;max-width:880px;">
        If you care about client retention &amp; growth, this is for you.
      </h2>
      <div class="kz-research-aud kz-grid-3">{aud_html}</div>
    </section>

    <section id="get-report" class="kz-cta-band kz-cta-band-dark">
      <div class="kz-eyebrow" style="color:var(--kz-yellow);">Get the full report</div>
      <div class="head">The Best vs The Rest.</div>
      <p style="color:rgba(255,251,240,.75);max-width:520px;margin:18px auto 0;font-size:16px;">
        Free · 15 pages · straight to your inbox. Two fields, no spam.
      </p>
      <form class="kz-research-form" action="#" method="post" onsubmit="return false;">
        <input type="email" name="email" placeholder="Work email" aria-label="Work email" required>
        <button type="submit" class="kz-btn kz-btn-yellow">Get the report</button>
      </form>
    </section>

    {footer_html(1)}
    '''
    return page_head('Our Research', 1,
                     'The 2026 Client Service Report from Kaizan: the data on what great client '
                     'service actually looks like, drawn from 1M+ anonymised client conversations.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# KNOWLEDGE HUB  ("Straight answers on client success and AI" — Q&A base)
# ─────────────────────────────────────────────────────────────────────

# Plain-language glossary / Q&A, grouped into topics. Each answer is written
# to stand alone (readable by a person or a language model).
KNOWLEDGE_HUB_DATA = [
    ('Client intelligence', [
        ('What is client intelligence?',
         "Client intelligence is the practice of turning every interaction across a client "
         "relationship into a structured, real-time view of account health, risk, and opportunity. It "
         "reads the calls, emails, and meetings that fill a relationship, not just the activity logged "
         "in a CRM. The point isn't to record what happened. It's to know what to do next, before a "
         "renewal forces the question."),
        ('How does client intelligence help an agency managing multiple clients?',
         "Client intelligence gives an agency one current view of every client at once, so nothing "
         "slips while attention is on the loudest account. It surfaces which relationships need "
         "attention now, which are quietly slipping, and which are ready to grow, the way a great "
         "account director would if they could sit in on every call."),
        ('How is client intelligence different from a CRM?',
         "Client intelligence reads the relationship, while a CRM stores what you log about it. A CRM "
         "tells you what someone remembered to type in. Client intelligence works from the actual "
         "conversations across calls, emails, and meetings, where intent and risk show up long before "
         "anyone updates a record."),
        ('What data sources feed client intelligence?',
         "Client intelligence draws on communication data (calls, emails, meeting transcripts), "
         "engagement activity, support history, and CRM records. The sharpest signals usually sit in "
         "conversation data, because that's where a client reveals intent and frustration first."),
    ]),
    ('Client success fundamentals', [
        ('What is client success?',
         "Client success, often called customer success in SaaS, is the practice of proactively "
         "helping clients reach their goals so they stay, grow, and refer you. It's a revenue "
         "function, not a support desk, and in agencies it lives inside account management."),
        ('What does an account manager do?',
         "An account manager owns the client relationship and works to keep clients happy, retained, "
         "and growing. Day to day that means running the relationship, leading reviews, catching risks "
         "early, proving the value of the work, and finding room to grow the account."),
        ('What is the difference between account management and client success?',
         "Account management owns the commercial relationship (renewals, growth, the day-to-day), "
         "while client success is the proactive discipline of making sure clients reach their goals. "
         "In agencies the two usually sit in the same role. The cleanest split: client success is "
         "whether the client wins, account management is whether the account grows."),
        ('What is the difference between client success and client support?',
         "Client success is proactive and long-term, while client support is reactive and "
         "issue-by-issue. Support answers the question a client asks today. Success makes sure the "
         "client reaches their goals across the whole relationship."),
        ('What is a client success plan?',
         "A client success plan is a documented strategy that ties a client's goals to the milestones, "
         "owners, and metrics needed to reach them. A good one defines success in the client's terms, "
         "not yours, and makes progress measurable."),
        ('How do you become a trusted advisor to a client?',
         "You become a trusted advisor by moving from order-taker to someone who shapes the client's "
         "decisions, which means understanding their business goals and tying your work to them. It "
         "comes from proactive insight, honest pushback, and showing up with the next idea before the "
         "client asks."),
    ]),
    ('Client onboarding', [
        ('What is client onboarding?',
         "Client onboarding is the process of bringing a new client into your agency and setting the "
         "relationship up to deliver, from kickoff and goal-setting through to access, expectations, "
         "and the first results. It's the highest-leverage moment for retention, because most churn is "
         "won or lost in the first few weeks."),
        ('What should a client onboarding process include?',
         "A strong onboarding process includes a clean handoff from sales to delivery, a kickoff "
         "meeting, a questionnaire to capture goals and access, a clear scope and stakeholder map, and "
         "a plan for the first 30 days. The aim is a fast first win and a client who leaves kickoff "
         "thinking this feels organised."),
        ('What questions should you ask a new client during onboarding?',
         "The most useful onboarding questions cover the client's goals, how they define success, who "
         "the decision-makers are, what their last agency got wrong, and how they prefer to "
         "communicate. Keep the list tight, under fifteen questions, and only ask what the sales "
         "process didn't already answer."),
        ('How do you onboard a client without losing them early?',
         "You hold onto new clients by delivering a quick early win, setting expectations clearly, and "
         "showing you understand their business from day one. A smooth, organised start builds the "
         "trust that carries the relationship through the first rough patch, which is usually when "
         "early churn happens."),
    ]),
    ('Retention and revenue', [
        ('What is client retention?',
         "Client retention is the rate at which a business keeps its clients over a set period, and "
         "the work that goes into keeping them. It's the foundation of stable revenue, because keeping "
         "a client costs far less than winning a new one."),
        ('How do you calculate client retention rate?',
         "Client retention rate is the percentage of clients you keep over a period, not counting new "
         "wins. Calculate it as: (clients at the end of the period - new clients gained) / clients at "
         "the start, times 100. Track it alongside revenue retention, since losing one large client "
         "hurts more than losing several small ones."),
        ('What is a good client retention rate?',
         "A healthy agency client retention rate is usually cited around 80 to 90% a year, though it "
         "varies by sector and service model. What matters more than the benchmark is the trend in "
         "your own numbers and the revenue behind each client, because one large account leaving "
         "outweighs several small ones."),
        ('What is net revenue retention (NRR) and how is it calculated?',
         "Net revenue retention (NRR) is the percentage of recurring revenue you keep from existing "
         "clients over a period, including growth and after losses. Calculate it as: (starting revenue "
         "+ expansion - contraction - churn) / starting revenue. Above 100% means you can grow from "
         "your existing clients alone."),
        ('What is time-to-value and why does it matter?',
         "Time-to-value is how long it takes a new client to see a first meaningful result from "
         "working with you. Shortening it is one of the most reliable ways to reduce early churn, "
         "because a client who sees value quickly is far more likely to stay."),
        ('How do you reduce client churn?',
         "You reduce client churn by catching at-risk clients early, fixing the root cause, and "
         "proving value before the renewal conversation starts. The biggest lever is timing: act on "
         "the warning signals while there's still room to change the outcome, not after the client has "
         "decided to leave."),
    ]),
    ('Client health and risk', [
        ('What is a client health score?',
         "A client health score is a single metric that estimates how likely a client is to renew, "
         "leave, or grow. It blends signals like engagement, sentiment, delivery, and communication "
         "frequency so a team knows which relationships need attention first."),
        ('How do you calculate a client health score?',
         "You calculate a client health score by picking the signals that predict retention, weighting "
         "them by importance, and combining them into one score. Common inputs are engagement, "
         "response times, sentiment, delivery against expectations, and payment behaviour. The right "
         "weighting comes from what actually predicts churn in your own client base."),
        ('What are the warning signs a client is about to leave?',
         "The earliest warning signs are behavioural: replies slow down, meetings get missed or "
         "shortened, scope shrinks, and new stakeholders start appearing on calls. These show up well "
         "before a client gives notice, which is exactly why they're worth tracking."),
        ('What is an at-risk client?',
         "An at-risk client is one showing signals of an elevated chance of leaving or cutting back at "
         "renewal. Typical triggers are falling engagement, an unresolved complaint, a lost champion, "
         "or a gap between the value promised and the value the client feels."),
    ]),
    ('Scope, expectations, and communication', [
        ('What is scope creep?',
         "Scope creep is the gradual expansion of a project beyond its agreed boundaries, usually "
         "through small, undocumented additions that pile up over time. Left unmanaged it erodes "
         "margin and breeds resentment on both sides."),
        ('How do you prevent scope creep?',
         "You prevent scope creep with a specific scope of work, a clear definition of what counts as a "
         "change request, and documentation of every request as it lands. Catching the small asks "
         "early, and naming them as out of scope politely, is what keeps a project profitable."),
        ('How do you manage client expectations?',
         "You manage client expectations by agreeing what success looks like up front, being honest "
         "about timelines and trade-offs, and communicating before problems land rather than after. "
         "Clear, proactive communication is the single biggest driver of whether a client feels well "
         "served."),
        ('How do you keep clients happy?',
         "You keep clients happy by delivering results, communicating proactively, and consistently "
         "connecting your work to their business goals. It comes from a client feeling understood and "
         "seeing value, not from speed alone, and the agencies that retain best treat communication as "
         "part of the deliverable."),
        ('How do you handle an unhappy client?',
         "You handle an unhappy client by responding quickly, listening before defending, owning what "
         "went wrong, and coming back with a concrete plan. Most relationships are recoverable if the "
         "client feels heard and sees you act, and catching the dissatisfaction early is what makes "
         "recovery possible."),
    ]),
    ('Business reviews (QBRs)', [
        ('What is a quarterly business review (QBR)?',
         "A quarterly business review (QBR) is a recurring strategic meeting where you and a client "
         "review progress, show the value delivered, and align on the next quarter. It's a "
         "relationship checkpoint, not a status update, and in agencies it's often run monthly."),
        ('What should a client business review include?',
         "A strong review covers goals and progress, the value and outcomes delivered, current "
         "challenges, and a plan for the next period. The best ones surface growth opportunities and "
         "renewal context, and they stay anchored to the client's business objectives, not your "
         "activity log."),
        ('How do you run an effective client review?',
         "You run an effective review by preparing around the client's goals, leading with outcomes "
         "instead of activity, and using the time to set direction. Bring the numbers on value "
         "delivered, get the right people in the room, and leave with owned next steps."),
        ('How often should you review clients?',
         "Most teams run a formal client review quarterly, with lighter monthly check-ins, though the "
         "right cadence depends on account size and complexity. Larger or strategic clients usually "
         "warrant more frequent reviews, and smaller ones often do fine with a lighter touch."),
    ]),
    ('Client reporting', [
        ('What should a client report include?',
         "A strong client report leads with progress against the client's goals, shows the outcomes "
         "and value delivered, explains what the numbers mean, and sets out what's next. The best "
         "reports translate activity into business impact, rather than handing the client a pile of "
         "metrics to interpret."),
        ('How often should you report to clients?',
         "Most agencies report monthly, with a deeper review quarterly, though the right rhythm depends "
         "on the client and the pace of the work. Consistency matters more than frequency, because a "
         "predictable report a client can rely on builds more trust than sporadic detail."),
    ]),
    ('Expansion and growth', [
        ('What is account expansion?',
         "Account expansion is revenue growth from existing clients through additional services, wider "
         "scope, and larger retainers. It's one of the most efficient ways to grow, because expanding "
         "a happy client costs far less than winning a new one."),
        ('What is the difference between upsell and cross-sell?',
         "An upsell grows what a client already buys (a bigger retainer, more scope), while a "
         "cross-sell adds a different service alongside it. An upsell deepens the commitment, and a "
         "cross-sell broadens it."),
        ('How do you identify expansion opportunities with a client?',
         "You spot expansion by reading the signals that a client is ready for more: strong results, "
         "new goals, growing teams, or needs raised in conversation. The clearest of these usually "
         "surface in what clients say on calls, where they describe problems your current scope "
         "doesn't cover yet."),
    ]),
    ('Metrics and benchmarks', [
        ('What is churn rate and how is it calculated?',
         "Churn rate is the percentage of clients or revenue lost over a period. Client churn is "
         "clients lost divided by clients at the start of the period; revenue churn swaps client "
         "counts for recurring revenue. Revenue churn is often the more useful number, because not "
         "every client is worth the same."),
        ('What is client lifetime value (LTV)?',
         "Client lifetime value (LTV) is the total revenue you can expect from one client across the "
         "whole relationship. Paired with the cost to acquire them, it shows whether the economics "
         "hold up, with a healthy LTV to acquisition-cost ratio often cited near 3 to 1."),
        ('What is the difference between NPS, CSAT, and CES?',
         "NPS, CSAT, and CES each measure something different. NPS (net promoter score) gauges "
         "long-term loyalty and likelihood to recommend, CSAT (customer satisfaction) measures how "
         "happy a client was with a specific interaction, and CES (customer effort score) measures how "
         "easy that interaction was. Used together they give a fuller picture than any one alone."),
    ]),
    ('AI for client management and account managers', [
        ('How is AI used in account management?',
         "AI is used in account management to read client conversations at scale, flag risk and "
         "opportunity early, and prepare the account manager for reviews and renewals. Its real edge "
         "is coverage: AI can read every call, email, and meeting across a whole book of clients, "
         "which no team can do by hand."),
        ('How can AI help account managers manage multiple clients?',
         "AI helps account managers cover a full book of clients by keeping a current view of every "
         "relationship, not just the ones touched this week. It reads the calls, emails, and meetings "
         "across every account, flags who needs attention, and takes the manual tracking off the "
         "manager's plate, so a lean team can give each client the attention once reserved for the top "
         "few."),
        ('Can AI predict client churn?',
         "Yes. AI predicts churn by spotting patterns across engagement, sentiment, and conversation "
         "data that tend to come before a client leaves. The value is timing: it flags risk early "
         "enough to act, not after the decision is made."),
        ('What is conversation intelligence?',
         "Conversation intelligence is the use of AI to analyse calls, emails, and meetings for "
         "sentiment, risk, intent, and opportunity. For client teams it turns thousands of scattered "
         "interactions into signals you can act on, instead of insight that stays buried in "
         "transcripts and inboxes."),
        ('How does AI help agencies prove value to clients?',
         "AI helps agencies prove value by pulling the evidence of work and outcomes together for "
         "reviews and renewals, so an account manager walks in prepared rather than scrambling. It "
         "surfaces what was delivered, where results landed, and what's next, which is the case that "
         "keeps a client renewing."),
    ]),
    ('Voice of client', [
        ('What is voice of client (voice of customer)?',
         "Voice of client, also known as voice of customer (VoC), is the structured capture and "
         "analysis of what clients say about their needs, expectations, and experience. It puts the "
         "client's actual words into your decisions, so teams act on evidence instead of assumption."),
        ('How do you collect voice of client data?',
         "You collect it from surveys, interviews, reviews, and increasingly from the conversations "
         "that already happen on calls, emails, and meetings. Analysing existing conversations scales "
         "best, because it captures honest, in-context feedback without asking clients to do more "
         "work."),
        ('How do you turn client feedback into action?',
         "You turn feedback into action by grouping what clients say into themes, ranking them by "
         "impact and frequency, routing each to the team that owns it, and closing the loop with the "
         "client. Insight only pays off when it changes a decision."),
    ]),
]


def render_knowledge_hub() -> str:
    toc_html = '\n'.join(
        f'<li><span class="num">{i+1:02d}</span>'
        f'<a href="#{faq_anchor(name)}">{E(name)}</a></li>'
        for i, (name, _qs) in enumerate(KNOWLEDGE_HUB_DATA)
    )
    sections_html = []
    for i, (name, qs) in enumerate(KNOWLEDGE_HUB_DATA):
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
    {nav_html(1, active='Resources')}

    <section class="kz-section-tight" style="padding-top:60px;border-bottom:1px solid var(--kz-line);">
      <div class="kz-eyebrow">Knowledge Hub · Client success &amp; account management</div>
      <h1 class="kz-h1" style="margin-top:18px;max-width:1100px;line-height:1.28;">
        <span class="kz-mark kz-mark-tight">Client success</span> and account management: FAQs
      </h1>
      <p class="kz-lede" style="margin-top:18px;max-width:820px;">
        A resource hub of the questions agency account managers and client teams actually search for,
        from onboarding and retention to client health, reporting, and using AI across a full book of
        clients.
      </p>
    </section>

    <section class="kz-faq-toc">
      <div class="kz-eyebrow" style="margin-bottom:14px;">On this page</div>
      <ol>{toc_html}</ol>
    </section>

    <section class="kz-faq-body kz-kh-body">
      <div class="kz-faq-content kz-kh-content">
        {''.join(sections_html)}
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Knowledge Hub', 1,
                     'Client success and account management FAQs: a resource hub covering client '
                     'intelligence, onboarding, retention, client health, reviews, reporting, '
                     'expansion, metrics and AI for account managers.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────

def render_demo() -> str:
    """Anti-bot interstitial for /demo/.

    Buttons across the site link here instead of straight to the calendar. The
    real booking URL is base64-obfuscated and only revealed after a Cloudflare
    Turnstile human-check passes — so crawlers can't scrape the link, and the
    common headless-bot bookers are stopped by Turnstile. This is a static page
    (no server-side token verification), which is the practical ceiling on
    GitHub Pages; it kills link-harvesting and most automated bookings."""
    import base64
    enc = base64.b64encode(CALENDAR_URL.encode()).decode()

    extra_head = (
        '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" '
        'async defer></script>'
    )

    body = f'''
    {nav_html(1)}

    <section class="kz-section-tight" style="min-height:60vh;display:flex;align-items:center;justify-content:center;padding:80px 0;">
      <div style="max-width:520px;width:100%;text-align:center;">
        <div class="kz-eyebrow" style="justify-content:center;">Book a demo · 30-min live walkthrough</div>
        <h1 class="kz-h1" style="margin-top:18px;font-size:34px;">One quick check, then your calendar.</h1>
        <p class="kz-lede" style="margin-top:16px;">
          We ask everyone to confirm they're human before booking. It keeps our
          calendar clear for real conversations. This takes a second.
        </p>

        <div style="display:flex;justify-content:center;margin:28px 0 8px;">
          <div class="cf-turnstile"
               data-sitekey="{TURNSTILE_SITE_KEY}"
               data-callback="kzOnVerified"
               data-error-callback="kzOnError"></div>
        </div>

        <p id="kz-demo-status" role="status" aria-live="polite"
           style="min-height:22px;color:var(--kz-ink-soft, #6b6b6b);font-size:14px;"></p>

        <noscript>
          <p class="kz-lede" style="margin-top:12px;">
            JavaScript is required to book online. Email
            <a href="mailto:hello@kaizan.ai" style="color:var(--kz-ink);text-decoration:underline;">hello@kaizan.ai</a>
            and we'll set up a time.
          </p>
        </noscript>

        <p style="margin-top:20px;font-size:14px;color:var(--kz-ink-soft, #6b6b6b);">
          Trouble verifying? Email
          <a href="mailto:hello@kaizan.ai" style="color:var(--kz-ink);text-decoration:underline;">hello@kaizan.ai</a>.
        </p>
      </div>
    </section>

    <script>
    (function () {{
      var DEST = '{enc}';
      var statusEl = document.getElementById('kz-demo-status');
      // Both UK and /us/ redirect to a Calendly link (different reps), and
      // both carry the visit's UTMs, captured earlier by
      // assets/js/calendly-utm.js into the same sessionStorage key.
      var UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
      var UTM_STORE = 'calendly_utms';
      function withUtms(dest) {{
        try {{
          var url = new URL(dest);
          if (url.hostname.indexOf('calendly.com') === -1) return dest;
          var saved = JSON.parse(sessionStorage.getItem(UTM_STORE) || '{{}}');
          UTM_KEYS.forEach(function (k) {{ if (saved[k]) url.searchParams.set(k, saved[k]); }});
          return url.toString();
        }} catch (e) {{ return dest; }}
      }}
      window.kzOnVerified = function () {{
        if (statusEl) statusEl.textContent = 'Verified, opening the calendar…';
        window.location.href = withUtms(atob(DEST));
      }};
      window.kzOnError = function () {{
        if (statusEl) statusEl.textContent = 'Verification failed. Please refresh and try again, or email hello@kaizan.ai.';
      }};
    }})();
    </script>

    {footer_html(1)}
    '''
    return page_head('Book a demo', 1,
                     "Confirm you're human, then book a 30-minute live demo of Kaizan.",
                     extra_head=extra_head) + body + page_foot()


def render_demo_confirmed() -> str:
    """/demo-confirmed/ — set as the Confirmation Page redirect on the Calendly
    event type both /demo/ links point to, so a visitor lands here right after
    booking a slot (UK and US both redirect here; nothing routes them by rep)."""
    body = f'''
    {nav_html(1)}

    <section class="kz-section-tight" style="min-height:60vh;display:flex;align-items:center;justify-content:center;padding:80px 0;">
      <div style="max-width:520px;width:100%;text-align:center;">
        <div class="kz-trial-badge" style="justify-content:center;"><span class="dot"></span>You're booked</div>
        <h1 class="kz-h1" style="margin-top:18px;font-size:34px;">Thanks, we&rsquo;ll see you soon.</h1>
        <p class="kz-lede" style="margin-top:16px;">
          Your demo is confirmed, check your inbox for the calendar invite with the
          details and a link to join.
        </p>
        <div style="margin-top:28px;">
          <a class="kz-btn kz-btn-yellow" href="/">Back to homepage</a>
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Demo booked', 1,
                     "Your demo with Kaizan is confirmed, check your inbox for the details.",
                     extra_head='<meta name="robots" content="noindex">') + body + page_foot()


def render_white_paper_confirmation() -> str:
    """/white-paper-confirmation/ — where the CARE white paper lead form
    (assets/js/white-paper.js, on /white-paper/) sends the visitor after a
    successful HubSpot submission, instead of showing the inline success
    state on the form itself."""
    body = f'''
    {nav_html(1)}

    <section class="kz-section-tight" style="min-height:60vh;display:flex;align-items:center;justify-content:center;padding:80px 0;">
      <div style="max-width:520px;width:100%;text-align:center;">
        <div class="kz-trial-badge" style="justify-content:center;"><span class="dot"></span>On its way</div>
        <h1 class="kz-h1" style="margin-top:18px;font-size:34px;">Thanks, check your inbox.</h1>
        <p class="kz-lede" style="margin-top:16px;">
          We&rsquo;ve sent the CARE white paper to your email address, it should land in
          the next few minutes.
        </p>
        <div style="margin-top:28px;">
          <a class="kz-btn kz-btn-yellow" href="/">Back to homepage</a>
        </div>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Thanks for downloading', 1,
                     "The CARE white paper is on its way to your inbox.",
                     extra_head='<meta name="robots" content="noindex">') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# POLICIES — versioned legal documents (Privacy / Licence / Cookies).
# Source of truth: content/policies/<slug>/<YYYY-MM-DD>.html, one file per
# version, filename = the date that version took effect. The newest file
# becomes the live page at /<slug>/; every file also gets a dated archive
# page at /<slug>/<date>/. See content/policies/README.md.
# ─────────────────────────────────────────────────────────────────────

POLICIES = [
    dict(slug='privacy-policy', title='Privacy Policy',
         desc='How Kaizan Limited collects, uses and protects your personal data.'),
    dict(slug='license-agreement', title='Licence Agreement',
         desc='The terms on which Kaizan Limited supplies the Kaizan software.'),
    dict(slug='cookie-policy', title='Cookie Policy',
         desc='The cookies Kaizan uses on its website and app, and how to manage them.'),
    dict(slug='data-processing-agreement', title='Data Processing Agreement',
         desc='How Kaizan processes personal data on behalf of its customers.'),
]


def _policy_date(iso: str) -> str:
    """'2025-10-01' → '1 October 2025'."""
    from datetime import date
    d = date.fromisoformat(iso)
    return f'{d.day} {d.strftime("%B %Y")}'


def load_policy_versions(slug: str) -> list[dict]:
    """All versions of a policy, newest first."""
    folder = ROOT / 'content' / 'policies' / slug
    return [dict(date=f.stem, body=f.read_text(encoding='utf-8'))
            for f in sorted(folder.glob('????-??-??.html'), reverse=True)]


def _policy_pdf_name(slug: str, date: str) -> str | None:
    """Site-relative filename of a version's PDF, if one was committed
    alongside the HTML source (content/policies/<slug>/<date>.pdf)."""
    if (ROOT / 'content' / 'policies' / slug / f'{date}.pdf').exists():
        return f'kaizan-{slug}-{date}.pdf'
    return None


def _policy_pdf_button(slug: str, date: str, p: str) -> str:
    pdf = _policy_pdf_name(slug, date)
    if not pdf:
        return ''
    return (f'<div class="kz-policy-actions">'
            f'<a class="kz-btn kz-btn-ghost kz-btn-pdf" href="{p}{slug}/{pdf}" download>'
            f'Download PDF <span class="arr">↓</span></a></div>')


def render_policy(pol: dict, version: dict, versions: list[dict], dated: bool) -> str:
    """One policy page. The live page (/<slug>/, depth 1) shows the newest
    version; dated archive pages (/<slug>/<date>/, depth 2) show each version,
    with a banner and noindex when it is no longer the current one."""
    depth = 2 if dated else 1
    p = relpath(depth)
    is_latest = version['date'] == versions[0]['date']

    banner = '' if is_latest else f'''
        <div class="kz-policy-banner">
          You are reading an archived version of this document, last updated
          {_policy_date(version['date'])}.
          <a href="{p}{pol['slug']}/">Read the current version →</a>
        </div>'''

    items = []
    for v in versions:
        href = f'{p}{pol["slug"]}/' if v is versions[0] else f'{p}{pol["slug"]}/{v["date"]}/'
        here = ' aria-current="page"' if v['date'] == version['date'] else ''
        tag = ' <span class="kz-policy-tag">Current</span>' if v is versions[0] else ''
        v_pdf = _policy_pdf_name(pol['slug'], v['date'])
        pdf_link = (f' · <a class="kz-policy-pdf-link" href="{p}{pol["slug"]}/{v_pdf}">PDF</a>'
                    if v_pdf else '')
        items.append(f'<li><a href="{href}"{here}><time datetime="{v["date"]}">'
                     f'{_policy_date(v["date"])}</time></a>{tag}{pdf_link}</li>')
    versions_html = f'''
        <div class="kz-policy-versions" id="version-history">
          <h2>Version history</h2>
          <p>Earlier versions of this document stay available, so you can see
             exactly what applied on a given date.</p>
          <ul>{''.join(items)}</ul>
        </div>'''

    body = f'''
    {nav_html(depth)}
    <article class="kz-policy">
      <div class="kz-policy-inner">
        <div class="kz-eyebrow">Legal</div>
        <h1 class="kz-post-title">{E(pol['title'])}</h1>
        <p class="kz-policy-meta">Last updated
          <time datetime="{version['date']}">{_policy_date(version['date'])}</time>
          · <a href="#version-history">Version history</a></p>
        {_policy_pdf_button(pol['slug'], version['date'], p)}
        {banner}
        <div class="kz-policy-body">
{version['body']}
        </div>
        {versions_html}
      </div>
    </article>
    {footer_html(depth)}
    '''
    title = pol['title'] if is_latest else f'{pol["title"]}, {_policy_date(version["date"])}'
    # Archive pages shouldn't compete with the live page in search results.
    extra_head = '<meta name="robots" content="noindex">' if dated else ''
    return page_head(title, depth, pol['desc'], extra_head=extra_head) + body + page_foot()


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f'  wrote {path.relative_to(ROOT)}')


def _remove_page(directory: Path):
    """Delete a generated page directory so a disabled page stops being served.
    Keeps build output in sync with the source (no stale pages left behind)."""
    import shutil
    if directory.exists():
        shutil.rmtree(directory)
        print(f'  removed {directory.relative_to(ROOT)}/')


def render_redirect(target: str) -> str:
    """A tiny redirect stub for a legacy URL. Meta-refresh + JS forward, plus a
    canonical to the target so search engines consolidate ranking onto it."""
    canon = f'https://kaizan.ai{target}'
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<title>Redirecting…</title>\n'
        f'<link rel="canonical" href="{E(canon)}">\n'
        f'<meta http-equiv="refresh" content="0; url={E(target)}">\n'
        f'<script>location.replace({json.dumps(target)})</script>\n'
        '</head><body>\n'
        f'<p>This page has moved to <a href="{E(target)}">{E(target)}</a>.</p>\n'
        '</body></html>\n'
    )


def write_redirects():
    """Generate redirect stub pages for legacy (pre-migration) URLs so they no
    longer 404. Map lives in tools/redirects.json ({old_path: new_url})."""
    map_file = Path(__file__).resolve().parent / 'redirects.json'
    if not map_file.exists():
        return
    redirects = json.loads(map_file.read_text(encoding='utf-8'))
    written = skipped = 0
    for old, new in redirects.items():
        dest = ROOT / old.strip('/') / 'index.html'
        # never clobber a real generated page
        if dest.exists():
            skipped += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_redirect(new), encoding='utf-8')
        written += 1
    print(f'  ({written} redirect stub(s) written, {skipped} skipped — real page exists)')


# ── US locale ──────────────────────────────────────────────────────────
# The UK site is the default (root). After it's built we mirror every page
# into /us/ with US spelling, the US booking link, the US legal entity, and
# self-canonical + hreflang tags so each market is independently indexable.

US_CALENDAR_URL = 'https://calendly.com/ray-kaizan/30min'
SITE_ORIGIN = 'https://kaizan.ai'

# US-only trial-form config: a separate Mailchimp embed instance (f_id) and
# tag IDs, so US leads route differently downstream from UK ones.
US_TRIAL_MC_F_ID = '0018efe5f0'
US_TRIAL_TAGS = '3789549,3789550'

# en-GB → en-US spelling (base forms; -ing/-ed/-ation variants listed explicitly
# where they occur). Applied to visible text only, case-preserving.
US_SPELLING = {
    'optimise': 'optimize', 'optimised': 'optimized', 'optimising': 'optimizing',
    'optimisation': 'optimization', 'optimises': 'optimizes',
    'organise': 'organize', 'organised': 'organized', 'organising': 'organizing',
    'organisation': 'organization', 'organisations': 'organizations', 'organisational': 'organizational',
    'personalise': 'personalize', 'personalised': 'personalized', 'personalising': 'personalizing',
    'personalisation': 'personalization',
    'prioritise': 'prioritize', 'prioritised': 'prioritized', 'prioritising': 'prioritizing',
    'recognise': 'recognize', 'recognised': 'recognized', 'recognising': 'recognizing',
    'analyse': 'analyze', 'analysed': 'analyzed', 'analysing': 'analyzing',
    'maximise': 'maximize', 'maximised': 'maximized', 'maximising': 'maximizing',
    'minimise': 'minimize', 'minimised': 'minimized', 'minimising': 'minimizing',
    'standardise': 'standardize', 'standardised': 'standardized', 'standardising': 'standardizing',
    'standardisation': 'standardization',
    'categorise': 'categorize', 'categorised': 'categorized',
    'summarise': 'summarize', 'summarised': 'summarized', 'summarising': 'summarizing',
    'utilise': 'utilize', 'utilised': 'utilized', 'utilising': 'utilizing', 'utilisation': 'utilization',
    'specialise': 'specialize', 'specialised': 'specialized', 'specialising': 'specializing',
    'realise': 'realize', 'realised': 'realized', 'realising': 'realizing',
    'emphasise': 'emphasize', 'emphasised': 'emphasized',
    'customise': 'customize', 'customised': 'customized', 'customising': 'customizing',
    'customisation': 'customization',
    'centralise': 'centralize', 'centralised': 'centralized',
    'capitalise': 'capitalize', 'capitalised': 'capitalized',
    'colour': 'color', 'colours': 'colors', 'coloured': 'colored',
    'behaviour': 'behavior', 'behaviours': 'behaviors', 'behavioural': 'behavioral',
    'favour': 'favor', 'favourite': 'favorite', 'favourable': 'favorable', 'favoured': 'favored',
    'labour': 'labor', 'honour': 'honor', 'honoured': 'honored',
    'centre': 'center', 'centres': 'centers', 'centred': 'centered',
    'licence': 'license', 'licences': 'licenses',
    'defence': 'defense', 'offence': 'offense',
    'programme': 'program', 'programmes': 'programs',
    'catalogue': 'catalog', 'catalogues': 'catalogs',
    'fulfil': 'fulfill', 'fulfilment': 'fulfillment', 'enrolment': 'enrollment',
    'travelled': 'traveled', 'travelling': 'traveling',
    'cancelled': 'canceled', 'cancelling': 'canceling',
    'modelling': 'modeling', 'modelled': 'modeled',
    'labelled': 'labeled', 'labelling': 'labeling',
    'grey': 'gray', 'whilst': 'while', 'amongst': 'among',
    'judgement': 'judgment', 'acknowledgement': 'acknowledgment',
}
_US_SPELL_RE = re.compile(r'\b(' + '|'.join(sorted(US_SPELLING, key=len, reverse=True)) + r')\b', re.I)


def _match_case(src: str, repl: str) -> str:
    if src.isupper():   return repl.upper()
    if src[:1].isupper(): return repl.capitalize()
    return repl


def us_spell(text: str) -> str:
    return _US_SPELL_RE.sub(lambda m: _match_case(m.group(0), US_SPELLING[m.group(0).lower()]), text)


def _spell_text_nodes(html: str) -> str:
    # Transform visible text only; never touch <script>/<style> contents.
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', html, flags=re.S | re.I)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'>([^<]+)<', lambda m: '>' + us_spell(m.group(1)) + '<', parts[i])
    # Also transform meta description / og:description content (attributes).
    parts_joined = ''.join(parts)
    parts_joined = re.sub(r'(name="description" content=")([^"]*)(")',
                          lambda m: m.group(1) + us_spell(m.group(2)) + m.group(3), parts_joined)
    parts_joined = re.sub(r'(property="og:description" content=")([^"]*)(")',
                          lambda m: m.group(1) + us_spell(m.group(2)) + m.group(3), parts_joined)
    return parts_joined


def _hreflang_block(path: str) -> str:
    return (f'<link rel="alternate" hreflang="en-GB" href="{SITE_ORIGIN}{path}">'
            f'<link rel="alternate" hreflang="en-US" href="{SITE_ORIGIN}/us{path if path != "/" else "/"}">'
            f'<link rel="alternate" hreflang="x-default" href="{SITE_ORIGIN}{path}">')


def build_us_locale():
    """Mirror every UK page into /us/ with US spelling, booking link, legal
    entity and self-canonical + hreflang. Relative page links resolve within
    /us/ automatically; only assets and the handful of absolute internal links
    (/ , /demo/, /for/) need rewriting."""
    import base64, shutil
    us_dir = ROOT / 'us'
    if us_dir.exists():
        shutil.rmtree(us_dir)

    uk_cal_b64 = base64.b64encode(CALENDAR_URL.encode()).decode()
    us_cal_b64 = base64.b64encode(US_CALENDAR_URL.encode()).decode()

    skip_top = {'us', 'assets', 'node_modules', 'content', 'tools', '.git', '.github'}

    def _safe(rel: Path) -> bool:
        # Only real page paths — guards against stray/garbage files in the tree.
        return all(re.fullmatch(r'[A-Za-z0-9._-]+', part) for part in rel.parts)

    pages = [f for f in ROOT.rglob('*.html')
             if f.relative_to(ROOT).parts[0] not in skip_top and _safe(f.relative_to(ROOT))]

    written = 0
    for f in pages:
        rel = f.relative_to(ROOT)
        # URL path for hreflang/canonical: /product/, /, /404.html …
        if rel.name == 'index.html':
            path = '/' + ('' if rel.parent == Path('.') else str(rel.parent).replace('\\', '/') + '/')
        else:
            path = '/' + str(rel).replace('\\', '/')

        html = f.read_text(encoding='utf-8')

        # 1. Inject hreflang into the UK page (idempotent) and write it back.
        if 'hreflang=' not in html:
            html = html.replace('</title>', '</title>\n' + _hreflang_block(path), 1)
            f.write_text(html, encoding='utf-8')

        # 2. Build the US version.
        us = html
        # Assets → root-absolute (shared, no duplication).
        us = re.sub(r'(["\'(])(?:\.\./)*assets/', r'\1/assets/', us)
        # calendly-utm.js (from page_head()) is kept as-is — /us/ also books
        # via Calendly, just a different link (US_CALENDAR_URL, below).
        # Absolute internal page links → /us-prefixed (home, /demo/, /for/).
        us = us.replace('href="/"', 'href="/us/"')
        us = re.sub(r'href="/(demo|for|referral-partners)(/|")', r'href="/us/\1\2', us)
        # Self-canonical + og:url for the US page.
        us = us.replace(f'rel="canonical" href="{SITE_ORIGIN}',
                        f'rel="canonical" href="{SITE_ORIGIN}/us')
        us = us.replace(f'property="og:url" content="{SITE_ORIGIN}',
                        f'property="og:url" content="{SITE_ORIGIN}/us')
        # US booking link (only the /demo/ interstitial carries it, base64-encoded).
        us = us.replace(uk_cal_b64, us_cal_b64)
        # About page CTA names the rep it books with — Glen on the UK link,
        # Ray on the US one — so it stays accurate after the link swap above.
        us = us.replace('Book time with Glen →', 'Book time with Ray →')
        # US legal entity.
        us = us.replace('Kaizan Ltd.', 'Kaizan Inc.')
        # US spelling.
        us = _spell_text_nodes(us)
        # Homepage: drop TradeDoubler from the client-logo belt — the brand
        # isn't well known in the US, so it's stripped from the US marquee.
        if path == '/':
            us = re.sub(
                r'<span class="kz-marquee-item"><span class="kz-marquee-logo"[^>]*>'
                r'<img[^>]*tradedoubler[^>]*></span><span class="sep">✺</span></span>',
                '', us)
            # US-only trial-form Mailchimp config: a different form instance
            # (f_id) and tag IDs than the UK form, so US signups route and
            # tag distinctly. The UK homepage keeps the original config.
            us = us.replace(f'f_id={TRIAL_MC_F_ID}', f'f_id={US_TRIAL_MC_F_ID}')
            us = us.replace(f'name="tags" value="{TRIAL_MC_TAGS}"',
                             f'name="tags" value="{US_TRIAL_TAGS}"')
        # US-only persona titles: match the retitled "I am a…" selector labels.
        # UK source keeps its own titles; these rewrites apply to /us/ only.
        # (Upper-case plural runs before singular so it isn't half-matched.)
        for old, new in (
            ('CLIENT SERVICE DIRECTORS',    'HEADS OF CLIENT SERVICES'),
            ('Client Service Directors',    'Heads of Client Services'),
            ('client service directors',    'heads of client services'),
            ('CLIENT SERVICE DIRECTOR',     'HEAD OF CLIENT SERVICES'),
            ('SENIOR LEADERSHIP / DIRECTOR', 'SENIOR LEADERSHIP'),
        ):
            us = us.replace(old, new)
        # US pricing page: swap the mirrored GBP tier cards + footnote for the
        # USD version (lambda replacement avoids re backreference escaping).
        if path == '/pricing/':
            us = re.sub(r'<section class="kzp">.*?</section>',
                        lambda m: us_pricing_section(), us, count=1, flags=re.S)

        out = us_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(us, encoding='utf-8')
        written += 1

    # Mirror policy PDFs so their (relative) links resolve under /us/ too.
    for pdf in ROOT.rglob('*.pdf'):
        if pdf.relative_to(ROOT).parts[0] in skip_top:
            continue
        dest = us_dir / pdf.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, dest)

    print(f'  ({written} US locale page(s) written to /us/)')


def main():
    print(f'Building Kaizan site → {ROOT}')

    # Top-level pages
    write(ROOT / 'index.html',                  render_home())
    write(ROOT / 'product' / 'index.html',      render_product())
    write(ROOT / 'integrations' / 'index.html', render_integrations())
    write(ROOT / 'pricing' / 'index.html',      render_pricing())
    write(ROOT / 'security' / 'index.html',     render_security())
    # Careers page disabled until the content is ready. render_careers() is kept
    # for easy re-enable. The /careers/ directory is removed on build so the page
    # 404s rather than serving stale content.
    _remove_page(ROOT / 'careers')
    write(ROOT / 'faq' / 'index.html',          render_faq())
    write(ROOT / 'research' / 'index.html',     render_research())
    write(ROOT / 'knowledge-hub' / 'index.html', render_knowledge_hub())
    write(ROOT / 'customers' / 'index.html',    render_customers())
    # /insights/ retired — the blog now lives at /blog/. render_insights() kept
    # for easy revert; the directory is removed so it doesn't serve stale content.
    _remove_page(ROOT / 'insights')
    write(ROOT / 'about' / 'index.html',        render_about())
    write(ROOT / 'demo' / 'index.html',         render_demo())
    write(ROOT / 'confirmation' / 'index.html', render_confirmation())
    write(ROOT / 'demo-confirmed' / 'index.html', render_demo_confirmed())
    write(ROOT / 'white-paper-confirmation' / 'index.html', render_white_paper_confirmation())
    write(ROOT / 'customer-success-software' / 'index.html',
                                                 render_customer_success_software())
    write(ROOT / '404.html',                    render_404())

    # Marketing / campaign landing pages
    write(ROOT / 'marketing' / 'july-offer' / 'index.html', render_july_offer())

    # Persona pages
    for slug in PERSONAS:
        write(ROOT / 'for' / slug / 'index.html', render_persona(slug))

    # Case-study detail pages
    for slug in CASE_DATA:
        write(ROOT / 'customers' / slug / 'index.html', render_case_study(slug))

    # Blog — Markdown posts from content/blog/<slug>/index.md (see tools/blog.py).
    # Drafts (draft: true) are excluded unless `python3 tools/build.py --drafts`.
    posts = blog.load_posts(include_drafts='--drafts' in sys.argv)
    write(ROOT / 'blog' / 'index.html', render_blog_index(posts))
    for post in posts:
        blog.copy_post_images(post['slug'])
        write(ROOT / 'blog' / post['slug'] / 'index.html', render_blog_post(post))
    print(f'  ({len(posts)} blog post(s) built)')

    # Policies — versioned legal documents from content/policies/ (see README there).
    n_pol = 0
    for pol in POLICIES:
        versions = load_policy_versions(pol['slug'])
        if not versions:
            continue
        write(ROOT / pol['slug'] / 'index.html',
              render_policy(pol, versions[0], versions, dated=False))
        n_pol += 1
        # Only superseded versions get dated archive URLs; the current version
        # lives at the undated URL alone.
        for v in versions[1:]:
            write(ROOT / pol['slug'] / v['date'] / 'index.html',
                  render_policy(pol, v, versions, dated=True))
            n_pol += 1
        # Copy committed per-version PDFs next to the pages.
        import shutil
        for v in versions:
            pdf = _policy_pdf_name(pol['slug'], v['date'])
            if pdf:
                src = ROOT / 'content' / 'policies' / pol['slug'] / f'{v["date"]}.pdf'
                shutil.copy2(src, ROOT / pol['slug'] / pdf)
                print(f'  wrote {pol["slug"]}/{pdf}')
    print(f'  ({n_pol} policy version(s) built)')

    write_redirects()

    build_us_locale()

    # Referral Partner Program landing page. Exact static export of the approved
    # design (self-contained markup + styles, native <details> FAQ, images under
    # assets/img/referral/). Emitted after build_us_locale() because that wipes
    # and rebuilds the /us/ tree. The USD source ships to /us/; a GBP version
    # (figures converted at ~1 GBP = 1.25 USD) ships to the UK root. The count-up
    # reads its currency symbol from the figure text, so it animates in the right
    # currency on each.
    ref_usd = (ROOT / 'content' / 'referral-partners' / 'index.html').read_text(encoding='utf-8')
    ref_gbp = (ref_usd
               .replace('$7,500', '£6,000')
               .replace('$22,050', '£17,640')
               .replace('$22,000', '£17,600')
               .replace('data-target="22050"', 'data-target="17640"')
               # UK "Book a call" CTAs point to the UK partner calendar.
               .replace('https://calendar.app.google/nXCQjV6kHfsmDs5c7',
                        'https://calendar.app.google/eWwFxNXq3mCZqw7HA'))
    for path_rel, html in ((ROOT / 'referral-partners' / 'index.html', ref_gbp),
                           (ROOT / 'us' / 'referral-partners' / 'index.html', ref_usd)):
        path_rel.parent.mkdir(parents=True, exist_ok=True)
        path_rel.write_text(html, encoding='utf-8')
    print('  (referral partner page → /referral-partners/ [GBP] + /us/referral-partners/ [USD])')

    print('Done.')


if __name__ == '__main__':
    main()
