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
    ('Home',         '/'),
    ('Product',      'product/'),
    # Sentinel: nav_html renders this as a hover dropdown listing PERSONA_LIST.
    ('Personas',     '__personas_dropdown__'),
    ('Integrations', 'integrations/'),
    # TODO: re-enable "Blog" once posts are ready.
    # ('Blog',         'insights/'),
    ('Pricing',      'pricing/'),
    # TODO: re-enable "Clients" nav item once the customer-stories content is ready.
    # ('Clients',      'customers/'),
    # Sentinel-ish: nav_html renders "Resources" as a hover dropdown listing
    # RESOURCES_MENU. The trigger itself points at the first item (Our Research).
    ('Resources',    'research/'),
    ('About',        'about/'),
]

# Sub-links shown in the "Resources" nav dropdown. The "Resources" trigger
# itself points at the Our Research page (research/, set in NAV above); the
# dropdown lists the other resources. FAQ maps to /faq/; Security is the
# Trust & Security page. Third column class (is-yellow / is-mute) is reserved
# for an optional glyph treatment.
RESOURCES_MENU = [
    ('Knowledge Hub', 'knowledge-hub/',  'is-mute'),
    ('FAQs',          'faq/',            'is-mute'),
    ('Security',      'security/',       'is-mute'),
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
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{E(title)} · Kaizan</title>
        <meta name="description" content="{E(desc)}">
        <link rel="icon" type="image/png" sizes="32x32" href="{p}assets/img/favicon-32x32.png">
        <link rel="icon" type="image/webp" sizes="16x16" href="{p}assets/img/favicon-16x16.webp">
        <link rel="apple-touch-icon" sizes="180x180" href="{p}assets/img/apple-touch-icon.png">
        <link rel="mask-icon" href="{p}assets/img/safari-pinned-tab.svg" color="#FFB900">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&display=swap">
        <link rel="stylesheet" href="{p}assets/css/tokens.css{tokens_v}">
        <link rel="stylesheet" href="{p}assets/css/site.css{site_css_v}">
        <script defer src="{p}assets/js/site.js{site_js_v}"></script>
        <!-- Google Tag Manager -->
        <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
        new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        }})(window,document,'script','dataLayer','GTM-NCXT2FLQ');</script>
        <!-- End Google Tag Manager -->
        </head>
        <body>
        <div class="kz-page">
        <main class="kz-main">
        ''')


def page_foot() -> str:
    return ('</main>\n</div>\n'
            '<!-- Google Tag Manager (noscript) -->\n'
            '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NCXT2FLQ" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
            '<!-- End Google Tag Manager (noscript) -->\n'
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
      <a class="kz-nav-logo" href="{p}index.html">
        <img class="icon" src="{p}assets/img/kaizan-icon.png" alt="">
        <img class="word" src="{p}assets/img/kaizan-logo.png" alt="Kaizan">
      </a>
      <nav class="kz-nav-links" aria-label="Primary">
        {''.join(items_html)}
      </nav>
      <div class="kz-nav-cta">
        <a class="kz-btn kz-btn-ghost" href="https://app.kaizan.ai/">Client log in</a>
        <a class="kz-btn kz-btn-yellow" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
        ('Get in touch', [('Book a demo', 'https://calendar.app.google/Eae719Ejh3xxN3Lg8'), ('Contact', 'mailto:hello@kaizan.ai'),
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
    'Fiona Skilton':     'fiona-skilton.png',
    'Derek Grant':       'derek-grant.png',
    'Brandon Smith':     'brandon-smith.png',
    'Corin Ward':        'corin-ward.png',
    'Adam Hopkinson':    'adam-hopkinson.png',
    'Alex Beddoe':       'alex-beddoe.png',
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
          Client Service <span class="kz-mark">Intelligence</span><br>
          for the AI Era
        </h1>
        <p class="kz-lede" style="margin-top:24px;font-size:18px;max-width:520px;">
          Kaizan is the AI platform for client service professionals. Where AI Helpers work 24/7
          so your team increases the ROI and Revenue across all your clients.
        </p>
        <div class="kz-hero-cta-stack">
          <a class="kz-cta-card is-yellow" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">
            <div>
              <div class="kz-cta-eyebrow">30-min live demo</div>
              <div class="kz-cta-headline">See Kaizan in action</div>
            </div>
            <div class="kz-cta-pill"><span>Book a demo</span><span class="kz-cta-arrow">→</span></div>
          </a>
          <a class="kz-cta-card is-ghost" href="white-paper/">
            <div>
              <div class="kz-cta-eyebrow">CARE white paper · 18 min</div>
              <div class="kz-cta-headline">What the top 10% do differently?</div>
            </div>
            <div class="kz-cta-pill"><span>Whitepaper</span><span class="kz-cta-arrow">→</span></div>
          </a>
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

    <!-- PERSONAS -->
    <section class="kz-personas">
      <h2 class="kz-h2" style="margin-bottom:8px;">I am a…</h2>
      <p class="kz-lede" style="margin-bottom:28px;max-width:640px;font-size:16px;">
        Pick your role to see how Kaizan fits into your week - personalised guidance, real use cases and daily workflows.
      </p>
      <div class="kz-personas-grid">{persona_pills}</div>
    </section>

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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
      <div class="kz-product-hero-row">
        <p class="kz-lede" style="font-size:19px;max-width:640px;">
          The AI Assistant captures and unifies every meeting, chat and email.
          The CARE Client Health Model scores every relationship.
          AI Helpers act on every client for you.
          Client360 shares market intel that affects clients.
          Together they form a system of truth and action for your client teams.
        </p>
        <div class="cta">
          <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo →</a>
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
      <div class="kz-product-care-row">
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
        Answers ship with our security review pack. <a href="https://calendar.app.google/Eae719Ejh3xxN3Lg8" style="color:var(--kz-ink);font-weight:600;">Request the pack →</a>
      </p>
    </section>

    <!-- PRICING anchor (placeholder) -->
    <section class="kz-section-tight" id="pricing">
      <div class="kz-eyebrow">Pricing</div>
      <h2 class="kz-h3" style="margin-top:10px;font-size:24px;max-width:820px;">
        Tiered by seats and integration depth.
      </h2>
      <p class="kz-lede" style="margin-top:14px;max-width:720px;">
        Detailed pricing is shared in the demo. <a href="https://calendar.app.google/Eae719Ejh3xxN3Lg8" style="color:var(--kz-ink);font-weight:600;">Book a demo →</a>
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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
      </div>
    </section>

    {footer_html(1)}
    '''
    return page_head('Product', 1,
                     'AI Assistant, AI Helpers, the Client Health Model and Client 360 — '
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
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo →</a>
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
        <a class="kz-btn kz-btn-yellow" style="padding:14px 24px;font-size:15px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
        <a class="kz-btn kz-btn-black" style="padding:14px 24px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-NCXT2FLQ');</script>
<!-- End Google Tag Manager -->
</head>
<body>
<div class="kz-page">
<main class="kz-main">
'''
    return (head + body + '</main>\n</div>\n'
            '<!-- Google Tag Manager (noscript) -->\n'
            '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NCXT2FLQ" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
            '<!-- End Google Tag Manager (noscript) -->\n'
            '</body>\n</html>\n')


def render_blog_post(post: dict) -> str:
    """Render a single hidden-blog post page at /blog/<slug>/index.html."""
    head = '''<!doctype html>
<html lang="en">
<head>
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
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','GTM-NCXT2FLQ');</script>
<!-- End Google Tag Manager -->
</head>
<body>
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
    return (head + body + '</main>\n</div>\n'
            '<!-- Google Tag Manager (noscript) -->\n'
            '<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NCXT2FLQ" '
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
            '<!-- End Google Tag Manager (noscript) -->\n'
            '</body>\n</html>\n')


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
          <a class="btn" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book time with Glen →</a>
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
          <p class="lede">Leverage all your unified client intelligence — every meeting, every signal,
            every score — in your own systems and agents. SOC 2 logged, two-way sync, scoped per tenant.</p>
        </div>
        <div class="actions">
          <a class="kz-btn kz-btn-yellow" style="padding:12px 20px;font-size:14px;white-space:nowrap;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Talk to us</a>
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
            <a class="kz-btn kz-btn-yellow" style="padding:14px 22px;font-size:14px;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book demo →</a>
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
        <a class="kz-btn kz-btn-black" style="padding:16px 26px;font-size:15px;white-space:nowrap;" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">
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
        return ('<div class="kz-secvis kz-secvis-badges">'
                '<img src="../assets/img/security/Security.png" '
                'alt="SOC 2, ISO 27001, GDPR, CASA Verified, CCPA — security and compliance certifications" '
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
            <a class="kz-btn kz-btn-yellow" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
          "chat messages — all anonymised — comparing how client service professionals work on "
          "the relationships that grow versus the ones that slip away."),
    meta='Free · 15 pages · Instant download',
    inside=[
        'The 8 behaviours that consistently mark the top 10% of account teams',
        'The KPIs that actually lead to happier, higher-revenue clients',
        'The CARE framework — how the patterns cluster into four pillars',
    ],
    dataset=[
        ('1M+',  'Anonymised client conversations'),
        ('10M+', 'Emails analysed'),
        ('15',   'Pages of research'),
        ('8',    'Behaviours decoded'),
    ],
    numbers=[
        ('2.2', '×', 'More risks surfaced at top-performing accounts than at bottom-performing ones. '
                     'The accounts that look quiet and healthy usually are not — silence is absence, '
                     'not stability.', 'The Risk Paradox'),
        ('66', '%', 'Of all client-facing calls are handled by just 25% of account managers. Coverage '
                    'across the whole portfolio is the lever most teams leave unpulled.', 'The AM Power Law'),
        ('1.84', '×', 'More calls per account manager on top-performing clients — at the same portfolio '
                      'size, email-to-call ratio and talk-time share. Top accounts are more of the same '
                      'conversation, not a different one.', 'The Ideal AM Profile'),
    ],
    care=[
        ('C', 'Client satisfaction', 'How happy the client is with you and the work being delivered.',
         '4.2×', 'More proactive comms per account at the top decile'),
        ('A', 'Activity with stakeholders', 'Stakeholder coverage and account context — who matters, '
         'what changed this week, the shape of the next conversation.',
         '73%', 'Of top performers maintain a live stakeholder map'),
        ('R', 'Relationship strength', 'Strategic partner or just a vendor? Whether rapport, trust and '
         'sentiment are where they need to be.',
         '2.1h', 'Median first response time at the top 10%'),
        ('E', 'Expansion opportunities', 'Inbound-signal capture and conversion — the quiet ask in '
         'passing, or the proactive suggestion of how to grow their business.',
         '82%', 'Of expansion revenue comes from prioritising commercial conversations early'),
    ],
    audiences=[
        ('Heads of Client Services & CS', 'Set the bar for the team. Benchmark, retrain, repeat.'),
        ('Account Directors & Managers', 'See where your book sits — and what to change on Monday.'),
        ('Agency Leaders', 'An operating system for client-facing teams at scale.'),
        ('Founders & CEOs', 'Retention is the lever. Here is what moves it.'),
        ('C-level teams', '82% of expansion is inbound — the data on how to catch it.'),
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
          <a class="kz-btn kz-btn-ghost" href="https://calendar.app.google/Eae719Ejh3xxN3Lg8">Book a demo</a>
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
      <p class="kz-lede" style="margin-bottom:36px;">Eleven behaviours, four pillars — the structure behind every top-decile account team.</p>
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
                     'The 2026 Client Service Report from Kaizan — the data on what great client '
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
                     'Client success and account management FAQs — a resource hub covering client '
                     'intelligence, onboarding, retention, client health, reviews, reporting, '
                     'expansion, metrics and AI for account managers.') + body + page_foot()


# ─────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────

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
